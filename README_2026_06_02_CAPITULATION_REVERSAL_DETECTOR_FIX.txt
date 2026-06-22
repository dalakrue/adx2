CAPITULATION REVERSAL DETECTOR FIX
==================================

This patch fixes the reported Finder case:
- 2026-06-01 16:00 showed a strong SELL candle / SELL trend.
- After that, price reversed upward into the end of the day.
- The previous 10-point engine showed NORMAL 4/10 because thresholds were too strict:
  * Sell→Buy Flip required after_buy >= 45 only.
  * Trust Confirmation required after_trust >= 80 only.
  * Reversal Strength required weighted score >= 70 only.
  * No specific rule existed for SELL capitulation + rebound.

What changed:
1. Sell→Buy Flip now catches capitulation rebound when before_sell >= 55 and after_buy >= 40.
2. Rising Efficiency card now also catches SELL exhaustion when seller dominance weakens after a fat-tail shock.
3. Fat Tail Z now triggers on either delta fat-tail expansion or after_fat_tail_z >= 1.0.
4. Buy Ratio Increase now catches recovery above 40% after seller dominance.
5. Sell Ratio Decrease now catches seller weakness near/under 60% after >60% seller dominance.
6. Trust Confirmation now accepts after_trust >= 50 when trust is improving by at least 3 points.
7. Reversal Strength now uses >=60 as early-warning threshold, with an extra capitulation-reversal boost.

Expected effect for the exported 2026-06-01 16:00 data:
- Old: 4/10 NORMAL
- New: 7+/10 WARNING/DANGER early reversal setup

This does not remove the old 10 metrics. It improves the thresholds so the detector catches one-hour SELL capitulation followed by reversal instead of waiting too late.
