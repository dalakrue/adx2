# Streamlit Cloud Deployment

## Repository files

Keep these at the repository root:

- `app.py`
- `requirements.txt`
- `runtime.txt`
- `.streamlit/config.toml`
- all `core/`, `ui/`, `tabs/`, `data/`, and supporting application folders

`runtime.txt` is pinned to:

```text
python-3.12
```

## Deploy

1. Push the complete extracted package to a private Git repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `app.py`.
4. Add provider credentials through Streamlit Secrets or the application's existing secure key-storage workflow. Do not commit keys.
5. Deploy and inspect the Cloud logs until the health/startup message appears.
6. Open Settings, enter each provider key, and use the one-click **Save & Connect** action.
7. Press **Run Calculation** once. A successful run publishes one canonical generation and navigates to Lunch Field 1.

## Optional database initialization

The app creates the DuckDB sidecar automatically. To initialize or migrate it explicitly before deployment:

```bash
python scripts/migrate_regime_trust_20260621.py
```

## Cloud storage note

Community Cloud storage may be ephemeral across restarts/redeploys. Export important history or mount/use a persistent approved storage mechanism when long-term history retention is required. No API key is written to the trust-history tables.

## Health validation

Run locally or in CI:

```bash
streamlit run app.py --server.headless true --server.port 8765
```

Then check the Streamlit health endpoint at `/_stcore/health`.
