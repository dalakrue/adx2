# Future Upgrade / Downgrade / Current-Fix Architecture — 2026-06-15

This patch separates the system into stable UI/control layers so future changes do not break navigation, copy, NLP, or trading calculations.

## 1. Stable shell layer
- `ui/liquid_glass_theme_20260615.py` contains liquid-glass CSS only.
- `ui/home_master_control_bar_20260615.py` is now a compact top rail with `☰ Menu`, `Run All`, `Copy Short`, and `Copy Full`.
- `ui/main_menu_drawer.py` is the real app drawer. It contains Menu, Connector, Timer, Copy, and UI/Sidebar controls.
- Native Streamlit sidebar is backup only and hidden by default through `ui/sidebar_hard_lock.py`.

## 2. Copy layer
- `ui/copy_tools.py` is the central copy engine.
- Clipboard and download fallback are both shown.
- No fake “preserved copy” messages should be added again.

## 3. NLP layer
- `core/nlp_lightweight_20260615.py` is local and rule-based.
- It supports tokenization, stemming, lemmatization, stopword removal, text normalization, POS tagging, dependency parsing, constituency parsing, NER, WSD, coreference, mention/entity/relation extraction, topic detection, summarization, and text generation seed.
- It does not download models and does not call external APIs.

## 4. Projection diagnostic layer
- `core/alpha_delta_points_20260615.py` calculates data-point diagnostics between blue path and red path:
  - Difference
  - Ratio
  - Divergence mean
  - Alpha now
  - Alpha previous
  - Delta point
  - Data point score
- This is display-only and does not replace PowerBI, ML, or regime logic.

## 5. Future upgrade rule
Add new UI features as separate files first, then import defensively. Do not edit trading formulas directly unless the change is explicitly about formulas.

## 6. Future downgrade rule
To downgrade the visual shell, disable imports in `core/app/runner.py` for the new UI file, or remove the drawer call. Trading calculations remain untouched.

## 7. Low RAM rule
Run All only sets session-state gates. Heavy sections still calculate in their existing original sections and can remain cached.
