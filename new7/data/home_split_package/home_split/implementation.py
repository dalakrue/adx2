import streamlit as st
import pandas as pd
import numpy as np

# ==========================================================
# SAFE IMPORTS
# ==========================================================

try:
    from core.common import DEFAULT_TABS, log_event
except Exception:
    DEFAULT_TABS = ["home", "engine", "backtest", "guide", "account"]

    def log_event(*args, **kwargs):
        return None

try:
    from core.styles import request_close_sidebar
except Exception:
    def request_close_sidebar(*args, **kwargs):
        return None

try:
    from core.data_connectors import manual_connect, mt5_account_info
except Exception:
    manual_connect = None
    mt5_account_info = None

try:
    from core.quant_models import quant_stack
except Exception:
    quant_stack = None

try:
    from core.database import append_csv, read_csv
except Exception:
    append_csv = None
    read_csv = None


# ==========================================================
# SAFE HELPERS
# ==========================================================

def _safe_num(v, default=0.0):
    try:
        if v is None:
            return default
        if isinstance(v, str) and v.strip() == "":
            return default
        v = float(v)
        if not np.isfinite(v):
            return default
        return v
    except Exception:
        return default


def _safe_int(v, default=0):
    try:
        if v is None:
            return default
        return int(v)
    except Exception:
        return default


def _safe_text(v, default=""):
    try:
        if v is None:
            return default
        return str(v)
    except Exception:
        return default


def _safe_append_csv(name, row):
    if append_csv is None:
        return False, "append_csv is unavailable."

    try:
        append_csv(name, row)
        return True, "Saved."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def _safe_read_csv(name):
    if read_csv is None:
        return pd.DataFrame()

    try:
        df = read_csv(name)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _safe_log_event(message):
    try:
        log_event(message)
    except Exception:
        pass


def _safe_close_sidebar():
    try:
        request_close_sidebar()
    except Exception:
        pass


def _normalize_account_info(raw):
    """
    Accepts different possible MT5 connector outputs and returns one safe dict.

    Supported:
    - dict account snapshot
    - tuple: info, ok, msg
    - tuple: ok, info, msg
    """
    if raw is None:
        return {}, False, "No MT5 account data returned."

    if isinstance(raw, tuple):
        if len(raw) >= 3:
            a, b, c = raw[0], raw[1], raw[2]

            if isinstance(a, dict):
                return a, bool(b), _safe_text(c, "MT5 account read finished.")

            if isinstance(b, dict):
                return b, bool(a), _safe_text(c, "MT5 account read finished.")

        if len(raw) >= 1 and isinstance(raw[0], dict):
            return raw[0], True, "MT5 account read finished."

    if isinstance(raw, dict):
        ok = bool(raw.get("ok", True))
        msg = raw.get("message", "MT5 account read finished.")
        return raw, ok, msg

    return {}, False, "Unsupported MT5 account response format."


def _safe_mt5_account_info():
    if mt5_account_info is None:
        return {}, False, "mt5_account_info is unavailable. Check core.data_connectors."

    try:
        raw = mt5_account_info()
        info, ok, msg = _normalize_account_info(raw)
        return info, ok, msg
    except Exception as exc:
        return {}, False, f"MT5 account reader crashed safely: {exc}"


def _safe_manual_connect(source, symbol, api_key="", bars=5000, timeframe="M1"):
    if manual_connect is None:
        st.error("manual_connect is unavailable. Check core.data_connectors import.")
        return

    try:
        with st.spinner(f"Connecting {source.upper()} {symbol} {timeframe}..."):
            manual_connect(
                source,
                symbol,
                api_key,
                bars=bars,
                timeframe=timeframe,
            )

        st.success(f"Connected: {source.upper()} {symbol} {timeframe}")
        _safe_rerun()

    except Exception as exc:
        st.error(f"{source.upper()} connection failed safely: {exc}")


def _safe_quant_stack(df):
    if df is None:
        return {
            "bias": "WAIT",
            "scale10": 0,
            "safe_pct": 0,
        }

    if quant_stack is None:
        return {
            "bias": "WAIT",
            "scale10": 0,
            "safe_pct": 0,
            "message": "quant_stack unavailable",
        }

    try:
        q = quant_stack(
            df,
            st.session_state.get("trade_history", []),
            st.session_state.get("account_snapshot", {}),
        )

        if not isinstance(q, dict):
            return {
                "bias": "WAIT",
                "scale10": 0,
                "safe_pct": 0,
                "message": "quant_stack returned invalid output",
            }

        q.setdefault("bias", "WAIT")
        q.setdefault("scale10", 0)
        q.setdefault("safe_pct", 0)

        return q

    except Exception as exc:
        return {
            "bias": "WAIT",
            "scale10": 0,
            "safe_pct": 0,
            "message": f"quant_stack crashed safely: {exc}",
        }


def _save_once_per_60_seconds(name, row, state_key):
    """
    Prevent duplicate CSV spam on every Streamlit rerun.
    """
    now = pd.Timestamp.now()
    last_time = st.session_state.get(state_key)

    should_save = False

    if last_time is None:
        should_save = True
    else:
        try:
            elapsed = (now - pd.to_datetime(last_time)).total_seconds()
            should_save = elapsed >= 60
        except Exception:
            should_save = True

    if should_save:
        ok, msg = _safe_append_csv(name, row)
        if ok:
            st.session_state[state_key] = now
        return ok, msg

    return True, "Skipped duplicate auto-save."


# ==========================================================
# RISK STATUS
# ==========================================================

def _risk_status(label, value):
    v = _safe_num(value)
    label = str(label).lower()

    if label == "margin_level":
        if v <= 0:
            return "UNKNOWN", "No margin level from MT5 yet"
        if v >= 500:
            return "VERY GOOD", "Large margin buffer"
        if v >= 250:
            return "GOOD", "Healthy margin buffer"
        if v >= 150:
            return "BAD", "Margin getting tight"
        return "DANGEROUS", "Margin call danger zone"

    if label == "drawdown":
        if v <= 3:
            return "VERY GOOD", "Very low drawdown"
        if v <= 8:
            return "GOOD", "Normal drawdown"
        if v <= 15:
            return "BAD", "Reduce risk"
        return "DANGEROUS", "High drawdown"

    if label == "margin_used_pct":
        if v <= 15:
            return "VERY GOOD", "Low margin usage"
        if v <= 35:
            return "GOOD", "Manageable usage"
        if v <= 60:
            return "BAD", "High usage"
        return "DANGEROUS", "Too much margin used"

    if label == "floating_pl":
        if v >= 0:
            return "GOOD", "Floating profit"
        return "BAD", "Floating loss; check exposure"

    if label == "free_margin_pct":
        if v >= 75:
            return "VERY GOOD", "Large free margin buffer"
        if v >= 50:
            return "GOOD", "Healthy free margin"
        if v >= 25:
            return "BAD", "Free margin getting low"
        return "DANGEROUS", "Free margin danger zone"

    if label == "open_positions":
        if v <= 3:
            return "VERY GOOD", "Low exposure count"
        if v <= 7:
            return "GOOD", "Manageable exposure count"
        if v <= 12:
            return "BAD", "Many open positions"
        return "DANGEROUS", "Too many open positions"

    return "GOOD", "Normal"


def _metric_status(col, label, value, status_key=None):
    status, note = _risk_status(status_key or str(label).lower(), value)
    col.metric(label, value)
    col.caption(f"{status}: {note}")


# ==========================================================
# POSITION PROCESSING
# ==========================================================

def _position_to_dict(pos):
    if isinstance(pos, dict):
        return pos

    if hasattr(pos, "_asdict"):
        try:
            return pos._asdict()
        except Exception:
            pass

    try:
        return dict(pos)
    except Exception:
        pass

    out = {}

    for key in dir(pos):
        if key.startswith("_"):
            continue

        try:
            value = getattr(pos, key)
            if not callable(value):
                out[key] = value
        except Exception:
            pass

    return out


def _guess_pip_size(symbol, price=None):
    symbol = str(symbol or "").upper()
    price = _safe_num(price)

    if "JPY" in symbol:
        return 0.01

    if "XAU" in symbol or "GOLD" in symbol:
        return 0.1

    if "XAG" in symbol or "SILVER" in symbol:
        return 0.01

    if "BTC" in symbol or "ETH" in symbol:
        return 1.0

    if price >= 100:
        return 0.01

    return 0.0001


def _calc_pips(row):
    price_open = _safe_num(row.get("price_open"))
    price_current = _safe_num(row.get("price_current"))
    symbol = row.get("symbol", "")
    side = str(row.get("side", "")).upper()

    if price_open <= 0 or price_current <= 0:
        return 0.0

    pip_size = _guess_pip_size(symbol, price_open)

    if side == "SELL":
        pips = (price_open - price_current) / pip_size
    else:
        pips = (price_current - price_open) / pip_size

    return round(pips, 1)


def _positions_frame(info):
    positions = info.get("positions", []) if isinstance(info, dict) else []

    if not positions:
        return pd.DataFrame()

    rows = [_position_to_dict(p) for p in positions]

    try:
        df = pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    if "time" in df.columns:
        df["open_time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")

    if "time_update" in df.columns:
        df["update_time"] = pd.to_datetime(df["time_update"], unit="s", errors="coerce")

    for c in ["profit", "volume", "price_open", "price_current", "swap", "commission"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    if "type" in df.columns:
        df["side"] = df["type"].map({0: "BUY", 1: "SELL"}).fillna(df["type"].astype(str))
    elif "side" not in df.columns:
        df["side"] = "UNKNOWN"

    if "open_time" in df.columns:
        now = pd.Timestamp.now()
        df["hold_minutes"] = (now - df["open_time"]).dt.total_seconds() / 60
        df["hold_hours"] = (df["hold_minutes"] / 60).round(2)

    if "price_open" in df.columns and "price_current" in df.columns:
        df["pips"] = df.apply(_calc_pips, axis=1)

    if "profit" in df.columns and "volume" in df.columns:
        df["profit_per_0.01"] = df.apply(
            lambda r: round(_safe_num(r.get("profit")) / max(_safe_num(r.get("volume")), 0.01) * 0.01, 2),
            axis=1,
        )

    return df


# ==========================================================
# DOO PRIME ACCOUNT PANEL
# ==========================================================

def doo_prime_account_panel():
    st.markdown("### 🏦 Doo Prime / MT5 Account Reader")

    st.caption(
        "Reads real local MT5/Doo Prime data when MetaTrader 5 is open and logged in. "
        "On Streamlit Cloud it safely shows MT5 unavailable instead of crashing."
    )

    c0, c1, c2 = st.columns(3)

    with c0:
        if st.button("🔍 Read Real Doo Prime MT5 Account", use_container_width=True, key="home_doo_read"):
            info, ok, msg = _safe_mt5_account_info()
            st.session_state.account_snapshot = info

            if ok:
                st.success(msg)
            else:
                st.warning(msg)

    with c1:
        if st.button("💾 Save Account Snapshot", use_container_width=True, key="home_doo_store"):
            info = st.session_state.get("account_snapshot", {})

            if not info:
                st.warning("No account snapshot to save yet.")
            else:
                positions = info.get("positions", []) or []

                ok, msg = _safe_append_csv(
                    "doo_prime_account_history",
                    {
                        "time": pd.Timestamp.now(),
                        "balance": _safe_num(info.get("balance")),
                        "equity": _safe_num(info.get("equity")),
                        "margin": _safe_num(info.get("margin")),
                        "margin_free": _safe_num(info.get("margin_free")),
                        "margin_level": _safe_num(info.get("margin_level")),
                        "profit": _safe_num(info.get("profit")),
                        "positions": len(positions),
                    },
                )

                if ok:
                    st.success("Account snapshot saved.")
                else:
                    st.error(msg)

    with c2:
        if st.button("🧹 Clear Screen Snapshot", use_container_width=True, key="home_doo_clear"):
            st.session_state.account_snapshot = {}
            _safe_rerun()

    info = st.session_state.get("account_snapshot", {})

    if not info:
        st.info("Open your local Doo Prime MetaTrader 5, login, then click Read Real Doo Prime MT5 Account.")
        return

    balance = _safe_num(info.get("balance"))
    equity = _safe_num(info.get("equity"), balance)
    margin = _safe_num(info.get("margin"))
    free = _safe_num(info.get("margin_free"))
    margin_level = _safe_num(info.get("margin_level"))
    floating = _safe_num(info.get("profit"), equity - balance)

    drawdown = max(0.0, (balance - equity) / max(balance, 1e-9) * 100.0)
    margin_used_pct = margin / max(equity, 1e-9) * 100.0 if equity else 0.0
    free_pct = free / max(equity, 1e-9) * 100.0 if equity else 0.0

    positions_df = _positions_frame(info)

    st.markdown("#### Real Account Stats")

    row1 = st.columns(6)

    _metric_status(row1[0], "Balance", round(balance, 2))
    _metric_status(row1[1], "Equity", round(equity, 2))
    _metric_status(row1[2], "Floating P/L", round(floating, 2), "floating_pl")
    _metric_status(row1[3], "Margin Used %", round(margin_used_pct, 2), "margin_used_pct")
    _metric_status(row1[4], "Free Margin %", round(free_pct, 2), "free_margin_pct")
    _metric_status(row1[5], "Margin Level %", round(margin_level, 2), "margin_level")

    row2 = st.columns(6)

    open_count = len(positions_df)

    buy_count = int((positions_df.get("side", pd.Series(dtype=str)) == "BUY").sum()) if not positions_df.empty else 0
    sell_count = int((positions_df.get("side", pd.Series(dtype=str)) == "SELL").sum()) if not positions_df.empty else 0

    total_lots = float(positions_df["volume"].sum()) if "volume" in positions_df.columns else 0.0
    worst = float(positions_df["profit"].min()) if "profit" in positions_df.columns and len(positions_df) else 0.0
    best = float(positions_df["profit"].max()) if "profit" in positions_df.columns and len(positions_df) else 0.0

    _metric_status(row2[0], "Open Positions", open_count, "open_positions")
    _metric_status(row2[1], "BUY Count", buy_count)
    _metric_status(row2[2], "SELL Count", sell_count)
    _metric_status(row2[3], "Total Lots", round(total_lots, 2))
    _metric_status(row2[4], "Worst Position", round(worst, 2), "floating_pl")
    _metric_status(row2[5], "Drawdown %", round(drawdown, 2), "drawdown")

    st.markdown("#### Account Risk Status")

    risk_table = pd.DataFrame(
        [
            {
                "Risk Data": "Margin Level",
                "Value": round(margin_level, 2),
                "Status": _risk_status("margin_level", margin_level)[0],
                "Meaning": _risk_status("margin_level", margin_level)[1],
            },
            {
                "Risk Data": "Drawdown %",
                "Value": round(drawdown, 2),
                "Status": _risk_status("drawdown", drawdown)[0],
                "Meaning": _risk_status("drawdown", drawdown)[1],
            },
            {
                "Risk Data": "Margin Used %",
                "Value": round(margin_used_pct, 2),
                "Status": _risk_status("margin_used_pct", margin_used_pct)[0],
                "Meaning": _risk_status("margin_used_pct", margin_used_pct)[1],
            },
            {
                "Risk Data": "Free Margin %",
                "Value": round(free_pct, 2),
                "Status": _risk_status("free_margin_pct", free_pct)[0],
                "Meaning": _risk_status("free_margin_pct", free_pct)[1],
            },
            {
                "Risk Data": "Floating P/L",
                "Value": round(floating, 2),
                "Status": _risk_status("floating_pl", floating)[0],
                "Meaning": _risk_status("floating_pl", floating)[1],
            },
        ]
    )

    st.dataframe(risk_table, use_container_width=True, hide_index=True)

    st.markdown("#### Stop-Out / Blow-Out Proxy")

    stopout_level = st.number_input(
        "Broker stop-out level % proxy",
        min_value=1.0,
        max_value=500.0,
        value=50.0,
        step=5.0,
        key="doo_stopout_level",
        help="This is only a proxy. Real stop-out depends on broker rules, leverage, spread, commission, swap, and symbol margin.",
    )

    if margin > 0:
        estimated_stopout_equity = margin * stopout_level / 100.0
        loss_room = equity - estimated_stopout_equity

        b1, b2, b3 = st.columns(3)
        b1.metric("Estimated Stop-Out Equity", round(estimated_stopout_equity, 2))
        b2.metric("Approx Loss Room", round(loss_room, 2))
        b3.metric("Loss Room % of Equity", round(loss_room / max(equity, 1e-9) * 100.0, 2))

        if loss_room <= 0:
            st.error("Danger: equity is near or below this stop-out proxy.")
        elif loss_room < equity * 0.10:
            st.warning("Warning: small loss room remains by this proxy.")
        else:
            st.success("Loss room exists by this proxy.")
    else:
        st.info("No used margin detected, so stop-out proxy is inactive.")

    if not positions_df.empty:
        st.markdown("#### Open Positions")

        display_cols = [
            c for c in [
                "ticket",
                "symbol",
                "side",
                "volume",
                "price_open",
                "price_current",
                "pips",
                "profit",
                "profit_per_0.01",
                "swap",
                "commission",
                "hold_hours",
                "open_time",
            ]
            if c in positions_df.columns
        ]

        st.dataframe(positions_df[display_cols], use_container_width=True, height=300)

        csv = positions_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Open Positions CSV",
            data=csv,
            file_name=f"doo_prime_positions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if "symbol" in positions_df.columns:
            st.markdown("#### Symbol Exposure")

            if "side" in positions_df.columns:
                expo = (
                    positions_df.groupby(["symbol", "side"], dropna=False)
                    .agg(
                        volume=("volume", "sum"),
                        profit=("profit", "sum"),
                        positions=("symbol", "count"),
                    )
                    .reset_index()
                )
            else:
                expo = (
                    positions_df.groupby("symbol")
                    .agg(
                        volume=("volume", "sum"),
                        profit=("profit", "sum"),
                        positions=("symbol", "count"),
                    )
                    .reset_index()
                )

            for col in ["volume", "profit"]:
                if col in expo.columns:
                    expo[col] = pd.to_numeric(expo[col], errors="coerce").round(2)

            st.dataframe(expo, use_container_width=True, hide_index=True)

    else:
        st.info("No open positions returned from MT5.")

    st.markdown("#### Lot / Risk Helper")

    h1, h2, h3 = st.columns(3)

    with h1:
        lot = st.number_input(
            "Lot size to check",
            min_value=0.01,
            value=0.01,
            step=0.01,
            key="doo_lot_calc",
        )

    with h2:
        margin_per_001 = st.number_input(
            "Margin needed per 0.01 lot",
            min_value=1.0,
            value=150.0,
            step=10.0,
            key="doo_margin_per_001",
        )

    with h3:
        planned_entries = st.number_input(
            "Planned entries",
            min_value=1,
            value=1,
            step=1,
            key="doo_planned_entries",
        )

    need = margin_per_001 * (lot / 0.01) * planned_entries
    possible = int(free / (margin_per_001 * (lot / 0.01))) if lot and margin_per_001 else 0
    after_plan_free = free - need

    z = st.columns(3)
    z[0].metric("Margin Needed", round(need, 2))
    z[1].metric("Possible Entries", possible)
    z[2].metric("After-Plan Free Margin", round(after_plan_free, 2))

    if after_plan_free < 0:
        st.error("Planned entries need more margin than current free margin.")
    elif after_plan_free < free * 0.25:
        st.warning("Plan leaves low free margin. Consider smaller lot or fewer entries.")
    else:
        st.success("Plan is acceptable by this margin helper.")


# ==========================================================
# RISK PANEL
# ==========================================================

def risk_panel():
    st.markdown("### 🛡️ Risk Inner Tab — under Doo Prime only")

    acct = st.session_state.get("account_snapshot", {})

    balance = _safe_num(acct.get("balance"), 1000.0)
    equity = _safe_num(acct.get("equity"), balance)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        manual_balance = st.number_input(
            "Manual balance if no Doo data",
            value=float(balance),
            key="risk_manual_balance",
        )

    with c2:
        manual_equity = st.number_input(
            "Manual equity if no Doo data",
            value=float(equity),
            key="risk_manual_equity",
        )

    with c3:
        risk_pct = st.slider(
            "Risk per trade %",
            0.1,
            10.0,
            1.0,
            0.1,
            key="risk_pct_inner",
        )

    with c4:
        max_daily_loss_pct = st.slider(
            "Max daily loss %",
            1.0,
            25.0,
            5.0,
            0.5,
            key="risk_daily_loss_pct",
        )

    s1, s2, s3 = st.columns(3)

    with s1:
        sl_pips = st.number_input(
            "Stop loss pips",
            min_value=1.0,
            value=50.0,
            key="risk_sl_pips",
        )

    with s2:
        pip_value = st.number_input(
            "Pip value per 0.01 lot",
            min_value=0.01,
            value=1.0,
            key="risk_pip_value",
        )

    with s3:
        planned_trades = st.number_input(
            "Planned trades today",
            min_value=1,
            value=3,
            step=1,
            key="risk_planned_trades_today",
        )

    risk_money = manual_equity * risk_pct / 100.0
    lot_001_units = max(0.0, risk_money / max(sl_pips * pip_value, 1e-9))
    max_daily_loss = manual_equity * max_daily_loss_pct / 100.0
    drawdown = max(0.0, (manual_balance - manual_equity) / max(manual_balance, 1e-9) * 100.0)

    trades_to_daily_stop = int(max_daily_loss / max(risk_money, 1e-9))
    planned_total_risk = risk_money * planned_trades

    row = st.columns(6)

    row[0].metric("Risk $ / Trade", round(risk_money, 2))
    row[1].metric("Suggested 0.01-lot Units", round(lot_001_units, 2))
    row[2].metric("Suggested Lot", round(lot_001_units * 0.01, 2))
    row[3].metric("Max Daily Loss $", round(max_daily_loss, 2))
    row[4].metric("Current Drawdown %", round(drawdown, 2))
    row[5].metric("Trades to Daily Stop", trades_to_daily_stop)

    st.markdown("#### Planned Day Risk")

    p1, p2, p3 = st.columns(3)

    p1.metric("Planned Total Risk", round(planned_total_risk, 2))
    p2.metric("Planned Risk % of Equity", round(planned_total_risk / max(manual_equity, 1e-9) * 100.0, 2))
    p3.metric("Remaining Daily Risk Room", round(max_daily_loss - planned_total_risk, 2))

    if planned_total_risk > max_daily_loss:
        st.error("Planned trades exceed your max daily loss rule.")
    elif planned_total_risk > max_daily_loss * 0.7:
        st.warning("Planned trades use more than 70% of daily risk room.")
    else:
        st.success("Planned trades are inside your daily risk rule.")

    risk_table = pd.DataFrame(
        [
            {
                "Risk Item": "Risk per trade",
                "Value": round(risk_pct, 2),
                "Status": "GOOD" if risk_pct <= 2 else "BAD" if risk_pct <= 5 else "DANGEROUS",
                "Meaning": "Lower risk gives more survival time.",
            },
            {
                "Risk Item": "Drawdown %",
                "Value": round(drawdown, 2),
                "Status": _risk_status("drawdown", drawdown)[0],
                "Meaning": _risk_status("drawdown", drawdown)[1],
            },
            {
                "Risk Item": "Planned total risk",
                "Value": round(planned_total_risk, 2),
                "Status": "GOOD" if planned_total_risk <= max_daily_loss else "DANGEROUS",
                "Meaning": "Must stay below daily max loss.",
            },
        ]
    )

    st.dataframe(risk_table, use_container_width=True, hide_index=True)

    if st.button("💾 Save Risk Snapshot", use_container_width=True, key="risk_save_snapshot"):
        ok, msg = _safe_append_csv(
            "risk_snapshots",
            {
                "time": pd.Timestamp.now(),
                "balance": manual_balance,
                "equity": manual_equity,
                "risk_pct": risk_pct,
                "risk_money": risk_money,
                "sl_pips": sl_pips,
                "pip_value_per_001": pip_value,
                "lot_001_units": lot_001_units,
                "suggested_lot": lot_001_units * 0.01,
                "max_daily_loss_pct": max_daily_loss_pct,
                "max_daily_loss": max_daily_loss,
                "drawdown_pct": drawdown,
                "planned_trades": planned_trades,
                "planned_total_risk": planned_total_risk,
            },
        )

        if ok:
            st.success("Risk snapshot saved. It will not duplicate automatically on every refresh.")
        else:
            st.error(msg)


# ==========================================================
# DOO PRIME PANEL
# ==========================================================

def doo_prime_panel():
    st.markdown("### 🏦 Doo Prime — Account + Risk")

    st.caption("Duplicate Risk tab removed from sidebar. Risk is only here under Doo Prime.")

    doo_tabs = st.tabs(["🏦 Real Account Stats", "🛡️ Risk Calculator", "📜 Risk / Account History"])

    with doo_tabs[0]:
        doo_prime_account_panel()

    with doo_tabs[1]:
        risk_panel()

    with doo_tabs[2]:
        h1, h2 = st.tabs(["Risk Snapshots", "Doo Prime Account History"])

        with h1:
            risk_hist = _safe_read_csv("risk_snapshots")

            if risk_hist.empty:
                st.info("No risk snapshots yet. Save one from Risk Calculator.")
            else:
                st.dataframe(risk_hist.drop_duplicates().tail(300), use_container_width=True)

        with h2:
            acct_hist = _safe_read_csv("doo_prime_account_history")

            if acct_hist.empty:
                st.info("No Doo Prime account history yet. Save one from Real Account Stats.")
            else:
                acct_hist = acct_hist.drop_duplicates().tail(300)
                st.dataframe(acct_hist, use_container_width=True)

                chart_cols = [c for c in ["balance", "equity", "margin_free"] if c in acct_hist.columns]

                if chart_cols and "time" in acct_hist.columns:
                    chart_df = acct_hist.copy()
                    chart_df["time"] = pd.to_datetime(chart_df.get("time"), errors="coerce")
                    chart_df = chart_df.dropna(subset=["time"])

                    if not chart_df.empty:
                        st.line_chart(chart_df.set_index("time")[chart_cols])


# ==========================================================
# HOME SHOW
# ==========================================================

def show():
    st.markdown("# 🏠 Home — Start Page")

    st.caption("Launcher, connection buttons, and upgraded Doo Prime account/risk stats are combined here.")

    home_tabs = st.tabs(["🏠 Launcher", "🏦 Doo Prime"])

    with home_tabs[0]:
        home_symbol = st.text_input(
            "Symbol space / other symbol possible",
            value=st.session_state.get("symbol", "XAUUSD"),
            key="home_symbol",
            help="Auto-filled XAUUSD, but you can type EURUSD, GBPUSD, BTCUSD if supported.",
        )

        st.session_state.symbol = str(home_symbol or "XAUUSD").upper().strip()

        grid = st.columns(4)

        safe_tabs = DEFAULT_TABS if DEFAULT_TABS else ["home", "engine", "backtest", "guide", "account"]

        for i, tab in enumerate(safe_tabs):
            with grid[i % 4]:
                if st.button(f"Open {tab}", use_container_width=True, key=f"home_open_{tab}"):
                    st.session_state.tab_choice = tab
                    _safe_log_event(f"Home open: {tab}")
                    _safe_close_sidebar()
                    _safe_rerun()

        st.markdown("---")

        api_key = st.text_input(
            "Twelve Data API key",
            value=st.session_state.get("twelve_api_key", ""),
            type="password",
            key="home_twelve_api_key",
        )

        st.session_state.twelve_api_key = api_key

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("MT5 M1", use_container_width=True, key="home_mt5_only"):
                _safe_manual_connect(
                    "mt5",
                    st.session_state.symbol,
                    st.session_state.twelve_api_key,
                    bars=5000,
                    timeframe="M1",
                )

        with c2:
            if st.button("MT5 M2 100D", use_container_width=True, key="home_mt5_m2"):
                _safe_manual_connect(
                    "mt5",
                    st.session_state.symbol,
                    st.session_state.twelve_api_key,
                    bars=80000,
                    timeframe="M2",
                )

        with c3:
            if st.button("Twelve Only", use_container_width=True, key="home_twelve_only"):
                _safe_manual_connect(
                    "twelve",
                    st.session_state.symbol,
                    st.session_state.twelve_api_key,
                    bars=5000,
                    timeframe="M1",
                )

        with c4:
            if st.button("Disconnect", use_container_width=True, key="home_disconnect"):
                st.session_state.connected = False
                st.session_state.source = "DISCONNECTED"
                st.session_state.last_df = None
                st.success("Disconnected.")
                _safe_rerun()

        st.metric("Current Source", st.session_state.get("source", "DISCONNECTED"))

        df = st.session_state.get("last_df")

        if df is not None:
            q = _safe_quant_stack(df)

            m = st.columns(4)

            m[0].metric("Safe 12H Bias", q.get("bias", "WAIT"))
            m[1].metric("Safety /10", q.get("scale10", 0))
            m[2].metric("Safety %", q.get("safe_pct", 0))
            m[3].metric("Symbol", st.session_state.symbol)

            with st.expander("Home quant detail"):
                st.json(q)

            auto_save_home = st.checkbox(
                "Auto-save home snapshot safely every 60 seconds",
                value=False,
                key="home_auto_save_snapshot",
            )

            if auto_save_home:
                _save_once_per_60_seconds(
                    "home_snapshots",
                    {
                        "time": pd.Timestamp.now(),
                        "symbol": st.session_state.symbol,
                        **q,
                    },
                    "home_last_auto_save_time",
                )
        else:
            st.info("No market data connected yet. Click MT5 M1, MT5 M2 100D, or Twelve Only.")

    with home_tabs[1]:
        doo_prime_panel()