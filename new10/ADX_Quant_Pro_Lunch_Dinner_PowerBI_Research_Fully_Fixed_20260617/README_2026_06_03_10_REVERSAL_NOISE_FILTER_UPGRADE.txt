10 REVERSAL NOISE FILTER UPGRADE - 2026-06-03

Problem fixed:
- Home and Finder could show 7/10 too easily because the old capitulation rule could auto-lift partial evidence to danger level.
- This created noisy false alerts where only a few real confirmation groups existed.

What changed:
1. Added strict reversal confirmation gate:
   - Needs at least 2 primary confirmations from direction rotation, shock move, side flip/recovery.
   - Needs tail confirmation from fat-tail or kurtosis.
   - Needs flow confirmation from efficiency/participation/pressure weakness.
   - Needs model confirmation from trust or DVE.

2. Replaced unsafe auto-lift:
   - Old: capitulation pattern could force weak setup to 7/10.
   - New: only strong capitulation + opposite-side confirmation + raw >=6 can lift to 7/10.

3. Added noise filter output:
   - raw_drivers shows how many raw drivers fired.
   - 10_reverse_decision shows the confirmed score after noise filtering.
   - noise_filter explains PASS, WATCH, or BLOCKED.

4. Both Home and Finder use the same patched evaluator, so their decision logic stays synchronized.

Files changed:
- tabs/home_split/reversal_engine_full_correct_patch.py
- tabs/home_split/home_finder_reversal_history_upgrade.py

Original code is not deleted. This remains a non-destructive runtime patch.
