"""Main-page replacement for the native sidebar controls.

This panel mirrors the critical sidebar functions with unique widget keys, so it
can be rendered at the same time as the native sidebar without duplicate-key
crashes. It writes to the same session_state fields used by the original sidebar
connector/timer logic.
"""
from __future__ import annotations
import time
import streamlit as st

try:
    from core.navigation_parts.state import _normalize_symbol, _safe_log_event
except Exception:
    def _normalize_symbol(x): return str(x or "EURUSD").upper().replace("/", "").replace(" ", "")
    def _safe_log_event(message): pass

try:
    from core.navigation_parts.connection import _connect_now
except Exception:
    def _connect_now(label="Connect", quick=False):
        st.warning("Connector function is unavailable. Native sidebar backup may still work.")

try:
    from core.navigation_parts.panels import _disconnect_shared_state
except Exception:
    def _disconnect_shared_state(reason="manual disconnect"):
        for k in ["connected", "source", "last_df", "last_fetch", "last_connection_error", "last_connection_message", "last_connection_rows"]:
            st.session_state.pop(k, None)
        st.session_state.connected = False
        st.session_state.source = "DISCONNECTED"
        st.session_state.last_connection_message = reason

def request_open_native_sidebar():
    # Native sidebar is optional backup only; no JavaScript DOM open is used.
    try:
        from ui.sidebar_hard_lock import enable_native_sidebar_backup
        enable_native_sidebar_backup()
    except Exception:
        pass

def request_close_native_sidebar():
    # Compatibility with older calls. No JavaScript DOM close attempt is used,
    # and this no longer locks the sidebar OFF. It only records close intent so
    # the native backup can always open again after any button click.
    try:
        from ui.sidebar_hard_lock import init_sidebar_policy, inject_sidebar_policy_css
        init_sidebar_policy()
        st.session_state["sidebar_close_requested_native_only"] = True
        st.session_state["new7_native_sidebar_status_20260614"] = "Close requested; native backup remains available."
        inject_sidebar_policy_css()
    except Exception:
        pass


def _safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass




def _market_connect_callback(key_prefix: str) -> None:
    """One click starts the connection; persistent state survives the rerun."""
    _connect_now(f"{key_prefix} connect", quick=str(key_prefix).startswith("settings_"))
    request_close_native_sidebar()


def _market_disconnect_callback() -> None:
    _disconnect_shared_state("manual market disconnect")
    try:
        from core.connector_state_machine_20260621 import disconnect
        disconnect(st.session_state, "market_connector_20260621", "Disconnected by user.")
    except Exception:
        pass
    request_close_native_sidebar()

def _fmt_timer(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def render_native_sidebar_js_controls() -> None:
    st.markdown('<div class="new7-card"><b>🧭 Native Sidebar Backup</b><br><span style="color:#64748b;font-size:.78rem;">Native sidebar is optional backup only. No JavaScript open/close buttons are used.</span></div>', unsafe_allow_html=True)


def _render_connector_status_only() -> None:
    """Read-only connector status for menu/sidebar surfaces.

    API secret inputs live only in Settings, preventing duplicate password fields
    and widget state conflicts in the sidebar, drawer and NLP workspace.
    """
    st.markdown("#### 🔌 Connector Status")
    try:
        rows = len(st.session_state.get("last_df")) if st.session_state.get("last_df") is not None else 0
    except Exception:
        rows = 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Market API", str(st.session_state.get("source", "DISCONNECTED") or "DISCONNECTED"))
    c2.metric("Symbol / TF", f"{st.session_state.get('symbol','EURUSD')} / {st.session_state.get('timeframe','H1')}")
    c3.metric("Rows", f"{rows:,}")
    try:
        from core.finnhub_connector import connection_status
        status = connection_status()
        f1, f2 = st.columns(2)
        f1.metric("Finnhub", "CONNECTED" if status.get("connected") else "DISCONNECTED")
        f2.metric("Availability", status.get("availability", "UNKNOWN"))
    except Exception as exc:
        st.caption(f"Finnhub status unavailable: {str(exc)[:100]}")
    st.caption("API keys are entered once in Settings only.")
    if st.button("⚙️ Open Settings API Controls", key="open_settings_api_controls_20260618", use_container_width=True):
        st.session_state["active_page"] = "Settings"
        st.session_state["active_subpage"] = ""
        st.session_state["tab_choice"] = "Settings"
        _safe_rerun()


def _render_connector(*, key_prefix: str = "main_drawer", show_secret_inputs: bool = True) -> None:
    st.markdown("#### 🔌 API / Data Connection")
    symbol = st.text_input(
        "Symbol",
        value=st.session_state.get("symbol", "EURUSD"),
        key=f"{key_prefix}_symbol_v1",
        placeholder="EURUSD / XAUUSD / GBPUSD",
    )
    st.session_state.symbol = _normalize_symbol(symbol)

    connector_options = ["twelve", "mt5", "doo_bridge", "fallback", "safe_demo"]
    current_mode = st.session_state.get("connector_mode", "twelve")
    if current_mode not in connector_options:
        current_mode = "twelve"
    connector_mode = st.selectbox(
        "API source",
        connector_options,
        index=connector_options.index(current_mode),
        key=f"{key_prefix}_connector_mode_v1",
    )
    st.session_state.connector_mode = connector_mode

    tfs = ["M1", "M2", "M5", "M15", "H1", "H4", "D1", "CUSTOM"]
    current_tf = str(st.session_state.get("timeframe", "H1") or "H1").upper()
    if current_tf not in tfs:
        current_tf = "H1"
    timeframe = st.selectbox(
        "Timeframe",
        tfs,
        index=tfs.index(current_tf),
        key=f"{key_prefix}_timeframe_v1",
        help="CUSTOM loads H1 as main data and M1 only as confirmation data.",
    )
    st.session_state.timeframe = timeframe

    bars = st.number_input(
        "Candles / bars",
        min_value=100,
        max_value=250000,
        value=int(st.session_state.get("connector_bars", 600) or 600),
        step=100,
        key=f"{key_prefix}_connector_bars_v1",
    )
    st.session_state.connector_bars = int(bars)

    if connector_mode in ["twelve", "fallback"] and show_secret_inputs:
        entered_twelve_key = st.text_input(
            "Twelve Data API key",
            value=st.session_state.get("twelve_api_key", ""),
            type="password",
            key=f"{key_prefix}_twelve_api_key_v1",
        )
        # A blank hidden/drawer widget must not erase a key saved from the
        # Settings mobile paste box during the same rerun.
        if str(entered_twelve_key or "").strip() or not st.session_state.get("twelve_api_key"):
            st.session_state.twelve_api_key = str(entered_twelve_key or "").strip()
    if connector_mode in ["doo_bridge", "fallback"] and show_secret_inputs:
        st.session_state.doo_bridge_url = st.text_input(
            "Doo Bridge URL",
            value=st.session_state.get("doo_bridge_url", ""),
            key=f"{key_prefix}_doo_bridge_url_v1",
            placeholder="http://127.0.0.1:8000/candles",
        )
        st.session_state.doo_bridge_token = st.text_input(
            "Doo Bridge token optional",
            value=st.session_state.get("doo_bridge_token", ""),
            type="password",
            key=f"{key_prefix}_doo_bridge_token_v1",
        )
    if not show_secret_inputs and connector_mode in ["twelve", "fallback"]:
        key_ready = bool(str(st.session_state.get("twelve_api_key", "") or "").strip())
        st.info("Twelve Data key: saved for this session." if key_ready else "Twelve Data key is empty. Paste and save it in the API Key Paste Center above.")
    if not show_secret_inputs and connector_mode in ["doo_bridge", "fallback"]:
        st.caption("Doo Bridge URL/token remain available in the app drawer connector. Settings restores the requested Twelve Data and MT5 controls without duplicating secret fields.")

    if connector_mode == "safe_demo":
        st.session_state.allow_safe_demo = True
        st.warning("SAFE_DEMO is only for UI testing, not live trading decisions.")
    else:
        st.session_state.allow_safe_demo = st.checkbox(
            "Allow SAFE_DEMO fallback when real data fails",
            value=bool(st.session_state.get("allow_safe_demo", False)),
            key=f"{key_prefix}_allow_safe_demo_v1",
        )

    try:
        from core.connector_state_machine_20260621 import snapshot
        persistent = snapshot(st.session_state, "market_connector_20260621")
    except Exception:
        persistent = {"state": "CONNECTED" if st.session_state.get("connected") else "DISCONNECTED", "message": ""}
    c1, c2 = st.columns(2)
    connect_label = "🔄 Refresh Connected Feed" if persistent.get("state") == "CONNECTED" else "✅ Connect Once Using Saved Settings"
    c1.button(
        connect_label, key=f"{key_prefix}_connect_api_v1", use_container_width=True,
        on_click=_market_connect_callback, args=(key_prefix,), disabled=persistent.get("state") == "CONNECTING",
    )
    c2.button(
        "⛔ Disconnect", key=f"{key_prefix}_disconnect_api_v1", use_container_width=True,
        on_click=_market_disconnect_callback, disabled=persistent.get("state") == "CONNECTING",
    )
    state_col, message_col = st.columns(2)
    state_col.metric("Connection State", str(persistent.get("state", "DISCONNECTED")))
    message_col.caption(str(persistent.get("message") or "Enter settings and press once to connect."))

    try:
        rows = len(st.session_state.get("last_df")) if st.session_state.get("last_df") is not None else 0
    except Exception:
        rows = 0
    source = str(st.session_state.get("source", "DISCONNECTED") or "DISCONNECTED")
    m1, m2, m3 = st.columns(3)
    m1.metric("Market API", source)
    m2.metric("Symbol / TF", f"{st.session_state.get('symbol','EURUSD')} / {st.session_state.get('timeframe','H1')}")
    m3.metric("Loaded Rows", f"{rows:,}")

    st.markdown("##### Finnhub Connection Status")
    st.caption("The canonical Finnhub key input is in the Settings Finnhub section; this market panel displays status only.")
    try:
        from core.finnhub_connector import connection_status
        status = connection_status()
        f1, f2 = st.columns(2)
        f1.metric("Connection", "CONNECTED" if status.get("connected") else "DISCONNECTED")
        f2.metric("API", status.get("availability", "UNKNOWN"))
        st.caption(f"Last successful connection: {status.get('last_success', 'Never')}")
    except Exception:
        st.info("Finnhub connector status is unavailable; the rest of the application remains usable.")
    if st.button("Finnhub key is managed in the Settings Finnhub section", key=f"{key_prefix}_finnhub_settings_owner_20260618", use_container_width=True, disabled=True):
        pass


def _render_timer(*, key_prefix: str = "main_drawer") -> None:
    st.markdown("#### ⏱ Trade Timer / Sound Alert")
    st.session_state.setdefault("sidebar_timer_minutes", int(st.session_state.get("timer_minutes", 120) or 120))
    st.session_state.setdefault("sidebar_timer_end", 0.0)
    st.session_state.setdefault("sidebar_timer_alerted", False)

    mins = st.number_input(
        "Timer minutes",
        min_value=1,
        max_value=1440,
        value=int(st.session_state.get("sidebar_timer_minutes", 120) or 120),
        step=5,
        key=f"{key_prefix}_timer_minutes_input_v1",
    )
    st.session_state.sidebar_timer_minutes = int(mins)

    try:
        import streamlit.components.v1 as components
        components.html(
            """
<button id="unlockMainDrawerTimerSound" style="width:100%;min-height:38px;border-radius:999px;border:1px solid #93c5fd;background:#eff6ff;font-weight:900;cursor:pointer;">🔊 Enable Timer Sound</button>
<div id="unlockMainDrawerTimerStatus" style="font-size:11px;text-align:center;margin-top:4px;color:#075985;">Tap once on phone/Cloud so alarm sound can play.</div>
<script>
(function(){
  const btn=document.getElementById('unlockMainDrawerTimerSound');
  const status=document.getElementById('unlockMainDrawerTimerStatus');
  async function unlock(){
    try{
      const AudioCtx=window.AudioContext||window.webkitAudioContext;
      const ctx=new AudioCtx(); const osc=ctx.createOscillator(); const gain=ctx.createGain();
      osc.frequency.value=660; gain.gain.value=0.001; osc.connect(gain); gain.connect(ctx.destination);
      osc.start(); osc.stop(ctx.currentTime+0.04); localStorage.setItem('m1_adx_timer_sound_unlocked','yes');
      status.textContent='Sound unlocked. Timer alarm can play on this browser.'; setTimeout(()=>ctx.close&&ctx.close(),120);
    }catch(e){status.textContent='Browser blocked sound. Keep page active and tap Start again.';}
  }
  btn.addEventListener('click', unlock);
  btn.addEventListener('touchend', function(e){e.preventDefault(); unlock();}, {passive:false});
})();
</script>
""",
            height=78,
        )
    except Exception:
        pass

    t1, t2 = st.columns(2)
    with t1:
        if st.button("▶ Start Timer", key=f"{key_prefix}_timer_start_v1", use_container_width=True):
            st.session_state.sidebar_timer_end = time.time() + int(mins) * 60
            st.session_state.sidebar_timer_alerted = False
            _safe_log_event(f"Main drawer timer started: {int(mins)} minutes")
            request_close_native_sidebar()
            _safe_rerun()
    with t2:
        if st.button("■ Reset Timer", key=f"{key_prefix}_timer_reset_v1", use_container_width=True):
            st.session_state.sidebar_timer_end = 0.0
            st.session_state.sidebar_timer_alerted = False
            _safe_log_event("Main drawer timer reset")
            _safe_rerun()

    end = float(st.session_state.get("sidebar_timer_end", 0) or 0)
    now = time.time()
    active = end > now
    remaining = max(0, int(end - now)) if end else 0
    status = "RUNNING" if active else ("TIME UP" if end else "STOPPED")
    st.markdown(
        f"""
<div class="new7-card">
  <b>Status:</b> {status}<br>
  <div style="font-size:1.55rem;font-weight:950;letter-spacing:.04em;">{_fmt_timer(remaining)}</div>
  <span style="font-size:.76rem;color:#64748b;">Timer state is shared with the native sidebar.</span>
</div>
""",
        unsafe_allow_html=True,
    )

    if end:
        try:
            import streamlit.components.v1 as components
            alarm_id = f"main_drawer_trade_timer_alarm_{int(end)}"
            components.html(
                f"""
<div style="font-family:Arial,sans-serif;padding:8px 10px;border-radius:14px;background:#eef6ff;border:1px solid #bfdbfe;color:#0f172a;text-align:center;">
  <div style="font-size:12px;font-weight:900;letter-spacing:.04em;">LIVE TIMER</div>
  <div id="mainDrawerLiveTimer" style="font-size:24px;font-weight:950;margin-top:3px;">--:--:--</div>
  <div id="mainDrawerLiveTimerStatus" style="font-size:12px;margin-top:2px;">syncing...</div>
</div>
<script>
(function() {{
  const endMs = {float(end) * 1000:.0f};
  const alarmKey = "{alarm_id}";
  const timerEl = document.getElementById("mainDrawerLiveTimer");
  const statusEl = document.getElementById("mainDrawerLiveTimerStatus");
  function pad(n) {{ return String(n).padStart(2, "0"); }}
  function fmt(sec) {{ sec=Math.max(0,Math.floor(sec)); const h=Math.floor(sec/3600); const m=Math.floor((sec%3600)/60); const s=sec%60; return pad(h)+":"+pad(m)+":"+pad(s); }}
  async function alarm() {{
    if(localStorage.getItem(alarmKey)==='played') return;
    localStorage.setItem(alarmKey,'played'); statusEl.textContent='TIME UP — alarm playing';
    try {{ if(navigator.vibrate) navigator.vibrate([700,220,700,220,1000]); }} catch(e) {{}}
    try {{
      const AudioCtx=window.AudioContext||window.webkitAudioContext; const ctx=new AudioCtx(); const stopAt=Date.now()+8000;
      async function beep(freq,len) {{ const osc=ctx.createOscillator(); const gain=ctx.createGain(); osc.type='square'; osc.frequency.value=freq; gain.gain.setValueAtTime(0.0001,ctx.currentTime); gain.gain.exponentialRampToValueAtTime(0.25,ctx.currentTime+0.02); gain.gain.exponentialRampToValueAtTime(0.0001,ctx.currentTime+len/1000); osc.connect(gain); gain.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime+len/1000+0.03); await new Promise(r=>setTimeout(r,len+100)); }}
      while(Date.now()<stopAt) {{ await beep(880,250); await beep(1320,250); }} setTimeout(()=>ctx.close&&ctx.close(),500);
    }} catch(e) {{}}
  }}
  function tick() {{ const rem=(endMs-Date.now())/1000; timerEl.textContent=fmt(rem); if(rem<=0){{statusEl.textContent='TIME UP'; alarm();}} else if(rem<=60){{statusEl.textContent='FINAL 1 MIN';}} else {{statusEl.textContent='running';}} }}
  tick(); setInterval(tick,1000);
}})();
</script>
""",
                height=96,
            )
        except Exception:
            pass

    if end and end <= now and not bool(st.session_state.get("sidebar_timer_alerted", False)):
        st.session_state.sidebar_timer_alerted = True
        st.warning("⏱ Timer reached 0. Check your trade / exit plan now.")


def _render_ui_and_account(*, key_prefix: str = "main_drawer") -> None:
    st.markdown("#### 👤 Account")
    # Phone/Laptop controls intentionally live only inside the floating/sidebar
    # menu, preventing duplicate UI mode buttons in Settings and Profile.
    mode = "Phone" if bool(st.session_state.get("phone_mode", False)) else "Laptop"
    st.metric("Display Mode", mode, "Change from ⋮ Menu")
    user = st.session_state.get("new7_auth_email", "Guest") or "Guest"
    st.caption(f"Signed in: {user} | " + ("Guest mode" if st.session_state.get("new7_auth_guest") else "Account mode"))
    if st.button("🚪 Logout", key=f"{key_prefix}_logout_v1", use_container_width=True):
        st.session_state["new7_auth_logged_in"] = False
        st.session_state["new7_auth_guest"] = False
        st.session_state["new7_auth_email"] = ""
        st.session_state["auth_mode"] = ""
        _safe_rerun()


def render_sidebar_fallback_panel(expanded: bool = False) -> None:
    """Render critical sidebar controls in the main page/drawer."""
    with st.expander("⚙️ Open / Close — Main-Page Sidebar Controls: API + Timer + UI + Account", expanded=expanded):
        st.caption("This is the no-fail replacement for the native sidebar. It uses separate widget keys, so Home/Lunch and native sidebar do not conflict.")
        _render_connector()
        st.divider()
        _render_timer()
        st.divider()
        _render_ui_and_account()
