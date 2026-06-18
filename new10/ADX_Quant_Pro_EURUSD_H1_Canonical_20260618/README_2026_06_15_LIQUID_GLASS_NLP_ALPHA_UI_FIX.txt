2026-06-15 Liquid Glass NLP Alpha/Delta UI Fix
================================================

Main changes
------------
1. Liquid Glass UI layer added with normal Streamlit/CSS only.
2. Native Streamlit sidebar is hidden/backup by default.
3. Primary navigation/control is the session_state Liquid Glass drawer opened from the top Menu button.
4. Home top controls are compact: Menu, Run All, Copy Short, Copy Full.
5. Connector/timer/settings controls are moved into the drawer so they do not duplicate above tab-choice buttons.
6. Central copy engine remains the only copy system and keeps download fallback.
7. AI Assistant final UI answers directly from st.chat_input Enter and from choice-box selection.
8. No required Analysis button in the final AI Assistant UI.
9. AI Assistant has Chat, Local NLP, Data Mining, Deep Analysis, History.
10. Local NLP pipeline added: normalization, tokenization, stopword removal, stemming, lemmatization, POS tagging, dependency parsing, constituency parsing, NER, WSD, coreference resolution, mention/entity/relation extraction, topic detection, summarization, text generation.
11. Same lightweight NLP pipeline is added to Research/Home NLP areas.
12. PowerBI projection display now includes blue-vs-red alpha/delta/data-point diagnostics using existing projection path values.
13. Regime projection display includes alpha/delta/data-point diagnostics using existing regime path values.
14. Run All is a low-RAM gate that sets existing section run flags but does not auto-run heavy calculations on app open.

Safety
------
- No external API was added.
- No heavy deep-learning model was added.
- Trading formulas and ML prediction engines were not replaced.
- Alpha/delta/data-point panels are display-only diagnostics.
- AI Assistant bias thresholds affect only local assistant explanation wording, not the trading engines.

Validation
----------
- python -m compileall passed after patching.
