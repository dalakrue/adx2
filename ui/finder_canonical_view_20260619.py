"""Read-only Finder presentation of the current canonical priority generation."""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping
import pandas as pd
import streamlit as st

from core.canonical_runtime_20260617 import get_canonical
from core.compact_canonical_20260619 import ACTIVE_CALCULATION_ID_KEY, get_compact_summary
from core.performance_store_20260619 import frame_manifest, query_frame
from core.snapshot_schema_20260619 import verify_display_generation


def _m(value: Any) -> Mapping[str, Any]: return value if isinstance(value, Mapping) else {}


def _logical_key(state: Mapping[str, Any]) -> str:
    refs = state.get("disk_backed_frame_refs_20260619")
    if isinstance(refs, Mapping):
        for key in ("finder_readonly_priority_table_20260618", "canonical_priority_table_20260617", "full_metric_history_df_20260618"):
            if key in refs: return key
    return "canonical_priority_table_20260617"


def _time_col(columns: list[str]) -> str | None:
    return next((c for c in ("Time","time","Datetime","Date","candle time","Completed H1 candle") if c in columns), None)


def _hour_col(columns: list[str]) -> str | None:
    return next((c for c in ("Hour","hour","Session Hour") if c in columns), None)


def _first_col(columns: list[str], aliases: tuple[str,...]) -> str | None:
    lower={c.lower():c for c in columns}
    for name in aliases:
        if name.lower() in lower: return lower[name.lower()]
    return None


def render_finder_canonical_view(*, state: MutableMapping[str, Any] | None = None) -> None:
    state = state if state is not None else st.session_state
    canonical=get_canonical(state); summary=get_compact_summary(state)
    if not canonical:
        st.info("Run Calculation in Settings. Finder will read the completed canonical generation."); return
    guard=verify_display_generation(state, state.get("finder_synced_snapshot_20260618"))
    if not guard["ok"]:
        st.warning(f"Finder detected stale display data and reloaded canonical generation {guard.get('expected_generation')}.")
        try:
            from core.operational_sync_20260618 import ensure_generation_consistency
            ensure_generation_consistency(state)
        except Exception: pass
    identity=_m(summary.get("identity")); priority=_m(summary.get("priority")); plan=_m(state.get("position_sizing_plan_20260619") or canonical.get("risk_plan"))
    top=st.columns(4)
    top[0].metric("Run generation", str(identity.get("calculation_generation","-")))
    top[1].metric("Completed H1 candle", str(identity.get("latest_completed_candle_time","-"))[-22:])
    top[2].metric("Priority", f"{priority.get('opportunity_quality','WATCH')} / {priority.get('current_rank','N/A')}")
    top[3].metric("Aggregate lots", f"{float(plan.get('recommended_lots') or 0):.2f}", str(plan.get("status","BLOCK")))

    calc_id=str(state.get(ACTIVE_CALCULATION_ID_KEY) or ""); logical=_logical_key(state)
    manifest=frame_manifest(calc_id, logical) if calc_id else {}
    cols=list(manifest.get("columns") or [])
    if not cols:
        fallback=state.get("finder_readonly_priority_table_20260618")
        if not isinstance(fallback,pd.DataFrame): fallback=state.get("canonical_priority_table_20260617")
        if isinstance(fallback,pd.DataFrame) and not fallback.empty:
            cols=[str(c) for c in fallback.columns]
        else:
            st.info("Finder table is unavailable for this completed generation."); return
    time_col=_time_col(cols); hour_col=_hour_col(cols)
    # Fetch only a compact metadata slice to populate filter choices.
    seed_cols=[c for c in (time_col,hour_col) if c]
    seed=query_frame(calc_id,logical,columns=seed_cols,limit=500,order_by=time_col,descending=True) if calc_id and seed_cols else pd.DataFrame()
    f1,f2,f3=st.columns(3)
    dates=[]
    if time_col and time_col in seed:
        dates=[str(x) for x in pd.to_datetime(seed[time_col],errors="coerce",utc=True).dropna().dt.date.drop_duplicates().tolist()]
    selected_date=f1.selectbox("Finder day", ["All"]+dates, key="finder_canonical_day_20260619")
    hours=[]
    if hour_col and hour_col in seed: hours=sorted(seed[hour_col].dropna().astype(str).unique().tolist())
    selected_hour=f2.selectbox("Finder hour", ["All"]+hours, key="finder_canonical_hour_20260619")
    page_size=f3.selectbox("Rows per page", [25,50,100], index=1, key="finder_page_size_20260619")
    page=int(state.get("finder_page_20260619",0) or 0)
    nav1,nav2=st.columns(2)
    if nav1.button("Previous",use_container_width=True,disabled=page<=0,key="finder_prev_20260619"): state["finder_page_20260619"]=max(0,page-1); st.rerun()
    if nav2.button("Load more",use_container_width=True,key="finder_next_20260619"): state["finder_page_20260619"]=page+1; st.rerun()
    page=int(state.get("finder_page_20260619",0) or 0)
    where={}
    if selected_hour!="All" and hour_col: where[hour_col]=selected_hour
    date_filter={time_col:selected_date} if selected_date!="All" and time_col else None
    visible_aliases=(
        ("Date/time",("Time","time","Datetime","Date","candle time")),
        ("Direction",("Direction","direction","Decision")),
        ("Priority rank",("Priority Rank 1-14","Priority Rank","priority rank","Rank")),
        ("Priority score",("Priority Score","KNN Priority Score","priority score")),
        ("Reliability",("Reliability","Reliability %","reliability")),
        ("Market quality",("Market Quality","Market Quality 0-100","market quality")),
        ("Conflict status",("Conflict Status","Conflict","conflict status")),
        ("Counter-trend warning",("Counter Trend","Counter-trend warning","counter trend")),
        ("Expected move",("Expected Move","expected move","Expected Move Pips")),
        ("Current regime",("Current Regime","Major Regime","Regime")),
        ("Full Metric History agreement",("Full Metric History Agreement","Full Metric Agreement","Authority Agreement")),
    )
    selected_cols=[]; rename={}
    for label,aliases in visible_aliases:
        found=_first_col(cols,aliases)
        if found and found not in selected_cols: selected_cols.append(found); rename[found]=label
    if time_col and time_col not in selected_cols: selected_cols.insert(0,time_col); rename[time_col]="Date/time"
    if not selected_cols: selected_cols=cols[:12]
    if calc_id:
        view=query_frame(calc_id,logical,columns=selected_cols,limit=int(page_size),offset=page*int(page_size),order_by=time_col,descending=True,where_equals=where,date_equals=date_filter)
    else:
        fallback=state.get("finder_readonly_priority_table_20260618"); view=fallback.iloc[page*int(page_size):(page+1)*int(page_size)][selected_cols] if isinstance(fallback,pd.DataFrame) else pd.DataFrame()
    view=view.rename(columns=rename)
    view.insert(0,"Run generation",identity.get("calculation_generation"))
    view["Completed H1 candle"]=identity.get("latest_completed_candle_time")
    view["Risk status"]=plan.get("status","BLOCK")
    view["Suggested aggregate lot size"]=plan.get("recommended_lots",0.0)
    st.dataframe(view,use_container_width=True,hide_index=True,height=430)

    st.markdown("#### Best two entries")
    top_two=priority.get("top_two") or canonical.get("top_two_daily_candidates") or []
    st.dataframe(pd.DataFrame(top_two[:2]) if top_two else pd.DataFrame([{"Status":"No canonical entry candidate; Finder does not fabricate one."}]),use_container_width=True,hide_index=True)
    with st.expander("Open / Close — selected-row explanation",expanded=False):
        st.write("Finder is presentation-only. Direction, priority, reliability, conflict, regime, and Full Metric agreement come from the same completed canonical generation.")
        st.json({"run_id":identity.get("run_id"),"generation":identity.get("calculation_generation"),"risk_plan":dict(plan),"filters":{"date":selected_date,"hour":selected_hour,"page":page}})
    with st.expander("Open / Close — replay / history and advanced diagnostics",expanded=False):
        st.caption(f"Disk-backed table: {logical} · stored rows: {manifest.get('row_count','unknown')} · page {page+1}")

__all__=["render_finder_canonical_view"]
