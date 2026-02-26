"""
Bridge script: Invoca API discovery + Auth0/Playwright acquisition + Whisper transcription.

This is the Python half of the pipeline. It handles everything up to transcription,
then writes status='transcribed' to the DB. The n8n workflow (WF-INV-01) picks up
from there for LLM analysis.

Usage:
    python scripts/bridge.py                   # default: last 24h, limit 150
    python scripts/bridge.py --limit 5         # test with 5 calls
    python scripts/bridge.py --days 3          # look back 3 days
    python scripts/bridge.py --dry-run         # preview only, no processing
    python scripts/bridge.py --skip-discovery  # skip API discovery, process existing discovered calls
"""

import argparse
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests as http_requests
from playwright.sync_api import sync_playwright
from supabase import create_client, Client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.config import load_config, Config
from modules.transcriber import Transcriber

# ---------------------------------------------------------------------------
# Supabase setup (Analysis DB — read/write)
# ---------------------------------------------------------------------------
SUPABASE_URL = "https://beviondsojrrdvknpdbh.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJldmlvbmRzb2pycmR2a25wZGJoIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NjM3NTExNjUsImV4cCI6MjA3OTMyNzE2NX0."
    "1MNK7A85C81VhzCJB5i_o5f9RS1pw1GL6wXWhxzMAqE"
)


def get_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _table(db: Client, name: str):
    return db.schema("invoca").table(name)


def log_event(db: Client, event: str, details: dict | None = None):
    """Write to invoca.workflow_events for observability."""
    try:
        _table(db, "workflow_events").insert({
            "workflow_name": "bridge.py",
            "stage": event,
            "level": "info",
            "event_payload": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass  # non-critical


# ---------------------------------------------------------------------------
# Step 1: Invoca API discovery
# ---------------------------------------------------------------------------
INVOCA_API_URL = "https://walkeradvertising.invoca.net/api/2020-10-01"


def discover_new_calls(
    config: Config, db: Client, days: int = 1, min_duration: int = 30,
) -> list[dict]:
    """Fetch new BC calls from Invoca API, dedup against DB, insert as discovered."""
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    url = f"{INVOCA_API_URL}/networks/transactions/{config.invoca_network_id}.json"
    params = {
        "oauth_token": config.invoca_oauth_token,
        "from": date_from,
        "to": date_to,
        "limit": 10000,
        "include_columns": (
            "call_record_id,complete_call_id,start_time_local,"
            "calling_phone_number,duration,recording,"
            "advertiser_campaign_name,advertiser_name,"
            "destination_phone_number,media_source,"
            "utm_source,utm_medium,utm_campaign,utm_term,utm_content,"
            "gclid"
        ),
    }

    print(f"[DISCOVER] Fetching calls {date_from} to {date_to}...")
    resp = http_requests.get(url, params=params)
    resp.raise_for_status()
    raw_calls = resp.json()
    print(f"  Total from API: {len(raw_calls)}")

    # Filter: BC brand, minimum duration, has recording
    bc_calls = []
    for c in raw_calls:
        adv = (c.get("advertiser_name") or "").lower()
        camp = (c.get("advertiser_campaign_name") or "").lower()
        is_bc = "betterclaims" in adv or "5bc" in camp or camp.startswith("bc")
        dur = c.get("duration") or 0
        has_rec = bool(c.get("recording"))
        if is_bc and dur >= min_duration and has_rec:
            bc_calls.append(c)

    print(f"  BC calls (dur>={min_duration}s, has recording): {len(bc_calls)}")

    if not bc_calls:
        return []

    # Dedup: get existing invoca_call_ids from DB
    existing_ids_rows = (
        _table(db, "calls")
        .select("invoca_call_id")
        .eq("brand_code", "BC")
        .execute()
        .data or []
    )
    existing_ids = {r["invoca_call_id"] for r in existing_ids_rows}

    new_calls = [c for c in bc_calls if c.get("complete_call_id") not in existing_ids]
    print(f"  New (not in DB): {len(new_calls)}")

    if not new_calls:
        return []

    # Insert new calls as 'discovered'
    inserted = []
    for c in new_calls:
        row = {
            "invoca_call_id": c.get("complete_call_id"),
            "call_record_id": c.get("call_record_id"),
            "brand_code": "BC",
            "advertiser_name": c.get("advertiser_name"),
            "campaign_name": c.get("advertiser_campaign_name"),
            "call_date_pt": c.get("start_time_local", "")[:10] or None,
            "call_start_time": c.get("start_time_local"),
            "duration_seconds": c.get("duration"),
            "caller_phone": c.get("calling_phone_number"),
            "destination_number": c.get("destination_phone_number"),
            "recording_url_signed": c.get("recording"),
            "media_source": c.get("media_source"),
            "utm_source": c.get("utm_source"),
            "utm_medium": c.get("utm_medium"),
            "utm_campaign": c.get("utm_campaign"),
            "utm_term": c.get("utm_term"),
            "utm_content": c.get("utm_content"),
            "gclid": c.get("gclid"),
            "status": "discovered",
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            result = _table(db, "calls").insert(row).execute()
            if result.data:
                inserted_row = result.data[0]
                inserted_row["recording_url_signed"] = c.get("recording")
                inserted.append(inserted_row)
        except Exception as e:
            print(f"  WARN: Failed to insert {c.get('complete_call_id')}: {e}")

    print(f"  Inserted: {len(inserted)} new calls")
    return inserted


# ---------------------------------------------------------------------------
# Step 2: Fetch discovered calls from DB (for processing)
# ---------------------------------------------------------------------------
def fetch_discovered_calls(db: Client, limit: int) -> list[dict]:
    rows = (
        _table(db, "calls")
        .select(
            "id,invoca_call_id,call_record_id,recording_url_signed,"
            "duration_seconds,brand_code,advertiser_name,campaign_name,call_date_pt"
        )
        .eq("brand_code", "BC")
        .eq("status", "discovered")
        .not_.is_("recording_url_signed", "null")
        .order("call_date_pt", desc=False)
        .limit(limit)
        .execute()
        .data or []
    )
    return rows


# ---------------------------------------------------------------------------
# Step 3: Auth0 login + Playwright S3 URL extraction
# ---------------------------------------------------------------------------
def extract_recording_id(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def invoca_auth0_login(email: str, password: str) -> http_requests.Session:
    """Authenticate via Invoca's Auth0 SSO flow."""
    session = http_requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    resp = session.get("https://walkeradvertising.invoca.net/login")
    csrf_match = re.search(r'authenticity_token" value="([^"]+)"', resp.text)
    if not csrf_match:
        raise RuntimeError("Could not find CSRF token on Invoca login page")
    csrf = csrf_match.group(1)

    resp = session.post(
        "https://walkeradvertising.invoca.net/auth/auth0",
        data={"utf8": "\u2713", "authenticity_token": csrf, "commit": "Log in"},
        allow_redirects=True,
    )

    state = parse_qs(urlparse(resp.url).query).get("state", [""])[0]
    if not state:
        raise RuntimeError("Could not extract Auth0 state parameter")

    resp = session.post(
        f"https://auth.us.invoca.net/u/login?state={state}",
        data={
            "state": state,
            "username": email,
            "password": password,
            "action": "default",
        },
        allow_redirects=True,
    )

    if "invoca.net" not in resp.url:
        raise RuntimeError(f"Auth0 login failed — landed at {resp.url}")

    return session


def get_s3_urls_batch(config: Config, calls: list[dict]) -> dict[int, str | None]:
    """Extract S3 signed URLs via Auth0 + Playwright browser automation."""
    print("  Authenticating via Auth0...", flush=True)
    session = invoca_auth0_login(config.invoca_email, config.invoca_password)
    print("  Auth OK", flush=True)

    pw_cookies = []
    for cookie in session.cookies:
        pw_cookie = {
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain or ".invoca.net",
            "path": cookie.path or "/",
        }
        if cookie.secure:
            pw_cookie["secure"] = True
        pw_cookies.append(pw_cookie)

    s3_urls: dict[int, str | None] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(pw_cookies)
        page = context.new_page()

        for i, c in enumerate(calls):
            call_id = c["id"]
            rec_id = extract_recording_id(c["recording_url_signed"])
            print(f"  [{i+1}/{len(calls)}] call_id={call_id} rec={rec_id}...",
                  end=" ", flush=True)

            try:
                rec_url = f"https://walkeradvertising.invoca.net/call/recording/{rec_id}"
                page.goto(rec_url)
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)

                signed_url = None

                if "s3" in page.url.lower() or "amazonaws" in page.url.lower():
                    signed_url = page.url
                else:
                    audio_elements = page.locator("audio").all()
                    for audio in audio_elements:
                        src = audio.get_attribute("src")
                        if src and ("s3" in src.lower() or "amazonaws" in src.lower()):
                            signed_url = src
                            break

                    if not signed_url:
                        links = page.locator(
                            "a[href*='s3'], a[href*='amazonaws']"
                        ).all()
                        for link in links:
                            href = link.get_attribute("href")
                            if href and ".mp3" in href.lower():
                                signed_url = href
                                break

                if signed_url:
                    print("OK", flush=True)
                else:
                    print("NO_URL", flush=True)

                s3_urls[call_id] = signed_url

            except Exception as e:
                print(f"FAIL: {e}", flush=True)
                s3_urls[call_id] = None

        browser.close()

    return s3_urls


# ---------------------------------------------------------------------------
# Step 4: Download + Transcribe
# ---------------------------------------------------------------------------
def download_from_s3(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resp = http_requests.get(url, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path


def update_call_transcribed(db: Client, call_id: int, transcript: str):
    word_count = len(transcript.split())
    _table(db, "calls").update({
        "transcript_text": transcript,
        "transcript_word_count": word_count,
        "status": "transcribed",
        "transcribed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", call_id).execute()


def update_call_failed(db: Client, call_id: int):
    _table(db, "calls").update({"status": "failed"}).eq("id", call_id).execute()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_bridge(
    limit: int = 150,
    days: int = 1,
    dry_run: bool = False,
    skip_discovery: bool = False,
):
    config = load_config()
    db = get_db()

    print("=" * 60)
    print(f"  Invoca Bridge — limit={limit}, days={days}, dry_run={dry_run}")
    print("=" * 60)

    # Step 1: Discover new calls from Invoca API
    if not skip_discovery:
        print("\n[1/4] Discovering new BC calls from Invoca API...")
        newly_discovered = discover_new_calls(config, db, days=days)
        log_event(db, "discovery_complete", {
            "new_calls": len(newly_discovered),
            "days_lookback": days,
        })
    else:
        print("\n[1/4] Skipping discovery (--skip-discovery)")

    # Step 2: Fetch all discovered calls ready for processing
    print("\n[2/4] Fetching discovered calls from DB...")
    calls = fetch_discovered_calls(db, limit)
    print(f"  Found {len(calls)} calls to process")

    if not calls:
        print("  Nothing to process.")
        log_event(db, "bridge_complete", {"processed": 0, "reason": "no_calls"})
        return

    if dry_run:
        print("\n[DRY RUN] Would process:")
        for c in calls:
            print(f"  id={c['id']}  invoca={c['invoca_call_id']}  "
                  f"dur={c['duration_seconds']}s  date={c['call_date_pt']}")
        return

    # Step 3: Get S3 signed URLs
    print(f"\n[3/4] Getting S3 URLs ({len(calls)} calls)...")
    s3_urls = get_s3_urls_batch(config, calls)
    valid_urls = sum(1 for u in s3_urls.values() if u)
    print(f"  Got {valid_urls}/{len(calls)} S3 URLs")

    # Step 4: Download + Transcribe each call
    print(f"\n[4/4] Downloading and transcribing...")
    transcriber = Transcriber(config)
    pipeline_start = time.time()
    stats = {"transcribed": 0, "failed": 0, "skipped": 0}

    for i, c in enumerate(calls):
        call_id = c["id"]
        invoca_id = c["invoca_call_id"]
        s3_url = s3_urls.get(call_id)

        print(f"\n  [{i+1}/{len(calls)}] call_id={call_id} ({invoca_id})")

        if not s3_url:
            print("    SKIP — no S3 URL")
            stats["skipped"] += 1
            continue

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            print("    Downloading...", end=" ", flush=True)
            dl_start = time.time()
            download_from_s3(s3_url, tmp_path)
            size_kb = tmp_path.stat().st_size / 1024
            print(f"{size_kb:.0f} KB ({time.time()-dl_start:.1f}s)", flush=True)

            if size_kb < 1:
                raise ValueError("Downloaded file too small (<1 KB)")

            print("    Transcribing...", end=" ", flush=True)
            tx_start = time.time()
            transcript = transcriber.transcribe(tmp_path)
            word_count = len(transcript.split())
            print(f"{word_count} words ({time.time()-tx_start:.1f}s)", flush=True)

            update_call_transcribed(db, call_id, transcript)
            stats["transcribed"] += 1

        except Exception as e:
            print(f"    FAIL: {e}", flush=True)
            stats["failed"] += 1
            try:
                update_call_failed(db, call_id)
            except Exception:
                pass

        finally:
            if tmp_path:
                try:
                    tmp_path.unlink(missing_ok=True)
                except Exception:
                    pass

        if (i + 1) % 5 == 0 and i + 1 < len(calls):
            elapsed = time.time() - pipeline_start
            avg = elapsed / (i + 1)
            remaining = (len(calls) - i - 1) * avg
            print(f"\n  [TIME] {i+1}/{len(calls)} done | "
                  f"ETA: {remaining/60:.1f} min")

    total_time = time.time() - pipeline_start
    print("\n" + "=" * 60)
    print("  BRIDGE COMPLETE")
    print(f"  Transcribed: {stats['transcribed']}")
    print(f"  Failed:      {stats['failed']}")
    print(f"  Skipped:     {stats['skipped']}")
    print(f"  Total time:  {total_time/60:.1f} min")
    print("=" * 60)

    log_event(db, "bridge_complete", {
        "transcribed": stats["transcribed"],
        "failed": stats["failed"],
        "skipped": stats["skipped"],
        "total_time_sec": round(total_time, 1),
    })


def main():
    parser = argparse.ArgumentParser(
        description="Bridge: Invoca discovery + transcription (no analysis)"
    )
    parser.add_argument(
        "--limit", type=int, default=150,
        help="Max calls to process (default: 150)",
    )
    parser.add_argument(
        "--days", type=int, default=1,
        help="Days to look back for Invoca API discovery (default: 1)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview calls without processing",
    )
    parser.add_argument(
        "--skip-discovery", action="store_true",
        help="Skip Invoca API discovery, only process existing discovered calls",
    )
    args = parser.parse_args()

    try:
        run_bridge(
            limit=args.limit,
            days=args.days,
            dry_run=args.dry_run,
            skip_discovery=args.skip_discovery,
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
