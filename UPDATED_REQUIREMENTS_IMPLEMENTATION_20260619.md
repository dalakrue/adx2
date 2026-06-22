# Updated Requirements Implementation — 2026-06-19

## Implemented

- Server-side Streamlit Secrets resolution for Finnhub and the second/Twelve Data market key.
- Stored keys are never autofilled into browser widgets. Settings shows configuration status and blank temporary replacement fields only.
- Authenticated, non-guest automatic startup with API validation TTL, latest-completed-H1 guard, generation lock, cooldown, stale-generation check, and optional automatic navigation to Lunch.
- Manual **Run Calculation + Open Lunch** remains available.
- Lunch upgraded from four to six closed-first fields.
- Existing ten Full Metric decision histories preserved; Decision 11, **Medium-Standard Regime Bias**, appended as read-only support using the requested 30/20/15/10/10/10/5 weighting.
- Five requested 25-day Field-4 tables are atomically published with the canonical generation.
- Similar-Day matching retains no-look-ahead ranking, z-normalized shape comparison, matrix-profile style distance, MPdist-inspired distance, constrained DTW, pattern families, anomaly flags, and baseline validation.
- Power BI adds explicit 50%, 80%, and 95% empirical intervals, base/bull/bear/historical-similar-day scenarios, generation reconciliation text, and a validation panel.
- Dinner removed from visible top-level navigation. Legacy Dinner/Regime routes redirect to Lunch Field 5 or Field 6 compatibility targets.
- Field 5 loads only the selected inner view. Field 6 does not import the AI workspace until enabled.
- Real secrets are excluded by `.gitignore`; a safe `.streamlit/secrets.example.toml` is included.

## Safety invariants

- No protected existing ten-decision formula is modified by Decision 11.
- Similar-Day future outcomes are attached only after ranking and are never matching features.
- Opening Lunch fields does not start a new market calculation.
- Automatic calculation is disabled for guest sessions and runs only for a newer completed H1 candle.
- Local SQLite is not used as permanent API-key storage.

## Verification

- Python compile check: PASS.
- Final focused regression run: 48 tests passed.
- All test modules were also covered in focused regression batches during implementation.
- Clean SQLite migration smoke test: PASS.
- Main-module import smoke test: PASS.
- Live Streamlit health endpoint boot test: PASS.
- Runtime databases were restored to their original uploaded state after testing.
- No real API keys are included in the ZIP.
