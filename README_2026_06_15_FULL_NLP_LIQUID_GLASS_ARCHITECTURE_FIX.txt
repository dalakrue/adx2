FULL NLP + LIQUID GLASS + ARCHITECTURE FIX — 2026-06-15

What was fixed/added:
1. Research NLP inner tab now shows the full lightweight local NLP pipeline even before heavy Research run.
2. AI Assistant already uses Enter-to-answer and choice-box auto-answer; 1200+ prepared patterns are preserved and every pattern has an answer_rule.
3. NLP pipeline includes tokenization, stemming, lemmatization, stopword removal, normalization, POS, dependency parsing, constituency parsing, NER/entity extraction, trading entry extraction, WSD, coreference, mention extraction, relation extraction, topic detection, summarization, and text generation.
4. Liquid Glass App Drawer is the primary sidebar replacement. Native Streamlit sidebar remains hidden/backup only, preventing stuck open/close conflicts.
5. Duplicate top status/command sections are hidden by default. Only ⋮ Menu, Run All, Copy Short, Copy Full remain above tabs. Extra status/health/architecture panels live inside the drawer.
6. Run All stays before the two copy buttons and enables existing run-gated sections in low-RAM mode.
7. PowerBI and Regime alpha/delta data point tables now explicitly calculate blue-vs-red difference, ratio, divergence mean, Alpha Now, Alpha Prev, Alpha Difference Now-Prev, Alpha Ratio Now/Prev, Alpha Divergence Mean Now-Prev, Delta Point, and Data Point Score.
8. Future upgrade/downgrade architecture registry added at core/upgrade_architecture_20260615.py and shown inside the drawer.

Preserved:
- No trading logic was deleted.
- No new prediction engine was added.
- No external AI API was added.
- Existing PowerBI, ML, regime, KNN/Greedy, copy/export and history functions are preserved.
