# Protected Logic Confirmation

The uploaded package was used as the hash authority.

| Protected file | Uploaded SHA-256 | Delivered SHA-256 | Status |
|---|---|---|---|
| `core/settings_run_orchestrator_20260617.py` | `bdedf3fd39ec5f36f07187ae0efdcd957d21b9a68898178eb2958781fae19745` | same | UNCHANGED |
| `core/decision_product_engine_20260617.py` | `e26c948f88a96f3af4881a2d0e1b06738b4f5b9e2a872b002d8d0aa8aabdfe76` | same | UNCHANGED |
| `core/canonical_runtime_20260617.py` | `2d5b1007290b5cf92a493fcebb92353b24cf4af9a1025036cf88b1e869c0bf89` | same | UNCHANGED |
| `tabs/home_parts/part_005.py` | `8e99f9a998f1258ff0fef51faf369efa49bebc5e9932094e856fa644e3583e92` | same | UNCHANGED |

The new `tabs/powerbi_direction_accuracy_patch_20260621.py` wraps only the historical validation result. It does not replace `_dv_predict_future_candles_v20260609`, point paths, interval paths, protected scores, priority logic or canonical decision publication.

Allowed new effect: validation evidence may show insufficient support or treat a tiny forecast as non-actionable.  
Forbidden and tested: WAIT promotion, BUY↔SELL reversal, model training on tab opening, or Settings calculation triggered from a Lunch field.
