# CLAUDE.md — Call Intent & Confusion Portal

## Overview

Read-only portal that displays Walker Brain's call analysis data. Answers two questions:
1. **"What are callers' intents?"** — primary_intent breakdown across all analyzed calls
2. **"Who do callers think they're calling?"** — category confusion detection with specific brands + channels

Single-component architecture: the portal reads `public.analysis_results` from the Analysis DB. No pipeline, no LLM calls, no data writes to Walker Brain tables.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  STREAMLIT PORTAL (Call Intent & Confusion Portal)           │
│  Card-based call list + expander details + 4 KPIs + 4 charts│
│  Auth: invoca.portal_users + portal_sessions (bcrypt+RPC)   │
│                                                              │
│  READS FROM: public.analysis_results (Walker Brain, 118 cols)│
│  WRITES TO:  invoca.portal_users/sessions (auth only)        │
└─────────────────────────────────────────────────────────────┘
          │
          v
┌─────────────────────────────────────────────────────────────┐
│              SUPABASE (beviondsojrrdvknpdbh)                │
│  public.analysis_results — 8,353+ rows, READ-ONLY           │
│  invoca.portal_users / invoca.portal_sessions — auth tables  │
└─────────────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `invoca_intent_portal/app.py` | Single-page portal: KPIs, charts, card list, detail expanders |
| `invoca_intent_portal/lib/db.py` | Read-only queries on `public.analysis_results` + auth RPCs |
| `invoca_intent_portal/lib/ui.py` | Dark theme, color maps, card/detail components, Plotly template |
| `invoca_intent_portal/lib/auth.py` | Supabase email/password auth + DB sessions |
| `invoca_intent_portal/lib/supabase_client.py` | Supabase client bootstrap |

## Infrastructure IDs

| Resource | ID | Notes |
|----------|-----|-------|
| Supabase (Analysis DB) | `beviondsojrrdvknpdbh` | Reads `public.analysis_results`, writes `invoca.*` auth tables |
| n8n WF-INV-01 (DEACTIVATED) | `iZLPEnrMWBgnzdfC` | Old pipeline — deactivated 2026-02-26 |

## Data Source: public.analysis_results

Walker Brain analyzes ~491 calls/day, producing 118 columns per call. The portal reads a subset:

**List view columns:** id, source_transcript_id, call_start_date, call_duration_seconds, primary_topic, primary_intent, outcome, emotional_tone, quality_score, case_type, summary, key_quote, category_confusion, process_confusion_points, brand_reference, other_brands_mentioned, channel_referenced, agent_empathy_score, agent_education_quality, agent_closing_effectiveness, confidence_score, needs_review, review_reason, original_language

**Detail view adds:** transcript_original (lazy-loaded)

**Key enums:**
- `primary_intent` (8 values): seeking_representation, information_only, calling_for_someone_else, follow_up, urgent_action, trust_verification, cost_inquiry, referral
- `outcome` (6 values): referral-made, callback-requested, consultation-scheduled, not-qualified, information-only, other
- `emotional_tone` (10 values): frustrated, neutral, confused, concerned, distressed, fearful, anxious, hopeful, angry, relieved
- `category_confusion` (bool): ~12.5% true (1,046/8,353)

## Auth Tables (invoca schema — portal's own)

**invoca.portal_users** — email/password (bcrypt via pgcrypto), @walkeradvertising.com domain restriction
**invoca.portal_sessions** — DB-backed session tokens (7-day TTL)

**Auth RPCs** (public schema, granted to anon):
- `authenticate_portal_user(email, password)` — bcrypt check + domain restriction
- `create_portal_session(user_id)` → token string
- `validate_portal_session(token)` → user info or empty
- `delete_portal_session(token)` → void

## Commands

```bash
# Run portal locally (bypasses auth)
cd invoca_intent_portal && LOCAL_DEV=1 streamlit run app.py
```

## What Was Removed (2026-02-26)

The entire Invoca pipeline was killed. The portal now reads Walker Brain data directly instead of running its own analysis.

**Deleted components:**
- `scripts/bridge.py` — Invoca API discovery + Whisper transcription ($1.80/day)
- `scripts/reanalyze.js` — Node.js bulk re-analysis via OpenRouter
- `modules/` — config.py, transcriber.py (pipeline support)
- `prompts/` — LLM analysis prompt
- `run_bridge.bat`, `package.json`, `node_modules/` — Node.js + Windows runner

**Deactivated:**
- WF-INV-01 (`iZLPEnrMWBgnzdfC`) — n8n workflow that analyzed calls via Grok ($5/day)
- Windows scheduler `InvocaBridgeQ6H` — user should delete: `schtasks /Delete /TN "InvocaBridgeQ6H" /F`

**Savings:** ~$7/day ($210/month) in Whisper + Grok costs eliminated.

## Status (2026-02-26)

- **Portal:** Rewritten for Walker Brain data — 4 KPIs, 4 charts (intent, outcome, confusion x intent, tone), card list with confusion detail
- **Data:** 8,353+ rows from Walker Brain, 12.5% confusion rate, ~491 new calls/day
- **Pipeline:** KILLED — no bridge.py, no n8n workflow, no LLM costs
- **Deploy:** GitHub (`alexbespwalker/invoca-intent-explorer`), Streamlit Cloud
- **TODO:** User should delete Windows scheduler: `schtasks /Delete /TN "InvocaBridgeQ6H" /F`
