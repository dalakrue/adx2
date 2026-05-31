import time
import streamlit as st

from core.common import DEFAULT_TABS, log_event
from core.styles import request_close_sidebar
from core.data_connectors import manual_connect
from core.websocket_feed import render_websocket_panel, websocket_status
from core.system_upgrade import sidebar_health_card, add_snapshot_button
from core.system_contract import render_sidebar_mini_contract, record_system_event

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None


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
        st.session_state.setdefault("activity_log", [])
        st.session_state.activity_log.insert(0, str(message))


def _fmt_timer(seconds):
    try:
        seconds = max(0, int(seconds))
    except Exception:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    sec = seconds % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _timer_alarm_html(duration_seconds: int = 8):
    """Play a longer browser-side timer alarm.

    Streamlit reruns only once when the timer finishes, so a single short audio tag
    is easy to miss. This component uses Web Audio beeps for about 8 seconds and
    also asks the phone/browser to vibrate when supported.
    """
    try:
        duration_seconds = int(max(5, min(duration_seconds, 10)))
    except Exception:
        duration_seconds = 8

    import streamlit.components.v1 as components

    components.html(
        f"""
        <div style="font-family:Arial,sans-serif;padding:10px;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;font-weight:800;text-align:center;">
          ⏰ TIME UP — alarm playing for {duration_seconds} seconds
        </div>
        <script>
        (async function() {{
          const seconds = {duration_seconds};
          const stopAt = Date.now() + seconds * 1000;
          try {{
            if (navigator.vibrate) {{
              navigator.vibrate([700,220,700,220,700,220,1000,300,1000,300,1400]);
            }}
          }} catch(e) {{}}

          try {{
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioCtx();
            async function oneBeep(freq, lengthMs) {{
              const osc = ctx.createOscillator();
              const gain = ctx.createGain();
              osc.type = "square";
              osc.frequency.value = freq;
              gain.gain.setValueAtTime(0.0001, ctx.currentTime);
              gain.gain.exponentialRampToValueAtTime(0.22, ctx.currentTime + 0.02);
              gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + lengthMs / 1000);
              osc.connect(gain);
              gain.connect(ctx.destination);
              osc.start();
              osc.stop(ctx.currentTime + lengthMs / 1000 + 0.03);
              await new Promise(r => setTimeout(r, lengthMs + 110));
            }}
            while (Date.now() < stopAt) {{
              await oneBeep(880, 260);
              await oneBeep(1320, 260);
            }}
            setTimeout(() => ctx.close && ctx.close(), 600);
          }} catch(e) {{
            try {{
              const audio = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
              audio.loop = true;
              audio.volume = 1.0;
              audio.play();
              setTimeout(() => {{ audio.pause(); audio.currentTime = 0; }}, seconds * 1000);
            }} catch(err) {{}}
          }}
        }})();
        </script>
        """,
        height=58,
    )


def _sidebar_timer_panel():
    st.session_state.setdefault("sidebar_timer_minutes", int(st.session_state.get("timer_minutes", 120) or 120))
    st.session_state.setdefault("sidebar_timer_end", 0.0)
    st.session_state.setdefault("sidebar_timer_alerted", False)

    end = float(st.session_state.get("sidebar_timer_end", 0) or 0)
    active = end > time.time()
    remaining = max(0, int(end - time.time())) if end else 0

    with st.expander("⏱ Trade Timer / Sound Alert", expanded=active):
        st.markdown(
            f"""
            <div class="sidebar-timer-card">
                <div><b>Status:</b> {'RUNNING' if active else 'STOPPED'}</div>
                <div class="sidebar-timer-big">{_fmt_timer(remaining)}</div>
                <small>When it reaches 0, the browser plays an 8-second sound + phone vibration.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mins = st.number_input(
            "Timer minutes",
            min_value=1,
            max_value=1440,
            value=int(st.session_state.get("sidebar_timer_minutes", 120) or 120),
            step=5,
            key="sidebar_timer_minutes_input",
        )
        st.session_state.sidebar_timer_minutes = int(mins)
        t1, t2 = st.columns(2)
        with t1:
            if st.button("▶ Start", use_container_width=True, key="sidebar_timer_start"):
                st.session_state.sidebar_timer_end = time.time() + int(mins) * 60
                st.session_state.sidebar_timer_alerted = False
                _safe_log_event(f"Sidebar timer started: {int(mins)} minutes")
                _safe_rerun()
        with t2:
            if st.button("■ Reset", use_container_width=True, key="sidebar_timer_reset"):
                st.session_state.sidebar_timer_end = 0.0
                st.session_state.sidebar_timer_alerted = False
                _safe_log_event("Sidebar timer reset")
                _safe_rerun()

    if active:
        try:
            st_autorefresh(interval=1000, key="sidebar_trade_timer_tick")
        except Exception:
            pass
    elif end and remaining <= 0 and not bool(st.session_state.get("sidebar_timer_alerted", False)):
        _timer_alarm_html()
        st.session_state.sidebar_timer_alerted = True
        st.warning("⏱ Timer reached 0. Check your trade / exit plan now.")


def _init_sidebar_state():
    st.session_state.setdefault("tab_choice", DEFAULT_TABS[0] if DEFAULT_TABS else "Home")
    if st.session_state.tab_choice not in DEFAULT_TABS:
        st.session_state.tab_choice = DEFAULT_TABS[0] if DEFAULT_TABS else "Home"
    st.session_state.setdefault("symbol", "XAUUSD")
    st.session_state.setdefault("phone_mode", False)
    st.session_state.setdefault("connector_mode", "fallback")
    st.session_state.setdefault("timeframe", "M1")
    st.session_state.setdefault("connector_bars", 600)


def _normalize_symbol(symbol):
    return str(symbol or "XAUUSD").strip().upper().replace(" ", "").replace("/", "")


def _set_mode(phone_mode: bool):
    st.session_state.phone_mode = bool(phone_mode)
    request_close_sidebar()
    _safe_rerun()


def _open_tab(tab):
    st.session_state.tab_choice = tab
    _safe_log_event(f"Open tab: {tab}")
    request_close_sidebar()
    _safe_rerun()


def _connect_now(label="Refresh", quick=False):
    """
    Shared sidebar connector action.
    quick=True is intentionally small/fast so the top Refresh button does not
    wait for a heavy 60,000 candle request. The heavy amount is still available
    inside the collapsed Connector settings expander.
    """
    try:
        bars = 600 if quick else int(st.session_state.get("connector_bars", 600))
        timeframe = str(st.session_state.get("timeframe", "M1") or "M1").upper()
        with st.spinner(f"{label}: loading {st.session_state.symbol} {timeframe} {bars:,} candles..."):
            df, ok, source, msg = manual_connect(
                mode=st.session_state.get("connector_mode", "fallback"),
                symbol=st.session_state.get("symbol", "XAUUSD"),
                api_key=st.session_state.get("twelve_api_key", ""),
                bars=bars,
                timeframe=timeframe,
                bridge_url=st.session_state.get("doo_bridge_url", ""),
                bridge_token=st.session_state.get("doo_bridge_token", ""),
            )
        if ok:
            st.success(f"{source}: {len(df):,} rows loaded")
        else:
            st.warning(str(msg))
        _safe_rerun()
    except Exception as exc:
        st.error(f"{label} failed: {exc}")


def sidebar_nav():
    _init_sidebar_state()

    with st.sidebar:
        st.markdown("### ⚡ ADX Quant Pro")
        st.caption("Tab buttons stay visible. All controls/status panels are open/close fields.")

        icons = {"Home": "🏠", "Engine": "⚡", "Train Data": "🧠", "Pre Original": "🧾", "Database": "🗄️", "Profile": "👤"}
        for tab in DEFAULT_TABS:
            icon = icons.get(tab, "•")
            active = tab == st.session_state.get("tab_choice")
            label = f"✅ {icon} {tab}" if active else f"{icon} {tab}"
            if st.button(label, use_container_width=True, key=f"nav_{tab}"):
                _open_tab(tab)

        st.markdown("---")

        with st.expander("⚡ Fast symbol + refresh controls", expanded=False):
            nav_symbol = st.text_input(
                "Symbol",
                value=st.session_state.get("symbol", "XAUUSD"),
                key="sidebar_symbol",
                placeholder="XAUUSD / EURUSD / GBPUSD",
            )
            st.session_state.symbol = _normalize_symbol(nav_symbol)

            top_cols = st.columns(2)
            with top_cols[0]:
                if st.button("⚡ Quick Refresh", use_container_width=True, key="sidebar_refresh_now"):
                    _connect_now("Quick refresh", quick=True)
            with top_cols[1]:
                if st.button("⛔ Off", use_container_width=True, key="sidebar_disconnect_api"):
                    for k in [
                        "connected", "source", "last_df", "last_fetch",
                        "doo_deep_results", "doo_deep_last_refresh",
                        "system_demo_guard_used",
                    ]:
                        st.session_state.pop(k, None)
                    st.session_state.connected = False
                    st.session_state.source = "DISCONNECTED"
                    try:
                        record_system_event("connection", "manual disconnect", "OK", "User disconnected global connector", persist=True)
                    except Exception:
                        pass
                    _safe_rerun()

            rows = len(st.session_state.get("last_df")) if st.session_state.get("last_df") is not None else 0
            st.caption(f"{st.session_state.get('source','DISCONNECTED')} | {st.session_state.get('timeframe','M1')} | {rows:,} rows | UI={'Phone' if st.session_state.get('phone_mode') else 'Laptop'}")

        with st.expander("🔌 Connector settings", expanded=False):
            connector_mode = st.selectbox(
                "API source",
                ["fallback", "mt5", "twelve", "doo_bridge"],
                index=["fallback", "mt5", "twelve", "doo_bridge"].index(st.session_state.get("connector_mode", "fallback")) if st.session_state.get("connector_mode", "fallback") in ["fallback", "mt5", "twelve", "doo_bridge"] else 0,
                key="sidebar_connector_mode",
            )
            st.session_state.connector_mode = connector_mode

            tfs = ["M1", "M2", "M3", "M5", "M10", "M15", "M30", "H1", "H4", "D1"]
            timeframe = st.selectbox(
                "Timeframe",
                tfs,
                index=tfs.index(st.session_state.get("timeframe", "M1")) if st.session_state.get("timeframe", "M1") in tfs else 0,
                key="sidebar_timeframe",
            )
            st.session_state.timeframe = timeframe

            bars = st.number_input(
                "Candles / bars",
                min_value=100,
                max_value=250000,
                value=int(st.session_state.get("connector_bars", 600)),
                step=100,
                key="sidebar_connector_bars",
                help="Use 600 for fast refresh. Use 5,000+ only when you need deeper history.",
            )
            st.session_state.connector_bars = int(bars)

            if connector_mode in ["twelve", "fallback"]:
                st.session_state.twelve_api_key = st.text_input(
                    "Twelve Data API key",
                    value=st.session_state.get("twelve_api_key", ""),
                    type="password",
                    key="sidebar_twelve_api_key",
                )
            if connector_mode in ["doo_bridge", "fallback"]:
                st.session_state.doo_bridge_url = st.text_input(
                    "Doo Bridge URL",
                    value=st.session_state.get("doo_bridge_url", ""),
                    key="sidebar_doo_bridge_url",
                    placeholder="http://127.0.0.1:8000/candles",
                )
                st.session_state.doo_bridge_token = st.text_input(
                    "Doo Bridge token optional",
                    value=st.session_state.get("doo_bridge_token", ""),
                    type="password",
                    key="sidebar_doo_bridge_token",
                )
            if connector_mode == "mt5":
                st.info("MT5 needs your local MT5 terminal open and logged in.")

            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("⚡ Fast 600", use_container_width=True, key="sidebar_connect_fast600"):
                    _connect_now("Fast connect", quick=True)
            with c_b:
                if st.button("✅ Load chosen", use_container_width=True, key="sidebar_connect_api"):
                    _connect_now("Connect", quick=False)

        with st.expander("🩺 Shared system health", expanded=False):
            sidebar_health_card()
            render_sidebar_mini_contract()
            add_snapshot_button("sidebar")

        _sidebar_timer_panel()

        with st.expander("🎨 UI mode", expanded=False):
            mode_cols = st.columns(2)
            with mode_cols[0]:
                if st.button("📱 Phone UI", use_container_width=True, key="nav_phone"):
                    _set_mode(True)
            with mode_cols[1]:
                if st.button("🖥️ Laptop UI", use_container_width=True, key="nav_wide"):
                    _set_mode(False)

        with st.expander("🌐 Websocket live feed", expanded=False):
            render_websocket_panel(location="sidebar")

        with st.expander("ℹ️ System Info", expanded=False):
            ws = websocket_status()
            st.write("Symbol:", st.session_state.get("symbol", "XAUUSD"))
            st.write("Current Tab:", st.session_state.get("tab_choice", "Home"))
            st.write("Connected:", st.session_state.get("connected", False))
            st.write("Websocket:", f"enabled={ws.get('enabled')} live={ws.get('runtime_connected')} queued={ws.get('queued_ticks')}")
            st.write("Auto app refresh:", "10 minutes")

    return st.session_state.get("tab_choice", DEFAULT_TABS[0] if DEFAULT_TABS else "Home")
