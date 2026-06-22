from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd

# The lightweight unit-test environment intentionally does not install Streamlit.
# Rendering is covered by source-contract assertions; pure collectors use this stub.
def _cache_resource(*args, **kwargs):
    def decorator(fn):
        return fn
    return decorator

sys.modules.setdefault("streamlit", SimpleNamespace(session_state={}, cache_resource=_cache_resource))

from ui.full_metric_regime_inner_renderer_20260618 import (
    build_existing_regime_summary,
    collect_existing_regime_tables,
)


ROOT = Path(__file__).resolve().parents[1]


def _state():
    history = pd.DataFrame([
        {"Regime": "BULL_NORMAL", "Start": "2026-06-18T05:00:00Z", "End": "2026-06-18T06:00:00Z", "Duration Hours": 4},
        {"Regime": "RANGE_NORMAL", "Start": "2026-06-18T01:00:00Z", "End": "2026-06-18T04:00:00Z", "Duration Hours": 4},
    ])
    knn = history.assign(**{"Similarity %": [94.0, 82.0], "KNN Regime Priority": [1, 2]})
    return {
        "regime_context_20260614": {
            "metrics": {
                "Current Regime": "BULL_NORMAL",
                "Regime Direction": "BUY",
                "Regime Confidence %": 74.0,
                "Regime Reliable Score": 71.0,
                "Transition Risk %": 24.0,
                "Estimated Remaining Hours": 9,
                "Regime Sync Source": "Canonical Full Metric generation",
            },
            "history": history,
            "knn": knn,
        },
        "full_metric_regime_history_df": history,
        "regime_standard_detail_tables_published_20260618": {
            "lower": history.head(1),
            "medium": knn.assign(**{"Standard": "Medium Standard"}),
            "higher": knn.assign(**{"Standard": "Higher Standard"}),
        },
    }


def _result():
    return {
        "history": pd.DataFrame([
            {
                "Time": "2026-06-18T06:00:00Z",
                "Direction": "BUY",
                "Regime": "BULL_NORMAL",
                "Major Regime": "BULL_NORMAL",
                "Alpha": 1.2,
                "Delta": 0.3,
                "Regime Confidence %": 74.0,
            }
        ])
    }


def test_regime_summary_reuses_existing_values_and_alpha_delta_interpretation():
    summary = build_existing_regime_summary(_result(), state=_state())
    values = dict(zip(summary["Regime Field"], summary["Value"]))
    assert values["Current Regime"] == "BULL_NORMAL"
    assert values["Current Major Regime"] == "BULL_NORMAL"
    assert values["Alpha"] == 1.2
    assert values["Delta"] == 0.3
    assert values["Interpretation"] == "Bullish advantage strengthening"


def test_existing_regime_tables_are_collected_without_recalculation():
    tables = collect_existing_regime_tables(_result(), state=_state())
    titles = [title for title, _ in tables]
    assert titles == [
        "Medium Standard Regime — About 5 Days",
        "Higher Standard Regime — About 25 Days",
    ]
    assert all("Lower" not in title and "Current" not in title and "Every" not in title for title in titles)
    assert all(isinstance(frame, pd.DataFrame) and not frame.empty for _, frame in tables)


def test_active_full_metric_paths_render_regime_tables_directly_visible():
    shared = (ROOT / "ui" / "full_metric_shared_renderer_20260618.py").read_text(encoding="utf-8")
    lunch = (ROOT / "ui" / "lunch_restored.py").read_text(encoding="utf-8")
    renderer = (ROOT / "ui" / "full_metric_regime_inner_renderer_20260618.py").read_text(encoding="utf-8")
    assert "render_existing_regime_inner_section(result)" in shared
    assert "render_existing_regime_inner_section(result)" in lunch
    # The restored existing section must not be hidden behind a second control.
    assert "st.expander(" not in renderer
    assert ".button(" not in renderer
    assert "st.tabs(" not in renderer
