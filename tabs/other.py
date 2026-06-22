"""V24 lazy Other tab.

Engine, Train Data, Database, Pre Original, Backtest, and Profile live here as inner
buttons. Nothing heavy is imported or rendered until the user presses the
manual Run Calculate button.
"""

import streamlit as st

try:
    from core.global_upgrade import render_page_shell, render_tab_footer
except Exception:
    def render_page_shell(title, subtitle="", icon=""):
        st.markdown(f"# {icon} {title}")
        if subtitle:
            st.caption(subtitle)
    def render_tab_footer(title):
        return None


INNER_TABS = [
    ("Engine", "⚡", "tabs.engine"),
    ("Train Data", "🧠", "tabs.train_data"),
    ("Database", "🗄️", "tabs.database_tab"),
    ("Pre Original", "🧾", "tabs.pre_original"),
    ("Backtest", "🧪", "tabs.engine_split.original_backtest_inner"),
    ("Profile", "👤", "tabs.profile"),
]


def _choose_inner_tab():
    current = st.session_state.get("other_inner_tab", "Engine")
    names = [name for name, _, _ in INNER_TABS]
    if current not in names:
        current = "Engine"
        st.session_state.other_inner_tab = current

    if bool(st.session_state.get("phone_mode", False)):
        current = st.selectbox("Other inner tab", names, index=names.index(current), key="other_inner_tab_phone_20260617")
        st.session_state.other_inner_tab = current
    else:
        cols = st.columns(3)
        for idx, (name, icon, _module) in enumerate(INNER_TABS):
            with cols[idx % 3]:
                label = f"✅ {icon} {name}" if current == name else f"{icon} {name}"
                if st.button(label, use_container_width=True, key=f"other_inner_tab_{idx}"):
                    st.session_state.other_inner_tab = name
                    current = name
    return st.session_state.get("other_inner_tab", current)


def _render_inner_page(name: str):
    module_map = {name: module for name, _icon, module in INNER_TABS}
    module_name = module_map.get(name)
    if not module_name:
        st.warning("Unknown inner tab.")
        return
    try:
        import importlib
        mod = importlib.import_module(module_name)
        show = getattr(mod, "show")
        return show()
    except Exception as exc:
        st.error(f"{name} inner tab could not run safely.")
        with st.expander(f"Show {name} error", expanded=True):
            st.code(str(exc))


def show():
    render_page_shell(
        "Other",
        "Lazy inner workspace. Press Run Calculate first; otherwise Engine, Train Data, Database, Pre Original, Backtest, and Profile do not run.",
        "📂",
    )

    canonical_ready = bool(st.session_state.get("canonical_decision_result_20260617")) and bool(st.session_state.get("settings_run_complete_20260617", True))
    st.caption(
        "The main Settings Run Calculation publishes this workspace. Hidden inner tabs stay idle; only the selected inner tab renders, with no second calculation required."
    )
    selected = _choose_inner_tab()

    if not canonical_ready:
        with st.expander("📂 Open / Close — Other tab is waiting", expanded=True):
            st.info("Run Calculation + Open Lunch in Settings once. Engine, Train Data, Database, Pre Original, Backtest, and Profile will then read the same completed generation.")
        render_tab_footer("Other")
        return

    st.markdown(f"### Running inner tab: {selected}")
    _render_inner_page(selected)
    if selected in {"Backtest", "Train Data", "Engine"}:
        try:
            from ui.decision_product_panel_20260617 import render_validation_calibration_panel
            render_validation_calibration_panel()
        except Exception as exc:
            st.caption(f"Validation/calibration details skipped safely: {exc}")
    render_tab_footer("Other")


# 2026-06-14 Logic Safety Guard + Hidden Danger Engine for Other/Dinner-regime workspace.
try:
    from ui.logic_safety_panel import install as _install_logic_safety_panel_other_20260614
    _install_logic_safety_panel_other_20260614(globals(), location="Other/Dinner-Regime")
    del _install_logic_safety_panel_other_20260614
except Exception as _logic_safety_panel_other_exc_20260614:
    try:
        import streamlit as st
        st.warning(f"Logic Safety Guard wrapper skipped: {_logic_safety_panel_other_exc_20260614}")
    except Exception:
        pass
