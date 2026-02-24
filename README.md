# Invoca Intent Explorer (Streamlit)

Stakeholder-facing Streamlit dashboard for Invoca call analytics stored in Supabase.

## App entrypoint

- `invoca_intent_portal/app.py`

## Local run

```bash
pip install -r requirements.txt
streamlit run invoca_intent_portal/app.py
```

## Required secrets (Streamlit Cloud)

In Streamlit Cloud app settings, add:

```toml
SUPABASE_URL = "https://<project>.supabase.co"
SUPABASE_SERVICE_KEY = "<service_role_key>"
# or SUPABASE_KEY
```

## Main filters in dashboard

- `Brand`
- `Media Source`

These are the primary controls for stakeholder exploration of BC and non-BC call cohorts.

## Pages

- Home KPI + distribution
- Call Detail drill-down
- Trends
- Review Queue
