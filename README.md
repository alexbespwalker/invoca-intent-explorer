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

## Streamlit Cloud deploy

Use Streamlit Cloud UI:

1. Open https://share.streamlit.io
2. Click `Create app`
3. Set repository to `alexbespwalker/invoca-intent-explorer`
4. Set branch to `main`
5. Set main file path to `invoca_intent_portal/app.py`
6. Add secrets from `.streamlit/secrets.toml.example`
7. Deploy

App URL is assigned after deploy (typically `https://<app-name>.streamlit.app`).

## Main filters in dashboard

- `Brand`
- `Media Source`

These are the primary controls for stakeholder exploration of BC and non-BC call cohorts.

## Pages

- Home KPI + distribution
- Call Detail drill-down
- Trends
- Review Queue
