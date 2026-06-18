"""One-click Settings calculation orchestrator.

This module does not add a prediction model. It calls the project's existing
Lunch, PowerBI, regime, NLP and shared-sync functions once, stores their normal
caches, and then lets the Lunch page render those caches without another Run or
Load button.
"""
from __future__ import annotations

import time
from typing import Any, Dict

import pandas as pd
import streamlit as st


REGIME_NLP_HISTORY_DAYS = 25


def _call(ns: Dict[str, Any], name: str, *args: Any, **kwargs: Any) -> Any:
    fn = ns.get(name)
    if not callable(fn):
        raise RuntimeError(f"Existing function {name} is unavailable")
    return fn(*args, **kwargs)


def _build_lunch_metric(ns: Dict[str, Any]) -> Dict[str, Any]:
    result = _call(ns, "_get_cached_lunch_metric_result", True)
    if not isinstance(result, dict):
        return {"ok": False, "message": "Lunch metric returned an unsupported result."}
    if result.get("ok"):
        st.session_state["lunch_show_full_metric_details"] = True
        try:
            _call(ns, "_get_cached_lunch_copy_payload", True)
        except Exception:
            pass
        try:
            scan = _call(ns, "_load_reversal_scan")
            if isinstance(scan, pd.DataFrame) and not scan.empty:
                st.session_state["home_reversal_25d_scan"] = scan
        except Exception:
            pass
    return result


def _build_powerbi(ns: Dict[str, Any], validated_df: pd.DataFrame | None = None) -> Dict[str, Any]:
    rows_limit = int(st.session_state.get("dv_pp_rows", 10000) or 10000)
    horizon = int(st.session_state.get("dv_pp_horizon", 36) or 36)
    min_days = int(st.session_state.get("dv_pp_min_days", 5) or 5)
    bt_lookback = int(st.session_state.get("dv_pp_bt", 180) or 180)

    raw = validated_df if isinstance(validated_df, pd.DataFrame) and not validated_df.empty else _call(ns, "_clean_lunch_visual_df", limit=rows_limit)
    data = _call(ns, "_dv_prepare_ohlc_v20260609", raw, limit=rows_limit)
    if not isinstance(data, pd.DataFrame) or data.empty or len(data) < 120:
        return {
            "ok": False,
            "message": "PowerBI needs at least 120 clean OHLC rows.",
            "rows": int(len(data)) if isinstance(data, pd.DataFrame) else 0,
        }

    base_result = _call(ns, "_five_layer_powerbi_calculate", data, horizon=horizon)
    predicted = _call(ns, "_dv_predict_future_candles_v20260609", data, horizon=horizon)
    bt_hist, bt_summary = _call(ns, "_dv_prediction_vs_actual_history_v20260609", data, lookback=bt_lookback, horizon=1)

    # Deterministic accuracy/reliability post-calibration. The original model
    # outputs are preserved; this adds a shared main path and empirical bands
    # based on completed prediction-vs-actual error and path agreement.
    yellow_current = pd.DataFrame()
    blue_previous = pd.DataFrame()
    yellow_builder = ns.get("_build_last_candle_yellow_6h_projection_v5")
    if callable(yellow_builder):
        try:
            yellow_current = yellow_builder(data, horizon=min(24, horizon), mode="Balanced", risk_filter="Medium")
        except Exception:
            yellow_current = pd.DataFrame()
        try:
            blue_previous = yellow_builder(data.iloc[:-1], horizon=min(24, horizon), mode="Balanced", risk_filter="Medium")
        except Exception:
            blue_previous = pd.DataFrame()
    try:
        from core.powerbi_path_calibration_20260617 import calibrate_projection_bundle, calibrated_candles
        regime_reliability = None
        regime_ctx = st.session_state.get("regime_context_20260614")
        if isinstance(regime_ctx, dict):
            metrics = regime_ctx.get("metrics", {}) if isinstance(regime_ctx.get("metrics"), dict) else {}
            regime_reliability = metrics.get("Regime Reliable Score") or metrics.get("Regime Reliability")
        regime_name = None
        conflict_state = None
        if isinstance(regime_ctx, dict):
            summary_ctx = regime_ctx.get("summary") if isinstance(regime_ctx.get("summary"), dict) else {}
            regime_name = regime_ctx.get("current_regime") or regime_ctx.get("Current Regime") or summary_ctx.get("Current Regime")
            conflict_state = regime_ctx.get("conflict") or regime_ctx.get("transition_risk")
        calibrated_bundle = calibrate_projection_bundle(
            data,
            red=predicted,
            yellow=yellow_current,
            blue=blue_previous,
            horizon=horizon,
            bt_history=bt_hist,
            bt_summary=bt_summary,
            regime_reliability=regime_reliability,
            current_regime=regime_name,
            transition_or_conflict=conflict_state,
            source_data_timestamp=data["time"].iloc[-1] if "time" in data.columns else None,
        )
        # Additive combination upgrade only: existing red/yellow/blue paths and
        # their raw outputs are preserved in the audit. Settled residual MSE,
        # Wiener gain and lagged residual correlation determine adaptive weights
        # before any visual step limiting is applied.
        try:
            from core.powerbi_mmse_weighting_20260618 import upgrade_projection_bundle
            support_cache = st.session_state.get("causal_quant_support_20260618")
            support_cache = support_cache if isinstance(support_cache, dict) else {}
            calibrated_bundle = upgrade_projection_bundle(
                calibrated_bundle,
                market_data=data,
                regime_conditioned_distributions=support_cache.get("regime_conditioned_distributions"),
                transition_state=(support_cache.get("transition_risk") or {}).get("status", conflict_state),
            )
        except Exception as exc:
            calibrated_bundle.setdefault("audit", {})["mmse_weighting_error"] = str(exc)[:240]
        calibrated_prediction = calibrated_candles(
            calibrated_bundle,
            anchor_price=float(data["close"].iloc[-1]),
        )
    except Exception as exc:
        calibrated_bundle = {"ok": False, "message": str(exc)}
        calibrated_prediction = pd.DataFrame()

    projection_history = _call(
        ns,
        "_dv_dynamic_projection_history_v20260609",
        data,
        lookback_days=10,
        horizon=min(6, horizon),
    )
    regime_summary, regime_hist = _call(
        ns,
        "_dv_major_regime_detector_v20260609",
        data,
        min_days=float(min_days),
        lookback_days=240,
        horizon=horizon,
    )
    recent = _call(ns, "_dv_last_continuous_days_v20260609", data, days=10)
    lightblue = _call(ns, "_dv_build_lightblue_path_v20260609", recent, predicted)
    sorter = ns.get("_dv_sort_newest_first_v20260609")
    if callable(sorter):
        bt_hist = sorter(bt_hist)
        regime_hist = sorter(regime_hist)

    signature_fn = ns.get("_lunch_df_signature")
    data_signature = signature_fn() if callable(signature_fn) else (len(data), str(data.iloc[-1].get("time", "")))
    signature = (data_signature, rows_limit, horizon, min_days, bt_lookback, "settings_auto_powerbi_20260617")

    st.session_state.update({
        "lunch_bi_visual_ready": True,
        "dv_pp_df": data,
        "dv_pp_base_result": base_result,
        "dv_pp_predicted": predicted,
        "dv_pp_predicted_calibrated_20260617": calibrated_prediction,
        "powerbi_calibrated_bundle_20260617": calibrated_bundle,
        "powerbi_path_audit_20260618": calibrated_bundle.get("audit", {}) if isinstance(calibrated_bundle, dict) else {},
        "dv_pp_lightblue_path": lightblue,
        "dv_pp_projection_history": projection_history,
        "dv_pp_bt_hist": bt_hist,
        "dv_pp_bt_summary": bt_summary,
        "dv_pp_regime_summary": regime_summary,
        "dv_pp_regime_hist": regime_hist,
        "dv_pp_sig": signature,
        "show_restored_powerbi_20260617": True,
        "load_original_powerbi_from_antd_lunch_20260615": True,
    })
    return {
        "ok": True,
        "rows": int(len(data)),
        "predicted_rows": int(len(predicted)) if isinstance(predicted, pd.DataFrame) else 0,
        "calibrated_rows": int(len(calibrated_prediction)) if isinstance(calibrated_prediction, pd.DataFrame) else 0,
        "path_reliability_pct": ((calibrated_bundle.get("summary") or {}).get("reliability_pct") if isinstance(calibrated_bundle, dict) else None),
        "backtest_rows": int(len(bt_hist)) if isinstance(bt_hist, pd.DataFrame) else 0,
    }


def _source_identity() -> tuple[str, str, str]:
    # Operational decisions in this product are intentionally fixed to the
    # protected EURUSD completed-H1 authority. M1 remains a timing input only.
    source = str(st.session_state.get("data_source") or st.session_state.get("selected_source") or st.session_state.get("source") or "SESSION")
    return "EURUSD", "H1", source


def _preflight_dataframe(ns: Dict[str, Any]) -> pd.DataFrame:
    """Deterministically select a timestamped OHLC source for the Settings run.

    Production decisions never manufacture timestamps and never select merely the
    first non-empty frame.  Candidates are scored by schema validity, explicit
    source preference, row count and latest completed timestamp.
    """
    candidates: list[tuple[str, pd.DataFrame]] = []
    for name, args in (("_clean_lunch_visual_df", (10000,)), ("_prepare_lunch_df", ()), ("_get_lunch_df", ())):
        fn = ns.get(name)
        if callable(fn):
            try:
                value = fn(*args) if args else fn()
            except TypeError:
                try:
                    value = fn(limit=10000)
                except Exception:
                    value = None
            except Exception:
                value = None
            if isinstance(value, pd.DataFrame) and not value.empty:
                candidates.append((name, value))
    for key in ("dv_pp_df", "lunch_5layer_powerbi_df", "last_df", "ohlc_df", "df"):
        value = st.session_state.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            candidates.append((key, value))

    preference = {"_clean_lunch_visual_df": 35, "dv_pp_df": 34, "lunch_5layer_powerbi_df": 32, "last_df": 30, "_prepare_lunch_df": 26, "ohlc_df": 22, "df": 18, "_get_lunch_df": 16}
    best = pd.DataFrame()
    best_score = float("-inf")
    for name, raw in candidates:
        frame = raw
        lower = {str(c).strip().lower(): c for c in frame.columns}
        time_col = next((lower[k] for k in ("time", "datetime", "timestamp", "date_time", "date") if k in lower), None)
        close_col = next((lower[k] for k in ("close", "c") if k in lower), None)
        if time_col is None or close_col is None:
            continue
        parsed = pd.to_datetime(frame[time_col], errors="coerce", utc=True)
        valid_count = int(parsed.notna().sum())
        if valid_count < 30:
            continue
        latest = parsed.max()
        if pd.isna(latest):
            continue
        ohlc_count = sum(1 for key in ("open", "high", "low", "close") if key in lower)
        duplicate_penalty = float(parsed.duplicated().mean() * 40.0)
        score = float(preference.get(name, 0)) + min(valid_count, 10000) / 250.0 + ohlc_count * 4.0 - duplicate_penalty
        # Reject explicitly mismatched identities; missing metadata remains a
        # lower-confidence fallback for legacy frames.
        attrs = getattr(frame, "attrs", {}) or {}
        active_identity = dict(zip(("symbol", "timeframe", "source"), _source_identity()))
        identity_mismatch = False
        for field in ("symbol", "timeframe", "source"):
            declared = attrs.get(field)
            active = active_identity.get(field)
            if declared and active:
                if str(declared).upper() != str(active).upper():
                    identity_mismatch = True
                    break
                score += 8.0
        if identity_mismatch:
            continue
        previous = st.session_state.get("canonical_decision_result_20260617") or {}
        declared_run = attrs.get("run_id")
        declared_signature = attrs.get("data_signature")
        if declared_run and previous.get("run_id"):
            score += 6.0 if str(declared_run) == str(previous.get("run_id")) else -18.0
        if declared_signature and previous.get("data_signature"):
            score += 6.0 if str(declared_signature) == str(previous.get("data_signature")) else -12.0
        if score > best_score:
            best = frame
            best_score = score
            st.session_state["selected_ohlc_source_key_20260617"] = name
            st.session_state["selected_ohlc_latest_time_20260617"] = latest.isoformat()
    return best


def run_settings_calculation(ns: Dict[str, Any]) -> Dict[str, Any]:
    """Build all existing caches once, then atomically publish one canonical result."""
    started = time.time()
    perf_started = time.perf_counter()
    try:
        import psutil
        _process = psutil.Process()
        rss_before = int(_process.memory_info().rss)
    except Exception:
        _process = None
        rss_before = 0
    lock_key = "settings_calculation_lock_20260617"
    lock_time_key = "settings_calculation_lock_time_20260617"
    now = time.time()
    if st.session_state.get(lock_key) and now - float(st.session_state.get(lock_time_key, 0) or 0) < 300:
        return {
            "ok": False, "duplicate_blocked": True,
            "errors": ["A calculation is already running; duplicate execution was blocked."],
            "built_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    st.session_state[lock_key] = True
    st.session_state[lock_time_key] = now

    symbol, timeframe, source = _source_identity()
    status: Dict[str, Any] = {
        "ok": True, "metric": {}, "powerbi": {}, "data_quality": {}, "ledger": {},
        "canonical": {}, "calibration": {}, "drift": {}, "errors": [],
    }
    nlp_result: Dict[str, Any] = {}
    research_pack: Dict[str, Any] = {}
    detail_tables: Dict[str, Any] = {}
    standards = pd.DataFrame()
    try:
        from core.operational_sync_20260618 import clear_operational_errors
        clear_operational_errors(st.session_state)
    except Exception:
        pass
    try:
        from core.decision_product_engine_20260617 import validate_data_quality
        from core.prediction_ledger_20260617 import get_prediction_ledger
        ledger = get_prediction_ledger()
        preflight = _preflight_dataframe(ns)
        quality, clean_preflight = validate_data_quality(
            preflight, symbol=symbol, timeframe=timeframe, source=source,
        )
        status["data_quality"] = {
            "status": quality.status, "score": quality.score,
            "warnings": quality.warnings, "blocking_reasons": quality.blocking_reasons,
        }
        # Settlements use only completed candles and run before a new prediction is written.
        status["outcome_settlement"] = ledger.settle_pending_outcomes(clean_preflight)
        status["ledger"] = ledger.health()

        if quality.status == "FAIL_ALL":
            failed_run_id = f"FAILED-{pd.Timestamp.utcnow().strftime('%Y%m%dT%H%M%S')}-{int(time.time()*1000)%1000000:06d}"
            ledger.record_failed_run({
                "run_id": failed_run_id,
                "created_at": pd.Timestamp.utcnow().isoformat(),
                "symbol": symbol, "timeframe": timeframe, "source": source,
                "data_signature": "preflight-failed", "model_version": "existing-models-v1",
                "calculation_version": "decision-product-20260617-v1", "schema_version": "2.0.0",
                "data_quality": {"status": quality.status}, "calculation_status": "FAILED",
                "failure_reason": "; ".join(quality.blocking_reasons),
                "market": {"latest_completed_candle_time": None},
            })
            status["ok"] = False
            status["errors"].append("Data quality FAIL_ALL: " + "; ".join(quality.blocking_reasons))
            st.session_state["canonical_decision_attempt_20260617"] = {
                "run_id": failed_run_id, "calculation_status": "FAILED",
                "failure_reason": "; ".join(quality.blocking_reasons),
                "data_quality": status["data_quality"],
            }
            return status

        # One private staging frame is the only OHLC input for this calculation.
        # It is not published to legacy keys until the complete canonical run succeeds.
        clean_preflight = clean_preflight.copy(deep=False)
        clean_preflight.attrs.update({"symbol": symbol, "timeframe": timeframe, "source": source, "validation_status": quality.status})
        st.session_state["calculation_staging_ohlc_df_20260617"] = clean_preflight

        if quality.status == "FAIL_MODEL":
            st.session_state["data_quality_disabled_models_20260617"] = list(quality.model_disabled)
            status["errors"].append(
                "Data quality FAIL_MODEL: affected models are blocked in the final policy ("
                + ", ".join(quality.model_disabled or ["unspecified model group"]) + ")"
            )
        else:
            st.session_state["data_quality_disabled_models_20260617"] = []

        try:
            from ui.home_master_control_bar_20260615 import run_home_calculation_gate
            run_home_calculation_gate()
        except Exception:
            for key in ("metric_run_calculate", "research_run_calculate", "other_run_calculate"):
                st.session_state[key] = True

        st.session_state.update({
            "metric_run_calculate": True,
            "research_run_calculate": True,
            "other_run_calculate": True,
            "lunch_force_reversal_scan": True,
            "lunch_run_visualization": True,
            "lunch_bi_visual_ready": True,
            "show_restored_original_lunch_20260617": True,
            "show_restored_metric_detail_20260617": True,
            "show_restored_metric_history_20260617": True,
            "show_restored_powerbi_20260617": True,
            "settings_auto_open_lunch_20260617": True,
            "dinner_load_original_advanced_details_20260614": True,
            "dinner_auto_sync_from_main_run_20260617": True,
            "regime_auto_sync_from_main_run_20260617": True,
        })

        try:
            status["metric"] = _build_lunch_metric(ns)
            if not status["metric"].get("ok"):
                status["ok"] = False
                status["errors"].append(status["metric"].get("message", "Lunch metric was not ready."))
        except Exception as exc:
            status["ok"] = False
            status["metric"] = {"ok": False, "message": str(exc)}
            status["errors"].append(f"Lunch metric: {exc}")

        try:
            status["powerbi"] = _build_powerbi(ns, validated_df=clean_preflight)
            if not status["powerbi"].get("ok"):
                status["ok"] = False
                status["errors"].append(status["powerbi"].get("message", "PowerBI was not ready."))
        except Exception as exc:
            status["ok"] = False
            status["powerbi"] = {"ok": False, "message": str(exc)}
            status["errors"].append(f"PowerBI: {exc}")

        # NLP, Data Analysis and Data Mining are built in this same Settings
        # transaction. Finnhub remains optional; cached/persisted 10-day real
        # news is used honestly when the live source returns fewer rows.
        try:
            from ui.nlp_research_panel import run_nlp_analysis
            nlp_result = run_nlp_analysis(force_news=False, use_finbert=False)
            articles = nlp_result.get("articles") if isinstance(nlp_result, dict) else None
            status["nlp"] = {
                "ok": bool(nlp_result),
                "source": "cached/local or optional Finnhub",
                "article_rows": int(len(articles)) if isinstance(articles, pd.DataFrame) else 0,
                "window_days": 10,
            }
        except Exception as exc:
            nlp_result = {}
            status["nlp"] = {"ok": False, "message": str(exc)}
            status["errors"].append(f"NLP: {exc}")
        try:
            from tabs.research import build_all_research_pack_for_settings
            research_pack = build_all_research_pack_for_settings(clean_preflight, nlp_result=nlp_result)
            status["research"] = {
                "ok": bool(research_pack.get("all_inner_tabs_ready")),
                "data_analysis": bool((research_pack.get("data_analysis") or {}).get("ok")),
                "data_mining": bool((research_pack.get("data_mining") or {}).get("ok")),
                "nlp": bool(research_pack.get("nlp")),
            }
        except Exception as exc:
            research_pack = {}
            status["research"] = {"ok": False, "message": str(exc)}
            status["errors"].append(f"Research/Data Mining: {exc}")

        # Prime the deepest existing regime/reliability caches once inside the
        # main Settings workflow. Dinner/Regime renderers only read these caches
        # and never expose another Run or Load control.
        status["inner_sections"] = {}
        for builder_name, label in (
            ("build_reliability_control_center_20260614", "reliability"),
            ("build_regime_context_20260614", "regime"),
        ):
            builder = ns.get(builder_name)
            if callable(builder):
                try:
                    built = builder(force=True)
                    status["inner_sections"][label] = {"ok": bool(built), "source": builder_name}
                except TypeError:
                    try:
                        built = builder(True)
                        status["inner_sections"][label] = {"ok": bool(built), "source": builder_name}
                    except Exception as exc:
                        status["inner_sections"][label] = {"ok": False, "message": str(exc)}
                        status["errors"].append(f"{label.title()} inner cache: {exc}")
                except Exception as exc:
                    status["inner_sections"][label] = {"ok": False, "message": str(exc)}
                    status["errors"].append(f"{label.title()} inner cache: {exc}")
            else:
                status["inner_sections"][label] = {"ok": False, "message": "Existing builder unavailable"}

        try:
            from core.adx_shared_sync_20260615 import ensure_shared_calculation_result
            legacy_shared = ensure_shared_calculation_result(force=True)
        except Exception as exc:
            legacy_shared = {}
            status["errors"].append(f"Shared sync: {exc}")

        try:
            from core.regime_sync_20260617 import canonical_regime_snapshot, regime_standard_table, regime_standard_detail_tables
            canonical_regime_snapshot(days=25)
            standards = regime_standard_table(force=True)
            detail_tables = regime_standard_detail_tables(force=False)
            status["regime_detail_tables"] = {k: int(len(v)) for k, v in detail_tables.items() if isinstance(v, pd.DataFrame)}
            st.session_state["regime_standard_table_20260617"] = standards
            st.session_state["regime_standard_detail_tables_published_20260618"] = detail_tables
            # Carry the existing 1-day, 5-day and 25-day standards into the same
            # immutable result instead of letting the Regime page calculate a
            # second, newer copy after Lunch/PowerBI have already finished.
            if isinstance(legacy_shared, dict) and isinstance(standards, pd.DataFrame) and not standards.empty:
                regime_payload = legacy_shared.setdefault("regime", {})
                for _, row in standards.iterrows():
                    label = str(row.get("Standard", "")).lower()
                    value = str(row.get("Major Regime", "UNKNOWN") or "UNKNOWN")
                    if "lower" in label:
                        regime_payload["lower_standard_regime"] = value
                    elif "middle" in label:
                        regime_payload["middle_standard_regime"] = value
                    elif "higher" in label:
                        regime_payload["higher_standard_regime"] = value
                regime_payload["standards"] = standards.to_dict("records")
        except Exception as exc:
            status["errors"].append(f"Regime sync: {exc}")

        canonical_priority_table = pd.DataFrame()
        try:
            from core.regime_sync_20260617 import merged_hourly_regime_nlp_priority
            canonical_priority_table = merged_hourly_regime_nlp_priority(days=REGIME_NLP_HISTORY_DAYS)
            status["canonical_priority_rows"] = int(len(canonical_priority_table)) if isinstance(canonical_priority_table, pd.DataFrame) else 0
        except Exception as exc:
            status["errors"].append(f"Canonical 25-day priority table: {exc}")

        # One causal 600-row Alpha/Delta history feeds all three regime standards.
        try:
            from core.regime_window_analytics_20260618 import build_regime_window_analytics
            legacy_regime = legacy_shared.get("regime", {}) if isinstance(legacy_shared, dict) and isinstance(legacy_shared.get("regime"), dict) else {}
            existing_regime = legacy_regime.get("current") or legacy_regime.get("current_regime") or ""
            existing_rel = ((legacy_shared.get("reliability") or {}).get("score", 50) if isinstance(legacy_shared, dict) else 50)
            window_analytics = build_regime_window_analytics(clean_preflight, existing_regime=str(existing_regime), existing_reliability=float(existing_rel or 50))
            st.session_state["regime_window_analytics_20260618"] = window_analytics
            if isinstance(legacy_shared, dict):
                legacy_shared.setdefault("regime", {})["window_analytics"] = window_analytics
                legacy_shared["regime_window_analytics"] = window_analytics
                bundle = st.session_state.get("powerbi_calibrated_bundle_20260617")
                if isinstance(bundle, dict):
                    legacy_shared.setdefault("powerbi", {})["calibrated_bundle"] = bundle
            status["regime_window_analytics"] = {"ok": bool(window_analytics.get("ok")), "rows": int(window_analytics.get("actual_history_rows", 0))}
        except Exception as exc:
            status["errors"].append(f"Regime window analytics: {exc}")

        try:
            from core.decision_product_engine_20260617 import build_decision_result, serialize_result
            from core.canonical_runtime_20260617 import proposed_generation, publish_canonical_atomically
            from core.full_metric_canonical_adapter_20260618 import (
                apply_canonical_confirmations,
                build_full_metric_authority,
                enrich_canonical_payload,
            )
            final_df = clean_preflight
            generation = proposed_generation(st.session_state)

            # The 25-day regime/NLP table remains a confirmation source. The
            # canonical priority table itself is ranked from the protected Full
            # Metric history, so no downstream tab can calculate another bias.
            confirmation_priority_table = canonical_priority_table
            full_metric_authority = build_full_metric_authority(
                status.get("metric") or {},
                final_df,
                symbol=symbol,
                timeframe=timeframe,
                legacy_shared=legacy_shared,
                confirmation_table=confirmation_priority_table,
                data_quality_status=quality.status,
            )
            # Causal Research support is computed once from completed H1 rows and
            # protected Full Metric history. It cannot create or reverse a
            # direction; it only enriches candidates and may force WAIT.
            try:
                from core.causal_quant_support_20260618 import (
                    apply_support_to_authority,
                    build_causal_support_bundle,
                    public_support_view,
                )
                previous_support = st.session_state.get("causal_quant_support_20260618")
                previous_support = previous_support if isinstance(previous_support, dict) else {}
                causal_support = build_causal_support_bundle(
                    final_df,
                    full_metric_authority.get("priority_table"),
                    context=legacy_shared,
                    previous_cache=previous_support,
                )
                full_metric_authority = apply_support_to_authority(full_metric_authority, causal_support)
                st.session_state["causal_quant_support_20260618"] = causal_support
                public_causal_support = public_support_view(causal_support)
                if isinstance(legacy_shared, dict):
                    legacy_shared["research_support"] = public_causal_support
                    legacy_shared.setdefault("data_mining", {})["causal_quant_support"] = public_causal_support
                research_pack = st.session_state.get("research_pack_20260612")
                if isinstance(research_pack, dict):
                    research_pack["causal_quant_support"] = public_causal_support
                    st.session_state["research_pack_20260612"] = research_pack
                status["causal_support"] = {
                    "ok": True,
                    "cache_status": causal_support.get("cache_status"),
                    "rows": causal_support.get("retained_rows"),
                    "pattern": (causal_support.get("pattern_memory") or {}).get("pattern_confirmation"),
                    "transition": (causal_support.get("transition_risk") or {}).get("status"),
                    "actionability": (causal_support.get("actionability") or {}).get("current_label"),
                }
            except Exception as exc:
                causal_support = {
                    "version": "causal-quant-support-20260618-v1",
                    "cache_status": "SAFE_FALLBACK",
                    "pattern_memory": {"pattern_confirmation": "NEUTRAL", "pattern_confidence": 0.0},
                    "transition_risk": {"status": "WATCH", "value": 0.5},
                    "actionability": {"current_label": "WATCH", "status": "FAILED SAFELY"},
                    "failure": str(exc)[:300],
                }
                st.session_state["causal_quant_support_20260618"] = causal_support
                status["errors"].append(f"Causal Research support: {exc}")
            canonical_priority_table = full_metric_authority["priority_table"]
            canonical_obj = build_decision_result(
                legacy_shared=legacy_shared, ohlc=final_df, symbol=symbol,
                timeframe=timeframe, source=source, ledger=ledger,
                calculation_generation=generation,
                full_metric_snapshot=full_metric_authority["snapshot"],
            )
            canonical_base = serialize_result(canonical_obj)
            try:
                from core.causal_quant_support_20260618 import apply_support_to_canonical
                canonical_base = apply_support_to_canonical(canonical_base, causal_support)
            except Exception as exc:
                canonical_base.setdefault("metadata", {})["causal_support_apply_error"] = str(exc)[:240]
                canonical_base.setdefault("final_decision", {}).setdefault("blocking_reasons", []).append(
                    "Causal support failed safely; entry remains conservatively gated"
                )
                canonical_base["final_decision"]["final_decision"] = "WAIT"
                canonical_base["final_decision"]["tradeability_decision"] = "WAIT"
                canonical_base["final_decision"]["less_risky_decision"] = "WAIT"

            # Additive multi-scale volatility/risk calibration.  This layer never
            # changes the protected Full Metric formulas or the central red/yellow/
            # blue path.  It is calculated once inside this Settings transaction
            # and is then reused by every existing tab through the canonical adapter.
            from core.multiscale_probabilistic_upgrade_20260618 import (
                build_and_apply_upgrade,
                enrich_existing_regime_tables,
                invariant_report,
            )
            previous_upgrade = st.session_state.get("multiscale_probabilistic_upgrade_20260618")
            previous_upgrade = previous_upgrade if isinstance(previous_upgrade, dict) else {}
            canonical_base, upgrade_cache, upgraded_bundle = build_and_apply_upgrade(
                canonical_base,
                ohlc=final_df,
                calibrated_bundle=st.session_state.get("powerbi_calibrated_bundle_20260617"),
                prediction_history=st.session_state.get("dv_pp_bt_hist"),
                previous_cache=previous_upgrade,
            )
            st.session_state["multiscale_probabilistic_upgrade_20260618"] = upgrade_cache

            # Ten-paper causal calibration runs once inside the same Settings
            # transaction. It is optional and fail-safe: Full Metric History and
            # the previously valid canonical result remain publishable if this
            # enrichment fails. The red/yellow/blue central paths are preserved;
            # only empirical bands, uncertainty and validation metadata are added.
            research_result = {}
            try:
                from core.research_calibration_20260618 import (
                    ResearchStore,
                    build_research_layer_fail_safe,
                )
                research_store = ResearchStore()
                experiment_matrix, _, _ = research_store.performance_matrix()
                conformal_settlement = research_store.settle_conformal_predictions(final_df)
                research_outcomes = research_store.completed_conformal_outcomes(limit=5000)
                ledger_outcomes = ledger.settled_predictions(symbol=symbol, timeframe=timeframe, limit=6000)
                completed_sources = [frame for frame in (ledger_outcomes, research_outcomes) if isinstance(frame, pd.DataFrame) and not frame.empty]
                settled_research_predictions = pd.concat(completed_sources, ignore_index=True, sort=False) if completed_sources else pd.DataFrame()
                status["research_conformal_settlement"] = conformal_settlement
                previous_research = st.session_state.get("research_calibration_20260618")
                previous_research = previous_research if isinstance(previous_research, dict) else {}
                canonical_base, research_result, upgraded_bundle, research_layer_status = build_research_layer_fail_safe(
                    canonical_base,
                    ohlc=final_df,
                    calibrated_bundle=upgraded_bundle,
                    prediction_history=st.session_state.get("dv_pp_bt_hist"),
                    settled_predictions=settled_research_predictions,
                    previous_cache=previous_research,
                    experiment_performance_matrix=experiment_matrix,
                    # PBO/DSR remain honestly UNAVAILABLE until the registry has
                    # enough tested configurations and aligned realised returns.
                    strategy_returns=None,
                    number_of_trials=None,
                    sharpe_trials=None,
                )
                if research_layer_status.get("ok"):
                    st.session_state["research_calibration_20260618"] = research_result
                    status["research_calibration"] = {
                        "ok": True,
                        "calculation_id": research_result.get("canonical_calculation_id"),
                        "validation_status": research_result.get("validation_status"),
                        "residual_vectors": (research_result.get("conformal_prediction") or {}).get("residual_vector_count"),
                        "pbo_status": (research_result.get("pbo") or {}).get("status"),
                        "dsr_status": (research_result.get("dsr") or {}).get("validation_label"),
                        "invariants": research_result.get("invariants"),
                    }
                else:
                    status["research_calibration"] = {"ok": False, "optional": True, **research_layer_status}
            except Exception as exc:
                canonical_base.setdefault("metadata", {})["research_calibration_error"] = str(exc)[:500]
                canonical_base.setdefault("metadata", {})["research_calibration_status"] = "FAILED SAFELY"
                status["research_calibration"] = {"ok": False, "optional": True, "message": str(exc)}

            if isinstance(upgraded_bundle, dict):
                st.session_state["powerbi_calibrated_bundle_20260617"] = upgraded_bundle
                try:
                    from core.powerbi_path_calibration_20260617 import calibrated_candles
                    anchor = float(pd.to_numeric(final_df["close"], errors="coerce").dropna().iloc[-1])
                    st.session_state["dv_pp_predicted_calibrated_20260617"] = calibrated_candles(
                        upgraded_bundle, anchor_price=anchor
                    )
                except Exception as exc:
                    canonical_base.setdefault("metadata", {})["probabilistic_candle_refresh_error"] = str(exc)[:240]
            detail_tables, standards = enrich_existing_regime_tables(
                detail_tables, standards if isinstance(standards, pd.DataFrame) else pd.DataFrame(),
                canonical_base.get("multiscale_regime") or {},
                str(canonical_base.get("canonical_calculation_id") or ""),
            )
            st.session_state["regime_standard_detail_tables_20260617"] = detail_tables
            st.session_state["regime_standard_detail_tables_published_20260618"] = detail_tables
            st.session_state["regime_standard_table_20260617"] = standards
            status["multiscale_probabilistic_upgrade"] = {
                "ok": True,
                "calculation_id": canonical_base.get("canonical_calculation_id"),
                "volatility_regime": (canonical_base.get("multiscale_regime") or {}).get("current_volatility_regime"),
                "invariants": invariant_report(canonical_base),
            }
            full_metric_authority = apply_canonical_confirmations(
                full_metric_authority, canonical_base
            )
            # Refresh only the candidate display/status aliases after the existing
            # canonical gates settle. Protected Full Metric formulas and direction
            # remain untouched; this keeps Lunch, Dinner, Finder and AI identical.
            try:
                from core.causal_quant_support_20260618 import apply_support_to_authority
                full_metric_authority = apply_support_to_authority(full_metric_authority, causal_support)
            except Exception as exc:
                canonical_base.setdefault("metadata", {})["candidate_support_refresh_error"] = str(exc)[:240]
            canonical_priority_table = full_metric_authority["priority_table"]
            canonical = enrich_canonical_payload(canonical_base, full_metric_authority)
            # Publish only after the complete object and canonical priority table
            # validate. The previous valid run remains untouched on failure.
            adapter = publish_canonical_atomically(
                st.session_state, canonical, legacy_shared=legacy_shared,
                priority_table=canonical_priority_table,
            )
            # Publish one read-only generation to every page/inner-tab alias.
            # This is intentionally after the canonical atomic transaction so a
            # failed run can never leave Lunch/Finder/Dinner on mixed data.
            from core.operational_sync_20260618 import synchronize_published_generation
            status["operational_sync"] = synchronize_published_generation(
                st.session_state, canonical, adapter, canonical_priority_table
            )
            ledger_write = ledger.record_result(canonical)
            status["ledger_write"] = ledger_write
            if isinstance(research_result, dict) and research_result:
                try:
                    from core.research_calibration_20260618 import persist_research_result
                    status["research_persistence"] = persist_research_result(research_result)
                except Exception as exc:
                    status["research_persistence"] = {"ok": False, "status": "FAILED SAFELY", "reason": str(exc)}
            st.session_state["canonical_decision_attempt_20260617"] = {
                "run_id": canonical.get("run_id"), "calculation_status": canonical.get("calculation_status"),
                "failure_reason": None, "data_signature": canonical.get("data_signature"),
                "calculation_generation": canonical.get("calculation_generation"),
            }
            status["canonical"] = {
                "ok": True, "run_id": canonical.get("run_id"),
                "decision": (canonical.get("final_decision") or {}).get("final_decision"),
                "selected_horizon": (canonical.get("final_decision") or {}).get("selected_horizon"),
            }
            status["calibration"] = (canonical.get("reliability") or {}).get("calibration_by_horizon", {})
            status["drift"] = canonical.get("drift", {})
            status["canonical"]["calculation_generation"] = canonical.get("calculation_generation")
            status["calculation_generation"] = canonical.get("calculation_generation")
            status["run_id"] = canonical.get("run_id")
            status["canonical"]["priority_rows"] = int(len(canonical_priority_table)) if isinstance(canonical_priority_table, pd.DataFrame) else 0
            status["adapter_version"] = adapter.get("version") if isinstance(adapter, dict) else None
            # Publish the adapter details only after the canonical transaction
            # succeeds; failed attempts cannot overwrite the last valid generation.
            st.session_state["full_metric_authority_20260618"] = full_metric_authority
            st.session_state["canonical_completed_ohlc_df_20260617"] = clean_preflight
            st.session_state["last_df"] = clean_preflight
            if isinstance(st.session_state.get("dv_pp_df"), pd.DataFrame):
                st.session_state["lunch_5layer_powerbi_df"] = st.session_state["dv_pp_df"]

            # Finish the Research pack with the final canonical priority history
            # and causal evidence, then publish every existing workspace alias.
            if isinstance(research_pack, dict) and research_pack:
                research_pack["regime_nlp_history"] = canonical_priority_table
                research_pack["causal_quant_support"] = st.session_state.get("causal_quant_support_20260618", {})
                research_pack["ten_paper_research_calibration"] = st.session_state.get("research_calibration_20260618", {})
                research_pack["canonical_calculation_id"] = canonical.get("canonical_calculation_id")
                research_pack["research_calculation_id"] = (canonical.get("research_calibration") or {}).get("canonical_calculation_id")
                st.session_state["research_pack_20260612"] = research_pack
                try:
                    import json
                    from tabs.research import _safe as _research_safe
                    st.session_state["research_export_20260612"] = json.dumps(_research_safe(research_pack), indent=2, ensure_ascii=False, default=str)
                except Exception:
                    pass
            from core.system_wide_completion_20260618 import publish_system_wide_completion
            manifest = publish_system_wide_completion(
                st.session_state,
                canonical=canonical,
                adapter=adapter,
                priority_table=canonical_priority_table,
                metric_result=status.get("metric") or {},
                regime_detail_tables=detail_tables,
                nlp_result=nlp_result,
                research_pack=research_pack,
                powerbi_status=status.get("powerbi") or {},
                errors=status.get("errors") or [],
            )
            status["readiness"] = manifest
            # Persist full historical DataFrames only after every existing
            # renderer/readiness hook has consumed the successful generation.
            # Session state keeps at most a display page; the database retains
            # the complete rows for history and export queries.
            try:
                from core.compact_canonical_20260619 import get_compact_summary
                from core.performance_store_20260619 import (
                    spool_history_frames, spool_nested_history_frames, compact_adapter_frames, session_dataframe_audit, record_timing,
                )
                summary = get_compact_summary(st.session_state)
                calc_id = str(summary.get("calculation_id") or canonical.get("canonical_calculation_id") or canonical.get("run_id"))
                status["disk_backed_history"] = spool_history_frames(
                    st.session_state, calc_id, phone_mode=bool(st.session_state.get("phone_mode", False))
                )
                status["disk_backed_nested_history"] = spool_nested_history_frames(
                    st.session_state, calc_id, phone_mode=bool(st.session_state.get("phone_mode", False))
                )
                compact_adapter_frames(st.session_state, phone_mode=bool(st.session_state.get("phone_mode", False)))
                status["session_dataframe_audit_after"] = session_dataframe_audit(st.session_state)
                record_timing(st.session_state, "run_calculation", time.perf_counter() - perf_started, calculation_id=calc_id)
            except Exception as exc:
                status["disk_backed_history"] = {"ok": False, "optional_error": str(exc)}
            if not manifest.get("ready"):
                missing = [name for name, item in (manifest.get("components") or {}).items() if not bool((item or {}).get("ready"))]
                status["ok"] = False
                status["errors"].append("Published generation is partial: " + ", ".join(missing))
        except Exception as exc:
            status["ok"] = False
            status["errors"].append(f"Canonical decision: {exc}")
            st.session_state["canonical_decision_attempt_20260617"] = {
                "calculation_status": "FAILED", "failure_reason": str(exc),
                "preserved_last_valid": bool(st.session_state.get("last_valid_canonical_decision_result_20260617")),
            }

        status["elapsed_seconds"] = round(time.time() - started, 3)
        try:
            rss_after = int(_process.memory_info().rss) if _process is not None else 0
        except Exception:
            rss_after = 0
        try:
            import resource
            raw_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            peak_rss = raw_peak * 1024 if raw_peak < 10_000_000 else raw_peak
        except Exception:
            peak_rss = max(rss_before, rss_after)
        status["performance"] = {
            "duration_seconds": round(time.perf_counter() - perf_started, 6),
            "rss_before_bytes": rss_before, "rss_after_bytes": rss_after, "peak_rss_bytes": peak_rss,
            "measurement_scope": "server process; iPhone CPU/RAM is not observable from Streamlit server",
        }
        status["built_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["settings_run_status_20260617"] = status
        st.session_state["settings_run_complete_20260617"] = bool(status.get("canonical", {}).get("ok"))
        try:
            from core.operational_sync_20260618 import record_operational_error
            for message in status.get("errors", [])[-12:]:
                record_operational_error(st.session_state, "Settings Run Calculation", message, stage="calculation")
        except Exception:
            pass
        return status
    finally:
        status.setdefault("elapsed_seconds", round(time.time() - started, 3))
        status.setdefault("built_at", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.session_state["settings_run_status_20260617"] = status
        st.session_state.pop("calculation_staging_ohlc_df_20260617", None)
        st.session_state[lock_key] = False
