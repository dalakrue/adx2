import streamlit as st


def apply_global_styles(phone_mode: bool = False):
    maxw = "100vw" if phone_mode else "1180px"
    pad = "0.30rem" if phone_mode else "0.85rem 1.20rem"
    font = "10.8px" if phone_mode else "11.5px"
    h1 = "1.02rem" if phone_mode else "1.35rem"
    h2 = "0.90rem" if phone_mode else "1.12rem"
    h3 = "0.82rem" if phone_mode else "0.98rem"
    btn_h = "34px" if phone_mode else "38px"
    metric_v = "16.5px" if phone_mode else "19px"
    tab_font = "9px" if phone_mode else "10.5px"
    card_pad = "6px" if phone_mode else "11px"
    radius = "13px" if phone_mode else "18px"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {{
  --glass: rgba(255,255,255,.78);
  --glass2: rgba(240,249,255,.64);
  --line: rgba(14,116,144,.16);
  --txt:#0f172a;
  --muted:#075985;
  --blue:#38bdf8;
  --green:#16a34a;
  --red:#dc2626;
  --amber:#d97706;
}}

html, body, [class*="css"] {{
  font-family: Inter, sans-serif !important;
  color: var(--txt) !important;
  font-size:{font}!important;
}}

.stApp {{
  background:
    radial-gradient(circle at top left, rgba(224,242,254,.68), transparent 30%),
    radial-gradient(circle at top right, rgba(219,234,254,.55), transparent 34%),
    radial-gradient(circle at bottom right, rgba(240,249,255,.85), transparent 38%),
    linear-gradient(135deg,#f8fbff 0%,#eef8ff 45%,#f8fafc 100%) !important;
  background-attachment: fixed;
}}

.main .block-container {{
  max-width:{maxw}!important;
  width:100%!important;
  padding:{pad}!important;
  margin-left:auto!important;
  margin-right:auto!important;
}}

section[data-testid="stSidebar"] {{
  background: rgba(248,252,255,.82)!important;
  backdrop-filter: blur(26px) saturate(170%)!important;
  border-right:1px solid rgba(14,116,144,.14)!important;
}}

section[data-testid="stSidebar"] * {{
  font-size:{font}!important;
}}

h1 {{
  font-size:{h1}!important;
  line-height:1.18!important;
  margin-top:.20rem!important;
  margin-bottom:.35rem!important;
}}

h2 {{
  font-size:{h2}!important;
  line-height:1.18!important;
  margin-top:.20rem!important;
  margin-bottom:.30rem!important;
}}

h3 {{
  font-size:{h3}!important;
  line-height:1.18!important;
  margin-top:.18rem!important;
  margin-bottom:.25rem!important;
}}

p, li, label, span, div, small {{
  font-size:{font}!important;
}}

.stMarkdown, .stMarkdown * {{
  font-size:{font}!important;
  line-height:1.35!important;
}}

.glass-card,
.metric-glass,
.inner-glass,
.telegram-card,
.ocean-card,
.card,
.profile-glass,
.alert-card,
.status-card,
.regime-card {{
  background: linear-gradient(135deg, rgba(255,255,255,.82), rgba(240,249,255,.68))!important;
  border:1px solid rgba(14,116,144,.14)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  backdrop-filter: blur(18px) saturate(175%)!important;
  box-shadow:0 6px 18px rgba(2,132,199,.07), inset 0 1px 0 rgba(255,255,255,.72)!important;
  animation: fadeUp .25s ease both;
  overflow-wrap:anywhere!important;
}}

.alert-card {{
  border-left:4px solid var(--amber)!important;
}}

.status-card {{
  border-left:4px solid var(--blue)!important;
}}

.regime-card {{
  border-left:4px solid var(--green)!important;
}}

.badge-buy,
.badge-sell,
.badge-neutral,
.badge-wait,
.badge-danger,
.badge-warning,
.badge-info {{
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  border-radius:999px!important;
  padding:4px 8px!important;
  font-weight:900!important;
  font-size:{font}!important;
  border:1px solid rgba(15,23,42,.08)!important;
}}

.badge-buy {{
  background:rgba(220,252,231,.90)!important;
  color:#166534!important;
}}

.badge-sell {{
  background:rgba(254,226,226,.90)!important;
  color:#991b1b!important;
}}

.badge-neutral,
.badge-wait {{
  background:rgba(241,245,249,.90)!important;
  color:#334155!important;
}}

.badge-danger {{
  background:rgba(254,226,226,.92)!important;
  color:#b91c1c!important;
}}

.badge-warning {{
  background:rgba(254,243,199,.92)!important;
  color:#92400e!important;
}}

.badge-info {{
  background:rgba(224,242,254,.92)!important;
  color:#075985!important;
}}

.stButton>button {{
  width:100%;
  min-height:{btn_h}!important;
  border-radius:{radius}!important;
  border:1px solid rgba(14,116,144,.15)!important;
  background: linear-gradient(135deg, rgba(255,255,255,.84), rgba(224,242,254,.62))!important;
  color:#0f172a!important;
  font-weight:800!important;
  font-size:{font}!important;
  padding:5px 8px!important;
  backdrop-filter: blur(16px)!important;
  box-shadow:0 4px 12px rgba(2,132,199,.07)!important;
  transition:.16s ease!important;
}}

.stButton>button:hover {{
  background:rgba(224,242,254,.78)!important;
  transform: translateY(-1px);
}}

.stButton>button:active {{
  transform: scale(.985);
}}

div[data-testid="metric-container"] {{
  background: rgba(255,255,255,.80)!important;
  border:1px solid rgba(14,116,144,.13)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  backdrop-filter: blur(16px)!important;
  box-shadow:0 4px 12px rgba(2,132,199,.06)!important;
}}

div[data-testid="metric-container"] label {{
  color:#075985!important;
  font-size:{font}!important;
  font-weight:800!important;
}}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  color:#0f172a!important;
  font-size:{metric_v}!important;
  font-weight:900!important;
}}

.stTabs [data-baseweb="tab-list"] {{
  gap:4px!important;
  flex-wrap:wrap!important;
  background:rgba(255,255,255,.50)!important;
  border-radius:{radius}!important;
  padding:4px!important;
}}

.stTabs [data-baseweb="tab"] {{
  border-radius:{radius}!important;
  padding:5px 7px!important;
  background:rgba(255,255,255,.68)!important;
  color:#0f172a!important;
  font-size:{tab_font}!important;
  min-height:28px!important;
  font-weight:800!important;
}}

.stTabs [aria-selected="true"] {{
  background:rgba(186,230,253,.80)!important;
  color:#075985!important;
}}

input, textarea, select,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
  background:rgba(255,255,255,.86)!important;
  color:#0f172a!important;
  border-radius:{radius}!important;
  font-size:{font}!important;
  border:1px solid rgba(14,116,144,.16)!important;
}}

[data-testid="stDataFrame"] {{
  border-radius:{radius}!important;
  overflow:hidden!important;
  border:1px solid rgba(14,116,144,.12)!important;
}}

[data-testid="stDataFrame"],
[data-testid="stDataFrame"] * {{
  font-size:{font}!important;
}}
/* Keep wide tables usable on phones instead of forcing the whole page too narrow. */
.element-container:has([data-testid="stDataFrame"]) {{
  overflow-x:auto!important;
}}


div[data-testid="column"] {{
  padding-left:0.16rem!important;
  padding-right:0.16rem!important;
}}

.stProgress > div > div > div > div {{
  background:linear-gradient(90deg,#38bdf8,#22c55e)!important;
}}

.engine-timer-box,
.engine-warning,
.stat-box {{
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  font-size:{font}!important;
}}

.engine-timer-title,
.stat-title {{
  font-size:{font}!important;
}}

.engine-timer-value,
.stat-value {{
  font-size:{metric_v}!important;
}}

hr {{
  margin:.65rem 0!important;
  border-color:rgba(14,116,144,.13)!important;
}}

::-webkit-scrollbar {{
  width:6px;
  height:6px;
}}

::-webkit-scrollbar-thumb {{
  background:rgba(14,116,144,.25);
  border-radius:999px;
}}

::-webkit-scrollbar-track {{
  background:rgba(255,255,255,.35);
}}


/* Compact connector/sidebar helpers */
.compact-hero {{
  padding:7px!important;
  margin-bottom:6px!important;
}}
section[data-testid="stSidebar"] .stExpander {{
  border-radius:14px!important;
  border:1px solid rgba(14,116,144,.12)!important;
  background:rgba(255,255,255,.55)!important;
}}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
  gap:.35rem!important;
}}
section[data-testid="stSidebar"] hr {{
  margin:.45rem 0!important;
}}


.ws-live-card {{
  background: linear-gradient(135deg, rgba(236,253,245,.88), rgba(224,242,254,.72))!important;
  border:1px solid rgba(16,185,129,.22)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  box-shadow:0 7px 18px rgba(16,185,129,.08)!important;
}}
.ws-dot-live, .ws-dot-off {{
  display:inline-block!important;
  width:8px!important;
  height:8px!important;
  border-radius:999px!important;
  margin-right:6px!important;
}}
.ws-dot-live {{ background:#16a34a!important; box-shadow:0 0 0 5px rgba(22,163,74,.12)!important; }}
.ws-dot-off {{ background:#dc2626!important; box-shadow:0 0 0 5px rgba(220,38,38,.10)!important; }}

/* New calm/compact layout helpers */
.clean-section {{
  background:linear-gradient(135deg, rgba(255,255,255,.86), rgba(239,248,255,.68))!important;
  border:1px solid rgba(14,116,144,.14)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  margin:.45rem 0!important;
  box-shadow:0 6px 18px rgba(2,132,199,.06)!important;
}}

div[data-testid="stExpander"] {{
  border:1px solid rgba(14,116,144,.14)!important;
  border-radius:{radius}!important;
  background:rgba(255,255,255,.58)!important;
  box-shadow:0 4px 14px rgba(2,132,199,.045)!important;
  overflow:hidden!important;
}}

div[data-testid="stExpander"] summary {{
  font-weight:900!important;
  color:#075985!important;
}}

.sidebar-timer-card {{
  border:1px solid rgba(14,116,144,.14)!important;
  border-radius:16px!important;
  padding:9px!important;
  margin:.35rem 0 .55rem 0!important;
  background:linear-gradient(135deg, rgba(255,255,255,.88), rgba(224,242,254,.72))!important;
  box-shadow:0 5px 14px rgba(2,132,199,.055)!important;
}}
.sidebar-timer-big {{
  font-weight:950!important;
  font-size:1.10rem!important;
  letter-spacing:.04em!important;
  color:#0f172a!important;
}}

@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(5px); }}
  to {{ opacity:1; transform:translateY(0); }}
}}

@media(max-width:430px) {{
  .main .block-container {{
    max-width:100vw!important;
    width:100vw!important;
    min-width:0!important;
    padding:0.28rem!important;
    margin-left:0!important;
    margin-right:0!important;
  }}

  html, body, [class*="css"],
  p, li, label, span, div, small,
  .stMarkdown, .stMarkdown * {{
    font-size:10.8px!important;
    line-height:1.24!important;
  }}

  /* Phone fix: Streamlit normally stacks every st.columns() item into one long vertical list.
     Keep metric/button rows as a compact grid so phone mode still feels like laptop mode. */
  div[data-testid="stHorizontalBlock"] {{
    display:grid!important;
    grid-template-columns:repeat(auto-fit, minmax(104px, 1fr))!important;
    gap:.28rem!important;
    align-items:stretch!important;
    width:100%!important;
  }}

  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
    width:100%!important;
    min-width:0!important;
    flex:unset!important;
    padding-left:0!important;
    padding-right:0!important;
  }}

  div[data-testid="metric-container"] {{
    min-height:72px!important;
    overflow:hidden!important;
  }}

  div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    white-space:normal!important;
    overflow-wrap:anywhere!important;
  }}

  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    white-space:normal!important;
    overflow-wrap:anywhere!important;
    line-height:1.05!important;
  }}

  h1 {{
    font-size:1rem!important;
    line-height:1.12!important;
  }}

  h2 {{
    font-size:.88rem!important;
    line-height:1.12!important;
  }}

  h3 {{
    font-size:.80rem!important;
    line-height:1.12!important;
  }}

  .stButton>button {{
    min-height:33px!important;
    font-size:9.8px!important;
    padding:4px 6px!important;
    border-radius:12px!important;
  }}

  div[data-testid="metric-container"] {{
    padding:7px!important;
    border-radius:12px!important;
  }}

  div[data-testid="metric-container"] label {{
    font-size:9.3px!important;
  }}

  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size:16px!important;
  }}

  .stTabs [data-baseweb="tab"] {{
    font-size:8.8px!important;
    padding:4px 5px!important;
    min-height:26px!important;
  }}

  .ocean-card,
  .glass-card,
  .inner-glass,
  .card,
  .profile-glass,
  .alert-card,
  .status-card,
  .regime-card {{
    padding:7px!important;
    border-radius:12px!important;
  }}

  section[data-testid="stSidebar"] {{
    width:230px!important;
    min-width:230px!important;
  }}

  div[data-testid="column"] {{
    padding-left:0.10rem!important;
    padding-right:0.10rem!important;
  }}

  .block-container > div {{
    max-width:100%!important;
  }}
}}

@media(max-width:380px) {{
  .main .block-container {{
    max-width:360px!important;
    width:100%!important;
    min-width:0!important;
    padding:0.34rem!important;
  }}

  html, body, [class*="css"],
  p, li, label, span, div, small,
  .stMarkdown, .stMarkdown * {{
    font-size:9.4px!important;
  }}

  .stButton>button {{
    min-height:31px!important;
    font-size:9.3px!important;
  }}
}}


/* === 2026 UI/UX full upgrade: universal page shell, stronger mobile grid, safer readability === */
.qx-page-head {{
  display:flex!important;
  align-items:stretch!important;
  justify-content:space-between!important;
  gap:.65rem!important;
  margin:.35rem 0 .45rem 0!important;
  padding:12px 13px!important;
  border-radius:22px!important;
  background:linear-gradient(135deg, rgba(255,255,255,.90), rgba(224,242,254,.72))!important;
  border:1px solid rgba(14,116,144,.16)!important;
  box-shadow:0 12px 32px rgba(2,132,199,.09), inset 0 1px 0 rgba(255,255,255,.86)!important;
  backdrop-filter:blur(22px) saturate(180%)!important;
}}
.qx-title-wrap {{ min-width:0!important; }}
.qx-kicker {{
  color:#075985!important;
  font-weight:900!important;
  letter-spacing:.08em!important;
  text-transform:uppercase!important;
  font-size:10px!important;
  margin-bottom:2px!important;
}}
.qx-title {{
  color:#0f172a!important;
  font-weight:950!important;
  font-size:1.38rem!important;
  line-height:1.05!important;
  letter-spacing:-.03em!important;
}}
.qx-subtitle {{
  color:#475569!important;
  font-size:11px!important;
  font-weight:750!important;
  margin-top:4px!important;
  overflow-wrap:anywhere!important;
}}
.qx-status {{
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  min-width:118px!important;
  border-radius:18px!important;
  padding:9px 12px!important;
  font-size:10px!important;
  font-weight:950!important;
  letter-spacing:.04em!important;
  text-align:center!important;
  border:1px solid rgba(15,23,42,.08)!important;
}}
.qx-ok {{ background:rgba(220,252,231,.86)!important; color:#166534!important; box-shadow:0 0 0 5px rgba(22,163,74,.08)!important; }}
.qx-off {{ background:rgba(254,226,226,.86)!important; color:#991b1b!important; box-shadow:0 0 0 5px rgba(220,38,38,.06)!important; }}
.qx-strip {{
  display:grid!important;
  grid-template-columns:repeat(4, minmax(0, 1fr))!important;
  gap:.42rem!important;
  margin:.25rem 0 .65rem 0!important;
}}
.qx-strip > div {{
  min-width:0!important;
  border-radius:17px!important;
  padding:9px 10px!important;
  background:rgba(255,255,255,.76)!important;
  border:1px solid rgba(14,116,144,.12)!important;
  box-shadow:0 5px 16px rgba(2,132,199,.055)!important;
}}
.qx-strip b {{
  display:block!important;
  color:#075985!important;
  font-size:9.6px!important;
  font-weight:950!important;
  margin-bottom:2px!important;
}}
.qx-strip span {{
  display:block!important;
  color:#0f172a!important;
  font-size:11px!important;
  font-weight:850!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}}
.qx-empty {{
  border-radius:18px!important;
  padding:10px 12px!important;
  margin:.25rem 0 .65rem 0!important;
  background:linear-gradient(135deg, rgba(255,255,255,.88), rgba(254,243,199,.62))!important;
  border:1px solid rgba(217,119,6,.20)!important;
  color:#78350f!important;
  box-shadow:0 6px 18px rgba(217,119,6,.06)!important;
}}
.qx-empty b {{ font-weight:950!important; }}
.qx-empty span {{ font-weight:700!important; }}

/* Better visual hierarchy for native Streamlit alerts */
div[data-testid="stAlert"] {{
  border-radius:18px!important;
  border:1px solid rgba(14,116,144,.14)!important;
  box-shadow:0 5px 16px rgba(2,132,199,.055)!important;
}}

/* Form widgets: easier tap targets without giant vertical whitespace */
div[data-baseweb="select"] > div,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {{
  min-height:36px!important;
}}

/* Tables: compact but readable */
[data-testid="stDataFrame"] {{ box-shadow:0 6px 18px rgba(2,132,199,.055)!important; }}

@media(max-width:760px) {{
  .qx-page-head {{
    display:grid!important;
    grid-template-columns:1fr!important;
    padding:10px!important;
    border-radius:18px!important;
    gap:.45rem!important;
  }}
  .qx-title {{ font-size:1.12rem!important; }}
  .qx-status {{ min-width:0!important; min-height:34px!important; }}
  .qx-strip {{ grid-template-columns:repeat(2, minmax(0, 1fr))!important; gap:.34rem!important; }}
  .qx-strip > div {{ padding:8px!important; border-radius:14px!important; }}
}}

@media(max-width:430px) {{
  .qx-page-head {{ margin:.18rem 0 .32rem 0!important; padding:8px!important; border-radius:15px!important; }}
  .qx-kicker {{ font-size:8.8px!important; }}
  .qx-title {{ font-size:1.0rem!important; }}
  .qx-subtitle {{ font-size:9.5px!important; }}
  .qx-status {{ font-size:8.8px!important; border-radius:12px!important; min-height:30px!important; padding:6px!important; }}
  .qx-strip {{ grid-template-columns:repeat(2, minmax(0, 1fr))!important; margin:.18rem 0 .44rem 0!important; }}
  .qx-strip b {{ font-size:8.7px!important; }}
  .qx-strip span {{ font-size:9.5px!important; }}
  .qx-empty {{ padding:8px!important; border-radius:14px!important; }}

  /* Force metric cards close to square on phone; avoids long vertical one-by-one feel. */
  div[data-testid="metric-container"] {{
    min-height:78px!important;
    display:flex!important;
    flex-direction:column!important;
    justify-content:space-between!important;
  }}

  /* Streamlit columns in nested panels should still be a grid, but never overflow sideways. */
  div[data-testid="stHorizontalBlock"] {{
    grid-template-columns:repeat(auto-fit, minmax(96px, 1fr))!important;
    gap:.24rem!important;
  }}
}}


/* === 2026 System Relationship + Timing layer === */
.rel-card {{
  background:linear-gradient(135deg, rgba(255,255,255,.90), rgba(224,242,254,.72))!important;
  border:1px solid rgba(14,116,144,.16)!important;
  border-radius:22px!important;
  padding:11px 12px!important;
  margin:.30rem 0 .60rem 0!important;
  box-shadow:0 10px 28px rgba(2,132,199,.08)!important;
  backdrop-filter:blur(20px) saturate(170%)!important;
}}
.rel-title {{
  font-weight:950!important;
  color:#075985!important;
  margin-bottom:8px!important;
}}
.rel-grid {{
  display:grid!important;
  grid-template-columns:repeat(4, minmax(0, 1fr))!important;
  gap:.42rem!important;
}}
.rel-grid > div {{
  min-width:0!important;
  background:rgba(255,255,255,.74)!important;
  border:1px solid rgba(14,116,144,.12)!important;
  border-radius:16px!important;
  padding:8px!important;
  box-shadow:0 5px 14px rgba(2,132,199,.045)!important;
}}
.rel-grid b {{
  display:block!important;
  color:#075985!important;
  font-size:9.5px!important;
  font-weight:950!important;
}}
.rel-grid span {{
  display:block!important;
  color:#334155!important;
  font-size:9.5px!important;
  font-weight:750!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}}
.rel-badge {{
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  margin-top:5px!important;
  padding:3px 7px!important;
  border-radius:999px!important;
  font-size:8.4px!important;
  font-weight:950!important;
  letter-spacing:.03em!important;
}}
.rel-ok {{ background:rgba(220,252,231,.92)!important; color:#166534!important; }}
.rel-warn {{ background:rgba(254,243,199,.92)!important; color:#92400e!important; }}
.rel-bad {{ background:rgba(254,226,226,.92)!important; color:#991b1b!important; }}
.rel-info {{ background:rgba(224,242,254,.92)!important; color:#075985!important; }}
.rel-mini {{
  border-radius:15px!important;
  padding:8px!important;
  margin:.28rem 0!important;
  background:linear-gradient(135deg, rgba(255,255,255,.86), rgba(224,242,254,.66))!important;
  border:1px solid rgba(14,116,144,.13)!important;
  box-shadow:0 5px 13px rgba(2,132,199,.05)!important;
}}
.rel-mini b {{ color:#075985!important; font-weight:950!important; }}
.rel-mini small {{ color:#334155!important; font-weight:750!important; }}
@media(max-width:760px) {{
  .rel-grid {{ grid-template-columns:repeat(2, minmax(0, 1fr))!important; }}
  .rel-card {{ border-radius:18px!important; padding:9px!important; }}
}}
@media(max-width:430px) {{
  .rel-grid {{ grid-template-columns:repeat(2, minmax(0, 1fr))!important; gap:.28rem!important; }}
  .rel-grid > div {{ min-height:78px!important; border-radius:13px!important; padding:7px!important; }}
  .rel-grid b, .rel-grid span {{ font-size:8.7px!important; }}
  .rel-badge {{ font-size:7.8px!important; padding:3px 6px!important; }}
}}

</style>
""",
        unsafe_allow_html=True,
    )


def auto_close_sidebar_script():
    st.markdown(
        r"""
<script>
function closeStreamlitSidebar(){
 const doc = window.parent.document;
 const buttons = Array.from(doc.querySelectorAll('button'));
 const closeBtn = buttons.find(b =>
   (b.getAttribute('aria-label') || '').toLowerCase().includes('close sidebar')
 );
 if(closeBtn){
   setTimeout(() => closeBtn.click(), 80);
 }
}

window.addEventListener('message', (e) => {
 if(e.data === 'close-sidebar') closeStreamlitSidebar();
});
</script>
""",
        unsafe_allow_html=True,
    )


def request_close_sidebar():
    st.markdown(
        "<script>window.parent.postMessage('close-sidebar','*');</script>",
        unsafe_allow_html=True,
    )


def status_badge(text, kind="info"):
    kind = str(kind or "info").lower()

    cls = {
        "buy": "badge-buy",
        "sell": "badge-sell",
        "wait": "badge-wait",
        "neutral": "badge-neutral",
        "danger": "badge-danger",
        "warning": "badge-warning",
        "info": "badge-info",
    }.get(kind, "badge-info")

    st.markdown(f'<span class="{cls}">{text}</span>', unsafe_allow_html=True)


def ocean_card(title="", body="", kind="status"):
    cls = {
        "alert": "alert-card",
        "regime": "regime-card",
        "status": "status-card",
    }.get(str(kind or "status").lower(), "status-card")

    st.markdown(
        f"""
        <div class="{cls}">
            <b>{title}</b><br>
            <span>{body}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_style(phone_mode: bool = False):
    apply_global_styles(phone_mode=phone_mode)


def apply_style(phone_mode: bool = False):
    apply_global_styles(phone_mode=phone_mode)