# Known Limitations

1. BOCPD and adaptive-window evidence are lightweight approximations designed for bounded Streamlit execution. They are monitoring evidence, not a replacement regime model.
2. Historical transition statistics are descriptive. The UI warns when fewer than five same-transition samples are available.
3. ECE and Brier score require settled probabilistic outcomes. They show unavailable/limited evidence when the settled sample is insufficient.
4. Adaptive conformal coverage is only as representative as the available settled residual window; distribution shift can temporarily reduce coverage.
5. The DuckDB sidecar is local to the Streamlit filesystem. On hosting plans with ephemeral storage, durable cross-redeploy history requires an external persistent volume or a controlled export/restore process. The application still preserves the current canonical in-session result.
6. MT5 is Windows-only and intentionally absent from Streamlit Cloud requirements. Existing cloud-safe market connectors remain available.
7. Streamlit reruns the script for UI interaction by design. The upgrade prevents those reruns from invoking the heavy calculator, but lightweight rendering and bounded search/query work still occur when their controls are used.
8. The automated startup health check confirms server boot and health endpoint response; it does not simulate every authenticated browser gesture or third-party provider response.
9. Validation was executed with the available local Python 3.13.5 interpreter. The package is pinned to Python 3.12, uses Python-3.12-compatible syntax/dependencies, and includes static/runtime contract tests, but this environment did not provide a separate Python 3.12 executable.
10. The research features improve monitoring, calibration, and auditability; they do not guarantee profitable trades or eliminate market risk.
