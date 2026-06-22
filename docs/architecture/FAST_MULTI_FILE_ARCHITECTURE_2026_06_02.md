# Fast Multi-File Architecture Upgrade — 2026-06-02

This project keeps the original Streamlit behavior while making future upgrades safer and faster.

## Main run path

```text
main.py
└── adx_dashpoard.py
    └── core.app_shell.run_app()
        └── core/app/runner.py
            ├── init shared state
            ├── apply UI/CSS
            ├── refresh shared connector data
            ├── render sidebar navigation
            └── lazy-load selected tab from core/app/registry.py
```

## New divided architecture

| Layer | Folder / file | Why it exists |
|---|---|---|
| App shell | `core/app/` | Keeps Streamlit startup, tab routing, lazy imports, refresh, and lifecycle handling separate. |
| Defaults | `core/config/defaults.py` | One place for tab names and session defaults. |
| State | `core/state/session_state.py` | One place for session initialization and repair. |
| Utils | `core/utils/` | Numeric, timer, and symbol helpers separated from app state. |
| Demo data | `core/data/synthetic.py` | Safe demo OHLC moved away from shared app logic. |
| Connectors | `core/connectors/` | MT5, TwelveData, Doo Bridge, websocket. A short hot cache avoids duplicate calls during Streamlit reruns. |
| UI | `core/ui/` | Glass CSS, UI helpers, animation/effect functions. |
| Models | `core/models/` | Indicators, ML bias, regime and quant math. |
| Storage | `core/storage/` | CSV/SQLite persistence and export helpers. |
| Tabs | `tabs/` + split folders | Top-level tab files stay thin. Heavy legacy implementations are isolated under split/legacy folders. |

## Compatibility kept

Old imports still work:

```python
from core.common import init_state, safe_float, synthetic_ohlc
from core.data_connectors import manual_connect, _normalize_ohlc
from core.database import append_csv, read_csv
from core.quant_models import quant_stack
from core.styles import apply_global_styles
```

This is important because many older tab patches import these names directly.

## Faster transition improvements

- `core/app/imports.py` caches tab imports.
- `core/app/routes.py` lazy-loads only the selected tab.
- `tabs/home_split/home.py`, `tabs/account_split/account.py`, and `tabs/train_data.py` now load heavy implementations only when the user opens that tab.
- `core/connectors/data_connectors.py` skips duplicate connector calls within a short hot-cache window when Streamlit reruns the same button action.
- `__pycache__` files are excluded from the final zip to keep upload/download lighter.

## Where to add future features

| New feature | Put it here |
|---|---|
| New tab | Add file under `tabs/<new_tab>/`, then register in `core/app/registry.py` and `core/config/defaults.py`. |
| New connector | `core/connectors/` and optionally re-export in `core/data_connectors.py`. |
| New metric/math | `core/models/` or a new focused file under that folder. |
| New UI effect/CSS | `core/ui/`. |
| New database/export logic | `core/storage/`. |
| New Train Data logic | `tabs/train/`, not the root `tabs/train_data.py` wrapper. |
| New Doo Prime/Home inner module | `tabs/home_split/` or `tabs/doo_prime/`. |

## Validation

Run:

```bash
python tools/validate_architecture.py
streamlit run main.py
```

The validator checks the modular file layout and compiles the Python files without needing MT5 or API keys.
