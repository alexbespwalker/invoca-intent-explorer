# Invoca Intent Explorer Portal

Streamlit portal for browsing Invoca call intent analysis data stored in Supabase (`invoca` schema).

## Run

```bash
pip install -r requirements.txt
streamlit run invoca_intent_portal/app.py
```

Optional local setup:

```bash
cp invoca_intent_portal/.env.example .env
```

## Required environment variables

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY` (or `SUPABASE_KEY`)

Optional Invoca discovery workflow env vars for n8n runtime:

- `INVOCA_SUBDOMAIN`
- `INVOCA_NETWORK_ID`
- `INVOCA_OAUTH_TOKEN`
- `INVOCA_DAYS_BACK`
- `INVOCA_MIN_DURATION`

## Pages

- `app.py`: Intent Explorer KPI + distribution + filtered call table.
- `pages/2_Call_Detail.py`: Transcript and per-call analysis drill-down.
- `pages/3_Trends.py`: Weekly trends for quality/confusion/repositioning.
- `pages/4_Review_Queue.py`: Manual QA adjudication queue.

## Internal module map

- `lib/sidebar_filters.py`: Shared sidebar/date/filter rendering for Home + Trends.
- `lib/filter_state.py`: Typed `CallFilters` model.
- `lib/data_access.py`: Backward-compatible facade to repository modules.
- `lib/calls_repo.py`: Calls + dimension option queries.
- `lib/analysis_repo.py`: Summary/trend/confusion/repositioning aggregations.
- `lib/review_repo.py`: Review queue reads/writes.
- `lib/ops_repo.py`: Pipeline health/freshness snapshots.
