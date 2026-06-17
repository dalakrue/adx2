FULL ERROR-FIXED BUILD — 2026-06-15

Run command:
  streamlit run adx_dashpoard.py

Main fixes included:
1. Added Streamlit compatibility layer:
   - Converts deprecated use_container_width=True/False into width='stretch'/'content'.
   - Intercepts old st.components.v1.html calls and routes them to the newer iframe path when available.
   - Prevents old preserved modules from producing warning spam while keeping existing calculations intact.

2. Cleaned entry files:
   - app.py, main.py, and adx_dashpoard.py are now simple safe entrypoints.
   - Removed old top-level sidebar-hiding CSS from entrypoints to avoid page-config and sidebar conflicts.

3. Sidebar/UI architecture:
   - Main navigation uses the existing Liquid Glass three-dot drawer.
   - Connector, timer, copy, UI/sidebar controls are independent drawer sections.
   - Native Streamlit sidebar is backup-only and no longer fights the main drawer.

4. NLP upgrades:
   - Lightweight local NLP pipeline is available in Research/NLP and AI Assistant inner tabs.
   - Includes tokenization, stemming, lemmatization, stopword removal, normalization, POS tagging,
     dependency parsing, constituency-style chunks, NER/entity extraction, WSD hints,
     coreference approximation, mention extraction, relation extraction, topic detection,
     summarization, and template text generation.

5. AI Assistant behavior:
   - Enter-to-answer via chat input.
   - Question choice answers immediately after selection.
   - 1000+ prepared pattern questions with answer_rule metadata.
   - BUY/SELL thresholds are less strict and WAIT is penalized to avoid oversimplified WAIT bias.

6. Alpha/Delta/Data Point logic:
   - Alpha/Delta point module calculates difference, ratio, divergence mean, alpha now/prev,
     alpha ratio, alpha difference, delta point, and data point score.
   - Integrated into PowerBI/projection and Regime/Dinner logic.

7. Low-RAM Run All control:
   - Home master control bar contains one compact Run All trigger before Copy Short and Copy Full.
   - Run flags are stored in session_state so heavy sections remain gated and low-RAM friendly.

Verification done in this sandbox:
  python -m compileall -q .
Result:
  PASS

Note:
  Streamlit itself is not installed inside the sandbox environment, so full browser UI execution could not be tested here.
  The package was syntax-checked and structurally patched for Streamlit runtime compatibility.
