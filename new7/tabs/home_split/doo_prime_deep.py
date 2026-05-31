import time
import pandas as pd
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None

from core.data_connectors import manual_connect

# IMPORTANT:
# Do NOT import _calc_market_analytics from .implementation at module load time.
# implementation.py imports this file, so a top-level reverse import creates a circular import.
# Helpers are lazy-loaded only when this panel is rendering.

AUTO_REFRESH_SECONDS = 600  # 10 minutes
DEEP_BASE_BARS = 60000


def _safe_num(v, default=0.0):
    try:
        if v is None:
            return default
        out = float(v)
        if pd.isna(out):
            return default
        return out
    except Exception:
        return default


def _safe_int(v, default=0):
    try:
        return int(float(v))
    except Exception:
        return int(default)


def _lazy_impl_func(name, fallback=None):
    try:
        import importlib
        impl = importlib.import_module("tabs.home_split.implementation")
        return getattr(impl, name, fallback)
    except Exception:
        return fallback


def _analytics_status(name, value):
    fn = _lazy_impl_func("_analytics_status")
    if callable(fn):
        try:
            return fn(name, value)
        except Exception:
            pass
    return "NORMAL", "No threshold warning."


def _status_badge(status):
    fn = _lazy_impl_func("_status_badge")
    if callable(fn):
        try:
            return fn(status)
        except Exception:
            pass
    s = str(status or "").upper()
    if s in ["DANGEROUS", "EXTREME", "SHOCK"]:
        return "🔴"
    if s in ["WARNING", "STRONG", "STARTING", "LIMIT", "EXHAUSTION"]:
        return "🟡"
    if s in ["GOOD", "SAFE", "CONTINUING", "CONFIRMED"]:
        return "🟢"
    return "⚪"


DEEP_SPECS = [
    ("m1_600", "M1", 600, "M1 600 candles"),
    ("m1_60000", "M1", 60000, "M1 60,000 candles"),
    ("h1_600", "H1", 600, "H1 600 candles"),
    ("h1_60000", "H1", 60000, "H1 60,000 candles"),
]


def _empty_result(label, msg):
    return {
        "label": label,
        "ok": False,
        "message": msg,
        "rows": 0,
        "market": {},
        "frame": pd.DataFrame(),
        "fetched_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "partial": True,
        "quality": "NO DATA",
    }


def _normalize_local(df):
    """Normalize any candle-like dataframe to time/open/high/low/close/volume."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    out = df.copy()
    rename = {
        "datetime": "time",
        "date": "time",
        "timestamp": "time",
        "bid": "close",
        "last": "close",
        "price": "close",
        "tick_volume": "volume",
        "real_volume": "volume",
    }
    for old, new in rename.items():
        if old in out.columns and new not in out.columns:
            out = out.rename(columns={old: new})

    if "time" not in out.columns:
        out["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(out), freq="min")

    if "close" not in out.columns:
        nums = out.select_dtypes(include="number").columns.tolist()
        if nums:
            out["close"] = out[nums[-1]]
        else:
            return pd.DataFrame()

    for col in ["open", "high", "low"]:
        if col not in out.columns:
            out[col] = out["close"]
    if "volume" not in out.columns:
        out["volume"] = 0

    out["time"] = pd.to_datetime(out["time"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.dropna(subset=["time", "open", "high", "low", "close"])
    out = out.sort_values("time").drop_duplicates(subset=["time"], keep="last").reset_index(drop=True)
    return out[["time", "open", "high", "low", "close", "volume"]]


def _resample_h1(df):
    base = _normalize_local(df)
    if base.empty:
        return pd.DataFrame()
    try:
        out = (
            base.set_index("time")
            .resample("1h", label="right", closed="right")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna()
            .reset_index()
        )
        return _normalize_local(out)
    except Exception:
        return pd.DataFrame()


def _shared_market_df(tf="M1", bars=600):
    """Fallback data source: the dataframe already used by the normal Doo Prime/Home panel."""
    base = _normalize_local(st.session_state.get("last_df"))
    if base.empty:
        return pd.DataFrame()

    tf = str(tf or "M1").upper()
    if tf == "H1":
        df = _resample_h1(base)
        if df.empty:
            df = base.copy()
    else:
        df = base.copy()

    bars = _safe_int(bars, 600)
    if bars > 0:
        df = df.tail(bars).copy()
    return _normalize_local(df)


def _market_from_df(df):
    calc = _lazy_impl_func("_calc_market_analytics")
    if not callable(calc):
        return {}, pd.DataFrame()
    try:
        market, frame = calc(df)
        if market is None:
            market = {}
        if frame is None:
            frame = pd.DataFrame()
        return market, frame
    except Exception as exc:
        return {}, pd.DataFrame({"error": [str(exc)]})


def _quality_label(rows, requested, source):
    rows = _safe_int(rows, 0)
    requested = max(_safe_int(requested, 1), 1)
    ratio = rows / requested
    source_u = str(source or "").upper()
    if rows <= 0:
        return "NO DATA"
    if "SAFE_DEMO" in source_u:
        return "DEMO / NOT LIVE"
    if "CACHE" in source_u or "SHARED" in source_u:
        return "USABLE FALLBACK"
    if ratio >= 0.90:
        return "FULL"
    if ratio >= 0.20:
        return "PARTIAL BUT USABLE"
    return "LOW HISTORY"


def _fetch_m1_base(max_bars=DEEP_BASE_BARS):
    """One efficient connector fetch for the heavy dashboard.

    Older version made four separate network/MT5 calls. This version fetches one large M1 base,
    then derives M1 600 / M1 60k / H1 600 / H1 60k locally. That is faster and less likely to blank.
    """
    messages = []
    df = pd.DataFrame()
    source = ""

    try:
        df, ok, source, msg = manual_connect(
            mode=st.session_state.get("connector_mode", "fallback"),
            symbol=st.session_state.get("symbol", "XAUUSD"),
            api_key=st.session_state.get("twelve_api_key", ""),
            bars=int(max_bars),
            timeframe="M1",
            bridge_url=st.session_state.get("doo_bridge_url", ""),
            bridge_token=st.session_state.get("doo_bridge_token", ""),
        )
        df = _normalize_local(df)
        messages.append(f"{source}: {msg}")
    except Exception as exc:
        messages.append(f"Connector fetch failed safely: {exc}")
        source = "CONNECTOR_FAILED"

    if not df.empty:
        return df, source or "UNKNOWN", " | ".join(messages)

    fallback_df = _shared_market_df("M1", max_bars)
    if not fallback_df.empty:
        return fallback_df, "SHARED_DOO_DATA_FALLBACK", "Using already-loaded Doo Prime/shared dataframe. " + " | ".join(messages)

    return pd.DataFrame(), source or "NO_SOURCE", "No usable connector data and no shared Doo Prime dataframe found. " + " | ".join(messages)


def _build_result(key, tf, bars, label, df, source, message):
    df = _normalize_local(df)
    if bars:
        df = df.tail(int(bars)).copy()

    market, frame = _market_from_df(df)
    if df.empty or not market:
        return _empty_result(label, f"No usable analytics built for {label}. {message}")

    quality = _quality_label(len(df), bars, source)
    return {
        "label": label,
        "ok": True,
        "source": source or "UNKNOWN",
        "message": message,
        "rows": len(df),
        "timeframe": tf,
        "bars": int(bars),
        "market": market or {},
        "frame": frame if frame is not None else pd.DataFrame(),
        "fetched_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "partial": len(df) < int(bars),
        "quality": quality,
    }


def refresh_deep_doo_analysis(force=True):
    """Refresh all four blocks efficiently, then restore normal app connection state."""
    original = {
        "last_df": st.session_state.get("last_df"),
        "connected": st.session_state.get("connected", False),
        "source": st.session_state.get("source", "DISCONNECTED"),
        "last_fetch": st.session_state.get("last_fetch", 0),
        "timeframe": st.session_state.get("timeframe", "M1"),
        "connector_bars": st.session_state.get("connector_bars", 600),
    }

    results = {}
    progress = st.progress(0, text="Starting 10-minute Doo Prime deep refresh...")
    try:
        progress.progress(0.10, text="Fetching one efficient M1 base dataset...")
        base_m1, source, message = _fetch_m1_base(DEEP_BASE_BARS)
        progress.progress(0.50, text="Deriving H1 locally from the M1 base...")
        base_h1 = _resample_h1(base_m1)
        if base_h1.empty:
            base_h1 = _shared_market_df("H1", DEEP_BASE_BARS)

        bases = {"M1": base_m1, "H1": base_h1}
        for i, (key, tf, bars, label) in enumerate(DEEP_SPECS, start=1):
            progress.progress(0.50 + (i / len(DEEP_SPECS)) * 0.45, text=f"Building {label}...")
            base = bases.get(tf, pd.DataFrame())
            block_source = source if tf == "M1" else f"{source} → LOCAL_H1_RESAMPLE"
            block_message = message if tf == "M1" else message + " | H1 was derived locally to avoid repeated heavy connector calls."
            results[key] = _build_result(key, tf, bars, label, base, block_source, block_message)
    finally:
        for k, v in original.items():
            st.session_state[k] = v

    progress.progress(1.0, text="Deep analysis refreshed.")
    time.sleep(0.12)
    progress.empty()
    st.session_state.doo_deep_results = results
    st.session_state.doo_deep_last_refresh = time.time()
    return results


def _regime_score(m):
    if not m:
        return 0.0
    eff = _safe_num(m.get("directional_efficiency"))
    trust = _safe_num(m.get("trust"))
    ft = abs(_safe_num(m.get("fat_tail_z"))) if m.get("fat_tail_available", False) else 0.0
    accel = abs(_safe_num(m.get("accel_abs")))
    score = eff * 0.45 + trust * 0.35 + min(ft * 12, 36) * 0.12 + min(accel * 500, 20) * 0.08
    return max(0.0, min(100.0, score))


def _reliability_caption(res):
    q = str(res.get("quality", "UNKNOWN"))
    rows = _safe_int(res.get("rows", 0), 0)
    bars = _safe_int(res.get("bars", 0), 0)
    if q == "FULL":
        return f"🟢 {q}: {rows:,}/{bars:,} candles loaded."
    if q in ["PARTIAL BUT USABLE", "USABLE FALLBACK"]:
        return f"🟡 {q}: {rows:,}/{bars:,} candles. Read it, but give more weight to blocks with more rows."
    if q == "DEMO / NOT LIVE":
        return f"🔴 {q}: connector failed and demo data was used. Do not rely on this for real exit decisions."
    return f"⚪ {q}: {rows:,}/{bars:,} candles."


def _show_one_result(res):
    label = res.get("label", "Analysis")
    st.markdown(f"### {label}")
    st.caption(_reliability_caption(res))

    if not res.get("ok"):
        st.warning(res.get("message", "No data."))
    elif res.get("partial"):
        st.info(f"Using {res.get('rows', 0):,} available rows. Full {res.get('bars', 0):,} candles were not available, so this block stays usable instead of blanking.")

    st.caption(f"Source: {res.get('source','-')} | Last refresh: {res.get('fetched_at','not refreshed')}")
    if res.get("message"):
        with st.expander("Fetch / quality note", expanded=False):
            st.write(res.get("message"))

    m = res.get("market", {}) or {}
    if not m:
        st.info("No market analytics yet for this block.")
        return

    c = st.columns(6)
    c[0].metric("Price", round(_safe_num(m.get("price_now")), 5))
    c[1].metric("10s %", round(_safe_num(m.get("sec10_pct")), 4))
    c[2].metric("1m %", round(_safe_num(m.get("min1_pct")), 4))
    c[3].metric("10m %", round(_safe_num(m.get("min10_pct")), 4))
    c[4].metric("DVE %", round(_safe_num(m.get("directional_efficiency")), 2))
    c[5].metric("Trust", f"{round(_safe_num(m.get('trust')),1)}%")

    d = st.columns(5)
    for col, title, key, status_name in [
        (d[0], "Fat Tail Z", "fat_tail_z", "fat_tail_z"),
        (d[1], "Kurtosis", "kurtosis", "fat_tail_z"),
        (d[2], "Rising Eff %", "efficiency_rising", "efficiency_rising"),
        (d[3], "Falling Eff %", "efficiency_falling", "efficiency_falling"),
        (d[4], "Accel", "accel_abs", "price_accel_abs"),
    ]:
        val = _safe_num(m.get(key))
        if key == "fat_tail_z" and not m.get("fat_tail_available", False):
            col.metric(title, "N/A")
            col.caption(f"⚪ DATA CHECK: {m.get('fat_tail_note', 'Fat-tail is not reliable yet.')}")
            continue
        s, note = _analytics_status(status_name, abs(val) if "accel" in key else val)
        col.metric(title, round(val, 3))
        col.caption(f"{_status_badge(s)} {s}: {note}")

    regime = m.get("regime", "UNKNOWN")
    direction = m.get("trend_direction", "UNKNOWN")
    score = round(_regime_score(m), 1)
    if any(x in str(regime) for x in ["LIMIT", "EXHAUSTION", "STOPPING", "SHOCK"]):
        st.warning(f"Important: {regime} | Direction: {direction} | Score: {score}")
    elif any(x in str(regime) for x in ["STARTING", "CONTINUING", "CONTINUES"]):
        st.success(f"Important: {regime} | Direction: {direction} | Score: {score}")
    else:
        st.info(f"Regime: {regime} | Direction: {direction} | Score: {score}")


def _combined_view(results):
    rows = []
    for key, res in (results or {}).items():
        m = res.get("market", {}) or {}
        rows.append({
            "Block": res.get("label", key),
            "Quality": res.get("quality", "UNKNOWN"),
            "Source": res.get("source", "-"),
            "Rows": res.get("rows", 0),
            "Direction": m.get("trend_direction", "WAIT"),
            "Regime": m.get("regime", "NO DATA"),
            "DVE %": round(_safe_num(m.get("directional_efficiency")), 2),
            "Rising Eff %": round(_safe_num(m.get("efficiency_rising")), 2),
            "Falling Eff %": round(_safe_num(m.get("efficiency_falling")), 2),
            "Fat Tail Z": round(_safe_num(m.get("fat_tail_z")), 2) if m.get("fat_tail_available", False) else "N/A",
            "Trust %": round(_safe_num(m.get("trust")), 2),
            "Combined Score": round(_regime_score(m), 2),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        st.info("Refresh first to create combined analysis.")
        return
    with st.expander("📊 Open deep-analysis metric table", expanded=False):
        st.dataframe(out, use_container_width=True, hide_index=True)

    buy_votes = int((out["Direction"].astype(str).str.upper().isin(["BUY", "UP"])).sum())
    sell_votes = int((out["Direction"].astype(str).str.upper().isin(["SELL", "DOWN"])).sum())
    avg_score = float(out["Combined Score"].mean())
    avg_dve = float(out["DVE %"].mean())
    avg_trust = float(out["Trust %"].mean())
    tail_numeric = pd.to_numeric(out["Fat Tail Z"], errors="coerce")
    max_tail = float(tail_numeric.abs().max()) if tail_numeric.notna().any() else 0.0
    demo_count = int(out["Quality"].astype(str).str.contains("DEMO", case=False, na=False).sum())

    cols = st.columns(6)
    cols[0].metric("BUY/UP Votes", buy_votes)
    cols[1].metric("SELL/DOWN Votes", sell_votes)
    cols[2].metric("Avg Score", round(avg_score, 1))
    cols[3].metric("Avg DVE", round(avg_dve, 1))
    cols[4].metric("Avg Trust", round(avg_trust, 1))
    cols[5].metric("Max Fat Tail", round(max_tail, 2))

    if demo_count:
        st.error("Reliability warning: one or more blocks are using demo data. Do not use those blocks for real exit timing.")
    elif max_tail >= 3:
        st.error("Combined warning: fat-tail shock is extreme. Avoid blind one-side chasing; protect margin first.")
    elif avg_dve >= 65 and avg_score >= 60 and avg_trust >= 55 and buy_votes > sell_votes:
        st.success("Combined read: BUY/UP pressure is strong across multiple views.")
    elif avg_dve >= 65 and avg_score >= 60 and avg_trust >= 55 and sell_votes > buy_votes:
        st.success("Combined read: SELL/DOWN pressure is strong across multiple views.")
    elif avg_dve >= 75 and avg_score < 55:
        st.warning("Combined read: movement may be near one-way limit/exhaustion. Watch falling efficiency and margin level.")
    else:
        st.info("Combined read: mixed or normal movement. Wait for cleaner DVE + trust alignment before relying on one direction.")

    st.markdown("#### Practical reading rule")
    st.write(
        "Prioritize blocks in this order: FULL quality first, then PARTIAL/USABLE FALLBACK. "
        "Ignore DEMO blocks for real money decisions. For danger exits, rising Falling Eff %, fat-tail above 2, "
        "and trust dropping below 50 are more important than direction alone."
    )


def _auto_seed_from_shared_if_needed():
    """Build instant panels from shared Doo dataframe before the user presses refresh."""
    if st.session_state.get("doo_deep_results"):
        return
    base = _shared_market_df("M1", DEEP_BASE_BARS)
    if base.empty:
        return
    h1 = _resample_h1(base)
    if h1.empty:
        h1 = _shared_market_df("H1", DEEP_BASE_BARS)
    bases = {"M1": base, "H1": h1}
    results = {}
    for key, tf, bars, label in DEEP_SPECS:
        df = bases.get(tf, pd.DataFrame()).tail(int(bars)).copy()
        results[key] = _build_result(
            key,
            tf,
            bars,
            label,
            df,
            "SHARED_DOO_DATA_INSTANT" if tf == "M1" else "SHARED_DOO_DATA_INSTANT → LOCAL_H1_RESAMPLE",
            "Instant fallback from the already-working Doo Prime dataframe. Press Refresh All 4 Now for a fresh connector attempt.",
        )
    st.session_state.doo_deep_results = results
    st.session_state.doo_deep_last_refresh = time.time()


def doo_prime_deep_analysis_panel():
    st.markdown("## ⚡ Doo Prime Analysis — 4‑Frame Deep Dashboard")
    st.caption("Fast mode: only the selected deep frame renders. Combined view opens only when selected.")

    try:
        st_autorefresh(interval=AUTO_REFRESH_SECONDS * 1000, key="doo_deep_ten_min_page_refresh")
    except Exception:
        pass

    _auto_seed_from_shared_if_needed()

    with st.expander("🔄 Open deep-analysis refresh controls", expanded=False):
        top = st.columns([1, 1, 2])
        with top[0]:
            if st.button("🔄 Refresh All 4 Now", use_container_width=True, key="doo_deep_refresh_all"):
                refresh_deep_doo_analysis(force=True)
        with top[1]:
            st.toggle("10‑min auto fetch", value=bool(st.session_state.get("doo_deep_auto_fetch", True)), key="doo_deep_auto_fetch")
        with top[2]:
            last = float(st.session_state.get("doo_deep_last_refresh", 0) or 0)
            if last:
                elapsed = max(0, int(time.time() - last))
                next_in = max(0, AUTO_REFRESH_SECONDS - elapsed)
                st.caption(f"Last deep refresh: {pd.Timestamp.fromtimestamp(last).strftime('%Y-%m-%d %H:%M:%S')} | next auto fetch in ~{next_in // 60}m {next_in % 60}s")
            else:
                st.caption("No deep refresh yet. It will seed from shared data first, then auto-fetch every 10 minutes.")

    if st.session_state.get("doo_deep_auto_fetch", True):
        last = float(st.session_state.get("doo_deep_last_refresh", 0) or 0)
        if time.time() - last >= AUTO_REFRESH_SECONDS:
            refresh_deep_doo_analysis(force=True)

    results = st.session_state.get("doo_deep_results", {})
    if not results:
        st.info("Connect/read Doo Prime, MT5, TwelveData, or Doo Bridge once first. Then this panel will reuse that same dataframe instead of staying blank.")
        return

    choice = st.radio(
        "Open deep-analysis frame",
        ["M1 600", "M1 60,000", "H1 600", "H1 60,000", "Combined"],
        horizontal=True,
        key="doo_deep_lazy_frame",
    )
    mapping = {"M1 600": "m1_600", "M1 60,000": "m1_60000", "H1 600": "h1_600", "H1 60,000": "h1_60000"}
    if choice == "Combined":
        _combined_view(results)
    else:
        key = mapping.get(choice, "m1_600")
        _show_one_result(results.get(key, _empty_result(key, "Not refreshed.")))

