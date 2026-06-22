# ADX Quant Pro / new7 — EURUSD H1 Causal End-to-End Upgrade

Date: 2026-06-18

## Result

The uploaded project was inspected, modified in place, tested, and repackaged as a complete Streamlit project. The protected **Full Metric Detail + History** calculation remains the directional source of truth. Its implementation file was not modified and its SHA-256 checksum remains:

`fe0797ab30f469f3ea748bc66a690b18a68aaf91306ac33c797bdcdcf6e60682`

No top-level route, top-level tab, inner tab, page, menu item, prediction model, trained model, or dataset was added.

## Implemented architecture

- Added one deterministic causal-support layer that consumes completed EURUSD H1 rows and protected Full Metric history only.
- Added past-only recurrent H1 pattern memory for 24, 120, and 600-row windows with 1H/2H/3H/6H settled outcomes and minimum-sample protection.
- Added structural-break/CUSUM-style strength, entropy increase, regime lifecycle risk, and the required 50/30/20 Transition Risk combination.
- Added causal triple-barrier settlement and meta-label actionability. Direction is inherited from Full Metric; the support layer can only confirm or force WAIT.
- Expanded settled evaluation to 1H, 2H, 3H, and 6H while keeping 2–3H as the primary practical actionability window.
- Added two canonical opportunity records with accepted/blocked reason, validity horizon, pattern state, transition risk, actionability, EV, and reliability. Unsafe entries are never forced.
- Added fractionally differentiated support validation. It remains weight zero unless stationarity, memory preservation, and out-of-sample stability checks pass.
- Added duplicate-evidence family diagnostics and a conservative duplicate-confirmation penalty applied only to uncertainty/confidence, never to protected Full Metric direction or scores.
- Added regime-conditioned empirical outcome distributions and deterministic small-sample shrinkage/fallback.
- Added MMSE/Wiener/lag-correlation reweighting of existing Power BI paths. Existing projections are preserved in the audit; no new projection model was added.
- Added genuine one-candle incremental updates for cached evidence rows, rolling moments, rolling correlations, pattern sequence counts, and newly settled barrier outcomes.
- Heavy incremental cache records stay in session state; canonical/UI payloads receive a compact view to lower browser and phone rendering load.
- Finder operational output now reads the canonical candidates and decision. Its old standalone calculation helper is no longer used for the operational decision.
- Lunch, Dinner, Research, Finder, and Dinner AI grounding consume the same canonical result and candidate records.
- Added Run ID/generation, completed-H1 timestamp, data signature, cache status, and creation-time diagnostics to existing displays.

## Modified files

### Added

- `core/causal_quant_support_20260618.py`
- `core/powerbi_mmse_weighting_20260618.py`
- `tests/test_causal_quant_end_to_end_20260618.py`
- `IMPLEMENTATION_REPORT_20260618_CAUSAL_END_TO_END.md`
- `TEST_RESULTS_20260618_CAUSAL_END_TO_END.txt`

### Updated

- `core/settings_run_orchestrator_20260617.py`
- `ui/decision_product_panel_20260617.py`
- `tabs/dinner_unified_center_20260617.py`
- `tabs/finder_alignment_upgrade_20260611.py`
- `tabs/research.py`

### Explicitly protected and unchanged

- `tabs/eurusd_h1_matrix.py`

## Test results

- Baseline before changes: **67 passed**
- Final full suite: **77 passed**
- Python compilation: **408 Python files compiled successfully**
- Main import test: **8 critical modules imported successfully**
- Streamlit AppTest: **0 exceptions**
- Streamlit server smoke test: health endpoint returned **ok**
- Requirements syntax: **33 requirement entries parsed successfully**
- Runtime target preserved: **python-3.12**

### Acceptance-test coverage

1. Python syntax compilation — PASS
2. Main Streamlit import — PASS
3. Streamlit startup/server health — PASS
4. Protected Full Metric checksum/regression — PASS
5. Canonical synchronization — PASS
6. Latest completed H1 protection — PASS
7. No future leakage — PASS
8. Candidate 1/2 consistency — PASS
9. BUY/SELL/WAIT one-way gate — PASS
10. Pattern-memory causality — PASS
11. Structural-break fallback — PASS
12. Probability small-sample fallback — PASS
13. Cache hit, append, and invalidation — PASS
14. Current-time-first tables — PASS
15. Mobile-safe compact canonical payload/AppTest — PASS
16. Existing tab and inner-tab preservation — PASS
17. Existing export and copy-function preservation — PASS
18. Python 3.12/Streamlit Cloud configuration checks — PASS

## Startup command

```bash
streamlit run app.py
```

## Remaining limitations

- Live market/API/MT5 behavior could not be exercised without the user's live credentials and network feeds. The project uses safe fallbacks and the server/application startup path was verified.
- MMSE specialization uses the existing settled residual records. When a narrow regime/session/volatility subgroup is unavailable, it deliberately falls back to broader valid samples instead of inventing a probability or weight.
- Fractionally differentiated features remain supporting-only and receive zero influence when validation fails. They never alter raw prices or protected Full Metric History.
- Optional NLP/model libraries remain defensively imported as in the uploaded project; absence of an optional package does not crash the app.
