"""Central copy/download engine for the 2026-06-15 UI stability upgrade.

Every visible copy button should route here.  The clipboard action uses a
self-contained Streamlit component and does not depend on the app/sidebar DOM.
A download fallback is always rendered so phone/browser clipboard blocking never
looks like a fake successful copy.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from typing import Any

import streamlit as st


def _safe_key(key: str) -> str:
    raw = str(key or "copy")
    return re.sub(r"[^A-Za-z0-9_-]", "_", raw)[:80] or "copy"


def _file_name(label: str, key: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", str(label or key or "copy")).strip("_")[:42]
    if not base:
        base = "copy_payload"
    digest = hashlib.sha1(str(key).encode("utf-8", "ignore")).hexdigest()[:7]
    return f"{base}_{digest}.txt"


def central_copy_button(label: str, text: Any, key: str, *, height: int = 92, show_fallback: bool = True) -> None:
    import streamlit.components.v1 as components

    safe_key = _safe_key(key)
    safe_label = html.escape(str(label or "Copy"))
    payload = str(text or "")
    text_json = json.dumps(payload)
    st.session_state[f"central_copy_payload_{safe_key}"] = payload
    components.html(
        f"""
<style>
*{{box-sizing:border-box}}body{{margin:0;background:transparent;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;}}
.new7-copy-wrap{{width:100%;padding:1px 0 0}}
.new7-copy-btn{{width:100%;min-height:50px;border-radius:18px;border:1px solid rgba(14,116,144,.22);cursor:pointer;font-weight:950;color:#fff;font-size:14px;line-height:1.12;background:radial-gradient(circle at 12% 8%,rgba(255,255,255,.42),transparent 24%),linear-gradient(135deg,#0284c7,#06b6d4 54%,#14b8a6);box-shadow:0 14px 30px rgba(2,132,199,.20),inset 0 1px 0 rgba(255,255,255,.42);touch-action:manipulation;-webkit-tap-highlight-color:transparent;user-select:none;}}
.new7-copy-btn:active{{transform:scale(.985)}}.new7-copy-status{{min-height:18px;text-align:center;color:#075985;margin-top:5px;font-size:12px;font-weight:900}}
@media(max-width:520px){{.new7-copy-btn{{min-height:54px;font-size:13px;padding:8px 6px}}.new7-copy-status{{font-size:11px}}}}
</style>
<div class="new7-copy-wrap">
  <button class="new7-copy-btn" id="new7_copy_{safe_key}" type="button">📋 {safe_label}</button>
  <textarea id="new7_copy_text_{safe_key}" readonly style="position:fixed;left:-9999px;top:-9999px;width:1px;height:1px;opacity:.01;"></textarea>
  <div class="new7-copy-status" id="new7_copy_status_{safe_key}">Ready • fallback download below</div>
</div>
<script>(function(){{
 const btn=document.getElementById('new7_copy_{safe_key}');
 const ta=document.getElementById('new7_copy_text_{safe_key}');
 const status=document.getElementById('new7_copy_status_{safe_key}');
 const txt={text_json}; ta.value=txt; let busy=false;
 async function copyNow(e){{
   if(e){{e.preventDefault();e.stopPropagation();}}
   if(busy) return; busy=true; let ok=false;
   try{{ if(navigator.clipboard && window.isSecureContext){{ await navigator.clipboard.writeText(txt); ok=true; }} }}catch(err){{ ok=false; }}
   if(!ok){{ try{{ ta.style.left='0px';ta.style.top='0px';ta.style.width='2px';ta.style.height='2px';ta.focus();ta.select();ta.setSelectionRange(0,ta.value.length); ok=document.execCommand('copy'); ta.blur(); ta.style.left='-9999px'; ta.style.top='-9999px'; }}catch(err){{ ok=false; }} }}
   status.textContent = ok ? 'Copied ✅ Paste now.' : 'Browser blocked copy — use Download/Text fallback.';
   if(ok){{ const old=btn.textContent; btn.textContent='✅ Copied'; setTimeout(function(){{btn.textContent=old;}},1200); }}
   setTimeout(function(){{busy=false;}},320);
 }}
 btn.addEventListener('click', copyNow, {{passive:false}});
 btn.addEventListener('pointerup', copyNow, {{passive:false}});
 btn.addEventListener('touchend', copyNow, {{passive:false}});
}})();</script>
        """,
        height=height,
    )
    if show_fallback:
        dl_cols = st.columns([1, 1])
        with dl_cols[0]:
            st.download_button(
                "⬇️ Download fallback",
                data=payload,
                file_name=_file_name(label, safe_key),
                mime="text/plain",
                key=f"download_fallback_{safe_key}",
                use_container_width=True,
            )
        with dl_cols[1]:
            with st.expander("Manual text fallback", expanded=False):
                st.text_area("Long-press / select all if browser copy is blocked", payload, height=160, key=f"textarea_fallback_{safe_key}")


def copy_fallback_script(text: str, key: str = "copy_fallback") -> None:
    central_copy_button("Copy", text, key, show_fallback=True)
