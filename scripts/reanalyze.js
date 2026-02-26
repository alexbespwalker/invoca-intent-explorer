#!/usr/bin/env node
/**
 * Re-analyze all transcribed calls with the new taxonomy prompt (v2).
 *
 * Reads transcripts from Supabase PostgREST, sends to OpenRouter (Grok),
 * writes analysis results back, and updates call status to 'analyzed'.
 *
 * Usage:
 *   node scripts/reanalyze.js              # process all transcribed calls
 *   node scripts/reanalyze.js --limit 5    # test with 5 calls
 *   node scripts/reanalyze.js --dry-run    # preview only
 */

const fs = require("fs");
const path = require("path");
const ini = require("ini");

// ── Config ──────────────────────────────────────────────────────────────
const CONFIG_PATH = path.join(__dirname, "..", "config.ini");
const PROMPT_PATH = path.join(__dirname, "..", "prompts", "transcript_analysis.txt");

const SUPABASE_URL = "https://beviondsojrrdvknpdbh.supabase.co";
const SUPABASE_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJldmlvbmRzb2pycmR2a25wZGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3NTExNjUsImV4cCI6MjA3OTMyNzE2NX0.1MNK7A85C81VhzCJB5i_o5f9RS1pw1GL6wXWhxzMAqE";
const MODEL = "x-ai/grok-4.1-fast";
const PROMPT_VERSION = "invoca_intent_v2";

// Read OpenRouter key from config.ini
function getOpenRouterKey() {
  const raw = fs.readFileSync(CONFIG_PATH, "utf8");
  const cfg = ini.parse(raw);
  const key = cfg.openrouter?.api_key;
  if (!key) throw new Error("Missing [openrouter] api_key in config.ini");
  return key;
}

// Read system prompt
function getSystemPrompt() {
  return fs.readFileSync(PROMPT_PATH, "utf8").trim();
}

// ── Supabase PostgREST helpers ──────────────────────────────────────────
const HEADERS = {
  apikey: SUPABASE_KEY,
  Authorization: `Bearer ${SUPABASE_KEY}`,
  "Content-Type": "application/json",
};

async function supaFetch(endpoint, opts = {}) {
  const url = `${SUPABASE_URL}/rest/v1/${endpoint}`;
  const { headers: extraHeaders, skipJson, ...restOpts } = opts;
  const res = await fetch(url, {
    ...restOpts,
    headers: { ...HEADERS, ...(extraHeaders || {}) },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Supabase ${res.status}: ${body}`);
  }
  if (skipJson) return null;
  return res.json();
}

async function getTranscribedCalls(limit) {
  let endpoint =
    "calls?status=eq.transcribed&transcript_text=not.is.null&brand_code=eq.BC&select=id,invoca_call_id,brand_code,advertiser_name,duration_seconds,call_date_pt,transcript_text&order=call_date_pt.asc";
  if (limit) endpoint += `&limit=${limit}`;
  // Need schema header for invoca schema
  return supaFetch(endpoint, {
    headers: { "Accept-Profile": "invoca" },
  });
}

async function checkExistingAnalysis(callId) {
  const rows = await supaFetch(
    `analysis?call_id=eq.${callId}&prompt_version=eq.${PROMPT_VERSION}&select=id`,
    { headers: { "Accept-Profile": "invoca" } }
  );
  return rows.length > 0;
}

async function insertAnalysis(row) {
  return supaFetch("analysis", {
    method: "POST",
    headers: { "Content-Profile": "invoca", Prefer: "return=minimal" },
    body: JSON.stringify(row),
    skipJson: true,
  });
}

async function updateCallStatus(callId) {
  return supaFetch(`calls?id=eq.${callId}`, {
    method: "PATCH",
    headers: { "Content-Profile": "invoca", Prefer: "return=minimal" },
    body: JSON.stringify({
      status: "analyzed",
      analyzed_at: new Date().toISOString(),
    }),
    skipJson: true,
  });
}

// ── OpenRouter ──────────────────────────────────────────────────────────
async function callLLM(apiKey, systemPrompt, userPrompt) {
  const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.2,
      max_tokens: 4096,
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`OpenRouter ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Parse + Validate ────────────────────────────────────────────────────
const VALID_INTENTS = new Set([
  "injury_new_case", "property_only", "already_represented",
  "insurance_inquiry", "existing_case", "wrong_number",
  "general_question", "spam", "other",
]);
const VALID_OUTCOMES = new Set([
  "connected", "callback_set", "caller_declined",
  "not_applicable", "caller_dropped", "wrong_number", "other",
]);
const VALID_SENTIMENTS = new Set([
  "positive", "neutral", "confused", "frustrated", "angry",
]);

function mapEnum(raw, validSet, fallback) {
  if (!raw) return fallback;
  const lower = String(raw).trim().toLowerCase();
  return validSet.has(lower) ? lower : fallback;
}

function parseAnalysis(responseText, call) {
  let cleaned = responseText.trim();
  if (cleaned.startsWith("```json")) cleaned = cleaned.slice(7);
  else if (cleaned.startsWith("```")) cleaned = cleaned.slice(3);
  if (cleaned.endsWith("```")) cleaned = cleaned.slice(0, -3);
  cleaned = cleaned.trim();

  const analysis = JSON.parse(cleaned);

  const callerIntent = mapEnum(analysis.caller_intent, VALID_INTENTS, "other");
  const callOutcome = mapEnum(analysis.call_outcome, VALID_OUTCOMES, "other");
  const callerSentiment = mapEnum(
    analysis.caller_sentiment, VALID_SENTIMENTS, "neutral"
  );

  let qualityScore = analysis.agent_quality_score;
  if (qualityScore != null) {
    qualityScore = Math.max(1, Math.min(10, parseInt(qualityScore) || 5));
  } else {
    qualityScore = null;
  }

  const confusionSignals = Array.isArray(analysis.confusion_signals)
    ? analysis.confusion_signals
    : [];
  const keyQuotes = Array.isArray(analysis.key_quotes)
    ? analysis.key_quotes
    : [];
  const flags = [];
  if (analysis.brand_confusion) flags.push("brand_confusion");
  if (analysis.flags && Array.isArray(analysis.flags)) {
    for (const f of analysis.flags) {
      if (!flags.includes(f)) flags.push(f);
    }
  }

  return {
    call_id: call.id,
    analysis_version: 1,
    model_used: MODEL,
    prompt_version: PROMPT_VERSION,
    caller_intent: callerIntent,
    intent_confidence: Math.max(0, Math.min(100, analysis.intent_confidence || 75)),
    brand_confusion: !!analysis.brand_confusion,
    confusion_signals: confusionSignals,
    call_outcome: callOutcome,
    case_type: analysis.case_type || null,
    caller_situation: analysis.caller_situation || null,
    agent_quality_score: qualityScore,
    caller_sentiment: callerSentiment,
    key_quotes: keyQuotes,
    flags: flags,
    raw_analysis: analysis,
    validation_passed: true,
    validation_warnings: [],
  };
}

// ── Main ────────────────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const limitIdx = args.indexOf("--limit");
  const limit = limitIdx >= 0 ? parseInt(args[limitIdx + 1]) : null;

  console.log(`=== Invoca Re-Analysis (v2 taxonomy) ===`);
  console.log(`Model: ${MODEL}`);
  console.log(`Prompt version: ${PROMPT_VERSION}`);
  if (dryRun) console.log("DRY RUN — no writes");
  if (limit) console.log(`Limit: ${limit}`);
  console.log();

  const apiKey = getOpenRouterKey();
  const systemPrompt = getSystemPrompt();
  const calls = await getTranscribedCalls(limit);

  console.log(`Found ${calls.length} transcribed calls to process.\n`);
  if (calls.length === 0) return;

  let processed = 0;
  let skipped = 0;
  let errors = 0;

  for (const call of calls) {
    const label = `[${processed + skipped + errors + 1}/${calls.length}] Call ${call.id} (${call.invoca_call_id})`;

    // Check if already processed (resumable)
    try {
      const exists = await checkExistingAnalysis(call.id);
      if (exists) {
        console.log(`${label} — SKIP (already has v2 analysis)`);
        skipped++;
        continue;
      }
    } catch (e) {
      // If check fails, proceed anyway
    }

    // Build user prompt
    let userPrompt = `Call ID: ${call.id}\n`;
    if (call.duration_seconds) userPrompt += `Duration: ${call.duration_seconds} seconds\n`;
    if (call.advertiser_name) userPrompt += `Brand: ${call.advertiser_name}\n`;
    userPrompt += `\n--- TRANSCRIPT ---\n${call.transcript_text}\n--- END TRANSCRIPT ---\n`;
    userPrompt += `\nAnalyze this call and provide your assessment in JSON format.`;

    if (dryRun) {
      console.log(`${label} — would send ${call.transcript_text.length} chars to LLM`);
      processed++;
      continue;
    }

    try {
      const response = await callLLM(apiKey, systemPrompt, userPrompt);
      const responseText = response.choices[0].message.content;
      const row = parseAnalysis(responseText, call);

      await insertAnalysis(row);
      await updateCallStatus(call.id);

      const intent = row.caller_intent;
      const situation = (row.caller_situation || "").substring(0, 80);
      console.log(`${label} — OK  intent=${intent}  "${situation}"`);
      processed++;

      // Rate limiting: 200ms between calls
      await new Promise((r) => setTimeout(r, 200));
    } catch (e) {
      console.error(`${label} — ERROR: ${e.message}`);
      errors++;
    }
  }

  console.log(`\n=== Done ===`);
  console.log(`Processed: ${processed}  Skipped: ${skipped}  Errors: ${errors}`);
}

main().catch((e) => {
  console.error("Fatal error:", e);
  process.exit(1);
});
