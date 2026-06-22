from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_lunch_has_exactly_six_principal_closed_first_gates():
    source = text("ui/lunch_four_core_fields_20260619.py")
    body = source.split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert body.count("if _gate(") == 6
    for label in (
        "1. Open / Close — Full Metric 25-Day History + Decision Tables",
        "2. Open / Close — Power BI Price Prediction Path",
        "3. Open / Close — 25-Day Regime History + Lower / Medium / Higher Standards",
        "4. Open / Close — Dinner Full Combined Intelligence",
        "5. Open / Close — Grounded AI Assistant",
        "6. Open / Close — Future Strategy Research History",
    ):
        assert label in source
    assert "Exactly 6" in body
    assert "with st.expander(FULL_METRIC_FIELD" not in source

def test_field5_and_field6_are_principal_not_nested_inside_field4():
    source = text("ui/lunch_four_core_fields_20260619.py")
    field4 = source.split("def _render_regime_combined_logic", 1)[1].split("def _render_ai_assistant_lazy", 1)[0]
    assert "render_compact_ai_assistant" not in field4
    assert "render_system_readiness" not in field4
    body = source.split("def render_lunch_six_core_fields", 1)[1].split("def render_lunch_four_core_fields", 1)[0]
    assert "if _gate(AI_FIELD, 5, state):" in body
    assert "if _gate(READINESS_FIELD, 6, state):" in body

def test_lunch_root_renders_quick_decision_search_then_six_field_renderer():
    source = text("tabs/final_lunch_upgrade_20260617.py")
    assert source.index("render_eight_cards") < source.index("render_lunch_search") < source.index("render_lunch_six_core_fields")
    renderer = text("ui/lunch_four_core_fields_20260619.py")
    assert "def render_lunch_six_core_fields" in renderer
    assert "Backward-compatible callable" in renderer
    router = text("tabs/antd_page_router_20260615.py")
    assert 'if not subpage:' in router
    assert '"Lunch Six Principal Fields"' in router
    nav = text("ui/antd_navigation_20260615.py")
    assert "LUNCH_CHILDREN: List[str] = []" in nav

def test_powerbi_does_not_add_nested_error_expanders():
    source = text("ui/powerbi_cached_renderer_20260619.py")
    assert 'with st.expander("Open / Close — Power BI error details"' not in source
    assert 'with st.expander("Open / Close — Projection integrity details"' not in source


def test_native_sidebar_is_not_rendered_or_reopenable():
    runner = text("core/app/runner.py")
    assert "sidebar_nav()" not in runner
    assert 'use_native_sidebar_fallback_20260619"] = False' in runner
    popup = text("ui/liquid_menu_popup_20260615.py")
    assert "with st.sidebar" not in popup
    assert "Open Sidebar" not in popup
    lock = text("ui/sidebar_hard_lock.py")
    assert '[data-testid="stSidebarCollapsedControl"]' in lock
    assert "def show_native_sidebar" in lock
    assert "Backward-compatible no-op" in lock
