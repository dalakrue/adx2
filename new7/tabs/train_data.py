import time
import pandas as pd
import streamlit as st

from core.data_connectors import manual_connect, connect_history_60d
from core.database import append_csv, read_csv
from core.quant_models import add_indicators, quant_stack


def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _normalize_df(df):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "time" in out.columns:
        out["time"] = pd.to_datetime(out["time"], errors="coerce")
        out = out.dropna(subset=["time"]).sort_values("time").drop_duplicates("time", keep="last")
    for c in ["open", "high", "low", "close", "volume"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.reset_index(drop=True)


def _collect_training_rows(df, label="LIVE"):
    df = _normalize_df(df)
    if df.empty:
        return 0
    try:
        enriched = add_indicators(df.copy())
    except Exception:
        enriched = df.copy()
    enriched["train_label"] = label
    enriched["source"] = st.session_state.get("source", "UNKNOWN")
    enriched["symbol"] = st.session_state.get("symbol", "XAUUSD")
    enriched["timeframe"] = st.session_state.get("timeframe", "M1")
    existing = st.session_state.get("training_df")
    if existing is None or not isinstance(existing, pd.DataFrame) or existing.empty:
        combined = enriched
    else:
        combined = pd.concat([existing, enriched], ignore_index=True)
    if "time" in combined.columns:
        combined["time"] = pd.to_datetime(combined["time"], errors="coerce")
        combined = combined.dropna(subset=["time"]).sort_values("time").drop_duplicates(["symbol", "timeframe", "time"], keep="last")
    combined = combined.tail(250000).reset_index(drop=True)
    st.session_state.training_df = combined
    return len(enriched)


def _save_training_snapshot(df):
    if df is None or df.empty:
        return False, "No training data to save."
    try:
        row = {
            "time": pd.Timestamp.now(),
            "symbol": st.session_state.get("symbol", "XAUUSD"),
            "timeframe": st.session_state.get("timeframe", "M1"),
            "source": st.session_state.get("source", "UNKNOWN"),
            "rows": int(len(df)),
            "first_time": str(df["time"].min()) if "time" in df.columns else "",
            "last_time": str(df["time"].max()) if "time" in df.columns else "",
        }
        append_csv("training_snapshots", row)
        return True, "Training snapshot saved."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def _history_search_panel(df):
    st.markdown("### 📅 History Search by Day")
    if df is None or df.empty or "time" not in df.columns:
        st.info("No time-based data loaded yet.")
        return
    tmp = df.copy()
    tmp["time"] = pd.to_datetime(tmp["time"], errors="coerce")
    tmp = tmp.dropna(subset=["time"]).sort_values("time")
    if tmp.empty:
        st.info("Loaded data has no valid time column.")
        return
    min_day = tmp["time"].min().date()
    max_day = tmp["time"].max().date()
    chosen = st.date_input("Choose day to inspect", value=max_day, min_value=min_day, max_value=max_day, key="train_history_day")
    day_df = tmp[tmp["time"].dt.date == chosen]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows that day", len(day_df))
    if not day_df.empty:
        c2.metric("Open", round(float(day_df["open"].iloc[0]), 5) if "open" in day_df.columns else "N/A")
        c3.metric("Close", round(float(day_df["close"].iloc[-1]), 5) if "close" in day_df.columns else "N/A")
        if "close" in day_df.columns:
            change = (day_df["close"].iloc[-1] - day_df["close"].iloc[0]) / max(abs(day_df["close"].iloc[0]), 1e-9) * 100
            c4.metric("Day Change %", round(float(change), 4))
        st.line_chart(day_df.set_index("time")[["close"]]) if "close" in day_df.columns else None
        with st.expander("📋 Open raw day data table", expanded=False):
            st.dataframe(day_df.tail(1000), use_container_width=True, height=360)
    else:
        st.warning("No candles found for that day in the loaded dataset.")


def show():
    st.markdown("# 🧠 Train Data — Live Dataset Builder")
    st.caption("Connect once from the sidebar, then this tab keeps collecting the shared dataframe so you can see rows increase live.")

    with st.expander("Connector shortcut", expanded=False):
        c1, c2, c3 = st.columns(3)
        mode = st.selectbox("Source", ["sidebar/default", "mt5", "twelve", "doo_bridge", "fallback"], key="train_mode")
        bars = c1.number_input("Candles to request", 100, 250000, int(st.session_state.get("train_bars", 120000)), 1000, key="train_bars")
        tf = c2.selectbox("Timeframe", ["M1", "M2", "M3", "M5", "M10", "M15", "M30", "H1", "H4"], index=0, key="train_tf")
        c3.metric("Current Source", st.session_state.get("source", "DISCONNECTED"))
        if st.button("Load maximum history now", use_container_width=True, key="train_load_max"):
            chosen = st.session_state.get("connector_mode", "fallback") if mode == "sidebar/default" else mode
            df, ok, source, msg = connect_history_60d(
                mode=chosen,
                symbol=st.session_state.get("symbol", "XAUUSD"),
                api_key=st.session_state.get("twelve_api_key", ""),
                timeframe=tf,
                bridge_url=st.session_state.get("doo_bridge_url", ""),
                bridge_token=st.session_state.get("doo_bridge_token", ""),
            )
            st.success(f"Loaded {len(df):,} rows from {source}. {msg}")
            _safe_rerun()

    auto = st.checkbox("Auto collect latest shared data on every refresh", value=True, key="train_auto_collect")
    interval = st.slider("Auto-refresh seconds", 2, 60, int(st.session_state.get("train_refresh_seconds", 5)), key="train_refresh_seconds")
    if auto:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=interval * 1000, key="train_live_refresh")
        except Exception:
            pass

    df = _normalize_df(st.session_state.get("last_df"))
    if auto and not df.empty:
        _collect_training_rows(df, "AUTO")

    train_df = _normalize_df(st.session_state.get("training_df"))
    r = st.columns(5)
    r[0].metric("Connected rows", len(df))
    r[1].metric("Training rows", len(train_df))
    r[2].metric("Symbol", st.session_state.get("symbol", "XAUUSD"))
    r[3].metric("Timeframe", st.session_state.get("timeframe", "M1"))
    r[4].metric("Source", st.session_state.get("source", "DISCONNECTED"))

    b1, b2, b3 = st.columns(3)
    if b1.button("➕ Collect current data now", use_container_width=True):
        n = _collect_training_rows(df, "MANUAL")
        st.success(f"Collected {n:,} rows into training dataset.")
        _safe_rerun()
    if b2.button("💾 Save training snapshot", use_container_width=True):
        ok, msg = _save_training_snapshot(train_df)
        st.success(msg) if ok else st.error(msg)
    if b3.button("🧹 Clear training screen data", use_container_width=True):
        st.session_state.training_df = pd.DataFrame()
        _safe_rerun()

    if not train_df.empty:
        try:
            q = quant_stack(train_df.tail(2000), st.session_state.get("trade_history", []), st.session_state.get("account_snapshot", {}))
            m = st.columns(3)
            m[0].metric("Instant Bias", q.get("bias", "WAIT"))
            m[1].metric("Safety /10", q.get("scale10", 0))
            m[2].metric("Safety %", q.get("safe_pct", 0))
        except Exception as exc:
            st.warning(f"Instant result unavailable: {exc}")
        if "close" in train_df.columns and "time" in train_df.columns:
            st.line_chart(train_df.set_index("time")[["close"]].tail(1500))
        with st.expander("🧠 Open training feature table", expanded=False):
            st.dataframe(train_df.tail(1000), use_container_width=True, height=360)
        csv = train_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download training dataset CSV", csv, "training_dataset.csv", "text/csv", use_container_width=True)
    else:
        st.info("No training rows yet. Connect in the sidebar or load maximum history, then collection starts.")

    _history_search_panel(train_df if not train_df.empty else df)
