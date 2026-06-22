2026-06-14 FINAL THREE-CENTER REGIME/AI UPGRADE

Base: uploaded last working ZIP.

What changed:
1. Lunch/Home visible UI is wrapped into exactly three main open/close sections:
   - 📂 Open / Close — Full Metric Details + History
   - 📈 Open / Close — Synced PowerBI Price Projection + Actual vs Error
   - 🧠 Open / Close — Master Decision + Reliability + Priority Center

2. Master Decision + Reliability + Priority Center now shows compact cards for:
   - Decision Control Panel
   - System Trust Center
   - Dynamic Entry Priority Center
   - Regime Sync Snapshot

3. Regime inner tab is rebuilt as Regime Intelligence Center:
   - Top summary only
   - Regime Sync Resolver
   - 25-Day Major Regime History Table using aggregated regime periods
   - Hourly/legacy regime detail is only inside Advanced Details

4. AI Assistant is simplified into AI Assistant Intelligence Center:
   - One question input box
   - One question selector
   - One Analyze button
   - One result output box
   - Uses existing local NLP, fuzzy matching, question patterns, history matching, regime/priority/reliability context only

5. Copy Short / Copy Full are extended with:
   - Decision Control Panel
   - System Trust Center
   - Dynamic Entry Priority Center
   - Regime Sync Snapshot
   - Regime Intelligence summary
   - AI Assistant answer summary when available

Validation:
- Python compileall passed.
- ZIP integrity tested after packaging.

Rules preserved:
- No external API added.
- No heavy model added.
- No new prediction engine added.
- Existing calculations and source renderers are preserved inside advanced expanders.
