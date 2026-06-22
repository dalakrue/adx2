from __future__ import annotations

import pandas as pd

from core.decision_contract_20260617 import DataQualityResult, DriftResult, NLPResult
from core.decision_product_engine_20260617 import _actionability


def test_moderate_soft_evidence_does_not_create_hard_blocker():
    probability, label, _, blockers, _ = _actionability(
        pd.DataFrame(), probability=0.72, interval_ratio=0.004, priority=62,
        expected_value=0.0002, transition=0.60,
        drift=DriftResult(status="DEGRADED"),
        quality=DataQualityResult(status="PASS_WITH_WARNING", score=90),
        nlp=NLPResult(conflict_level="HIGH", importance=0.70),
    )
    assert probability > 0
    assert blockers == []
    assert label in {"YES", "NO"}  # coverage gate may remain conservative, but not hard-blocked


def test_negative_ev_and_critical_data_are_hard_blockers():
    _, label, _, blockers, _ = _actionability(
        pd.DataFrame(), probability=0.80, interval_ratio=0.001, priority=90,
        expected_value=-0.0001, transition=0.20,
        drift=DriftResult(status="STABLE"),
        quality=DataQualityResult(status="FAIL_ALL", score=0),
        nlp=NLPResult(conflict_level="NONE", importance=0.0),
    )
    assert label == "NO"
    assert "negative expected value after costs" in blockers
    assert "critical market data quality failure" in blockers
