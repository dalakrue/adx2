2026-06-03 STRICT NOISE-GATED 10 REVERSAL UPGRADE
===================================================

What changed
------------
The 10-point reversal detector now uses a strict final gate before allowing a 7/10+ danger score:

    raw_active_count >= 7
    trend_exhaustion == True
    pressure_transfer == True
    shock_move == True
    low_volume_noise == False

Safe scoring ladder
-------------------
- Raw 7/10 but no exhaustion: capped at 6/10
- Raw 7/10 + exhaustion only: capped at 6/10
- Raw 7/10 + exhaustion + pressure transfer: 7/10 transition warning only if not low-volume noise
- Raw 8/10 + exhaustion + pressure transfer + shock: 8/10 danger
- Strong opposite-side confirmation after peak: 8-9/10

Where it applies
----------------
- Home current reversal score
- Home 25D reversal history scan table
- Finder day-only hourly reversal replay
- Finder strongest-hour driver table
- Copy/export payloads include the new gate columns

New visible columns/fields
--------------------------
- strict_gate_valid
- trend_exhaustion
- pressure_transfer
- shock_move
- low_volume_noise
- noise_filter

Purpose
-------
This catches trend-stop / transition reversal windows like 09:00-15:00, but prevents every noisy 6/10-8/10 cluster from becoming a 7/10 danger alert.
