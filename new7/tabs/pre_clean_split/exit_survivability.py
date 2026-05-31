import math
import time
import pandas as pd
import streamlit as st

from .utils import safe_rerun

def _exit_s(x, default=0.0):
    try:
        if x is None:
            return float(default)
        if isinstance(x, str) and x.strip() == "":
            return float(default)
        return float(x)
    except Exception:
        return float(default)

def _clamp(x, low=0.0, high=100.0):
    try:
        x = float(x)
    except Exception:
        x = 0.0
    return max(float(low), min(float(high), x))

def _softmax3(a, b, c):
    m = max(float(a), float(b), float(c))
    ea = math.exp(max(-60, min(60, float(a) - m)))
    eb = math.exp(max(-60, min(60, float(b) - m)))
    ec = math.exp(max(-60, min(60, float(c) - m)))
    total = ea + eb + ec

    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3

    return ea / total, eb / total, ec / total

def exit_survivability_tab():
    """
    FULL Exit Survivability inner tab.
    Paste this whole function over your old exit_survivability_tab().
    """

    st.markdown("# 🔥 EXIT SURVIVABILITY ENGINE")
    st.caption(
        "Hold Decision • Momentum Decay • Exhaustion Detection • Liquidity Trap • "
        "Edge Quality • Adaptive Exit Probability"
    )

    # =====================================================
    # STYLE
    # =====================================================
    st.markdown(
        """
        <style>
        .exit-card {
            background: linear-gradient(135deg, rgba(239,246,255,.95), rgba(248,250,252,.98));
            border: 1px solid #DCE7F7;
            border-radius: 16px;
            padding: 14px;
            margin: 8px 0 12px 0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, .06);
        }
        .exit-title {
            font-size: 18px;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .exit-sub {
            font-size: 12px;
            color: #475569;
            line-height: 1.45;
        }
        .danger-box {
            background: linear-gradient(135deg,#FEE2E2,#FECACA);
            border: 1px solid #FCA5A5;
            border-radius: 14px;
            padding: 12px;
            color: #7F1D1D;
            font-weight: 800;
            text-align: center;
        }
        .good-box {
            background: linear-gradient(135deg,#DCFCE7,#BBF7D0);
            border: 1px solid #86EFAC;
            border-radius: 14px;
            padding: 12px;
            color: #14532D;
            font-weight: 800;
            text-align: center;
        }
        .warn-box {
            background: linear-gradient(135deg,#FEF3C7,#FDE68A);
            border: 1px solid #FBBF24;
            border-radius: 14px;
            padding: 12px;
            color: #78350F;
            font-weight: 800;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # CLEAR FUNCTION
    # =====================================================
    def clear_exit_inputs():
        keys = [
            "exit_y_madx", "exit_y_plus", "exit_y_minus", "exit_y_atr",
            "exit_today_madx", "exit_today_plus", "exit_today_minus", "exit_today_atr",
            "exit_h1_madx", "exit_h1_plus", "exit_h1_minus", "exit_h1_atr",
            "exit_h2_madx", "exit_h2_plus", "exit_h2_minus", "exit_h2_atr",
            "exit_prev2_madx", "exit_prev2_plus", "exit_prev2_minus", "exit_prev2_atr",
            "exit_now2_madx", "exit_now2_plus", "exit_now2_minus", "exit_now2_atr",
            "exit_trade_direction",
            "exit_position_age_bars",
            "exit_entry_quality",
            "exit_risk_mode",
        ]

        for k in keys:
            if k in st.session_state:
                del st.session_state[k]

        safe_rerun()

    top_clear, top_info = st.columns([1, 4])

    with top_clear:
        if st.button(
            "🗑️ CLEAR EXIT INPUTS",
            type="secondary",
            use_container_width=True,
            key="exit_clear_all_full",
        ):
            clear_exit_inputs()

    with top_info:
        st.markdown(
            """
            <div class="exit-card">
                <div class="exit-title">Position survival dashboard</div>
                <div class="exit-sub">
                    Fill Daily, H4, and 2H values. This engine estimates HOLD, TRAIL,
                    PARTIAL EXIT, FULL EXIT, or EMERGENCY EXIT.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # =====================================================
    # INPUTS
    # =====================================================
    st.markdown("## 📥 Market Structure Inputs")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Yesterday")

        y_madx = st.number_input(
            "Yesterday MADX",
            value=None,
            key="exit_y_madx",
            step=0.1,
            format="%.2f",
        )
        y_plus = st.number_input(
            "Yesterday +DI",
            value=None,
            key="exit_y_plus",
            step=0.1,
            format="%.2f",
        )
        y_minus = st.number_input(
            "Yesterday -DI",
            value=None,
            key="exit_y_minus",
            step=0.1,
            format="%.2f",
        )
        y_atr = st.number_input(
            "Yesterday ATR",
            value=None,
            key="exit_y_atr",
            step=0.1,
            format="%.2f",
        )

        st.markdown("### Today Daily")

        today_madx = st.number_input(
            "Today MADX",
            value=None,
            key="exit_today_madx",
            step=0.1,
            format="%.2f",
        )
        today_plus = st.number_input(
            "Today +DI",
            value=None,
            key="exit_today_plus",
            step=0.1,
            format="%.2f",
        )
        today_minus = st.number_input(
            "Today -DI",
            value=None,
            key="exit_today_minus",
            step=0.1,
            format="%.2f",
        )
        today_atr = st.number_input(
            "Today ATR",
            value=None,
            key="exit_today_atr",
            step=0.1,
            format="%.2f",
        )

    with col2:
        st.markdown("### Previous H4 Block")

        h1_madx = st.number_input(
            "Prev H4 MADX",
            value=None,
            key="exit_h1_madx",
            step=0.1,
            format="%.2f",
        )
        h1_plus = st.number_input(
            "Prev H4 +DI",
            value=None,
            key="exit_h1_plus",
            step=0.1,
            format="%.2f",
        )
        h1_minus = st.number_input(
            "Prev H4 -DI",
            value=None,
            key="exit_h1_minus",
            step=0.1,
            format="%.2f",
        )
        h1_atr = st.number_input(
            "Prev H4 ATR",
            value=None,
            key="exit_h1_atr",
            step=0.1,
            format="%.2f",
        )

        st.markdown("### Current H4 Block")

        h2_madx = st.number_input(
            "Current H4 MADX",
            value=None,
            key="exit_h2_madx",
            step=0.1,
            format="%.2f",
        )
        h2_plus = st.number_input(
            "Current H4 +DI",
            value=None,
            key="exit_h2_plus",
            step=0.1,
            format="%.2f",
        )
        h2_minus = st.number_input(
            "Current H4 -DI",
            value=None,
            key="exit_h2_minus",
            step=0.1,
            format="%.2f",
        )
        h2_atr = st.number_input(
            "Current H4 ATR",
            value=None,
            key="exit_h2_atr",
            step=0.1,
            format="%.2f",
        )

    st.markdown("### 2H Micro Structure")

    mcol1, mcol2 = st.columns(2)

    with mcol1:
        st.markdown("**Previous 2H**")

        prev2_madx = st.number_input(
            "Prev 2H MADX",
            value=None,
            key="exit_prev2_madx",
            step=0.1,
            format="%.2f",
        )
        prev2_plus = st.number_input(
            "Prev 2H +DI",
            value=None,
            key="exit_prev2_plus",
            step=0.1,
            format="%.2f",
        )
        prev2_minus = st.number_input(
            "Prev 2H -DI",
            value=None,
            key="exit_prev2_minus",
            step=0.1,
            format="%.2f",
        )
        prev2_atr = st.number_input(
            "Prev 2H ATR",
            value=None,
            key="exit_prev2_atr",
            step=0.1,
            format="%.2f",
        )

    with mcol2:
        st.markdown("**Current 2H**")

        now2_madx = st.number_input(
            "Now 2H MADX",
            value=None,
            key="exit_now2_madx",
            step=0.1,
            format="%.2f",
        )
        now2_plus = st.number_input(
            "Now 2H +DI",
            value=None,
            key="exit_now2_plus",
            step=0.1,
            format="%.2f",
        )
        now2_minus = st.number_input(
            "Now 2H -DI",
            value=None,
            key="exit_now2_minus",
            step=0.1,
            format="%.2f",
        )
        now2_atr = st.number_input(
            "Now 2H ATR",
            value=None,
            key="exit_now2_atr",
            step=0.1,
            format="%.2f",
        )

    st.markdown("### Trade Context")

    t1, t2, t3 = st.columns(3)

    with t1:
        trade_direction = st.selectbox(
            "Your Current Trade Direction",
            ["BUY", "SELL"],
            key="exit_trade_direction",
        )

    with t2:
        position_age_bars = st.number_input(
            "Position Age / Bars Held",
            min_value=0,
            max_value=200,
            value=0,
            step=1,
            key="exit_position_age_bars",
        )

    with t3:
        entry_quality = st.selectbox(
            "Entry Quality",
            ["A+ High Conviction", "Good", "Average", "Weak"],
            index=1,
            key="exit_entry_quality",
        )

    risk_mode = st.selectbox(
        "Risk Mode",
        ["Normal", "Protect Profit", "Aggressive Hold", "Very Conservative"],
        index=0,
        key="exit_risk_mode",
    )

    # =====================================================
    # SAFE VALUES
    # =====================================================
    y_madx = _exit_s(y_madx)
    y_plus = _exit_s(y_plus)
    y_minus = _exit_s(y_minus)
    y_atr = _exit_s(y_atr)

    today_madx = _exit_s(today_madx)
    today_plus = _exit_s(today_plus)
    today_minus = _exit_s(today_minus)
    today_atr = _exit_s(today_atr)

    h1_madx = _exit_s(h1_madx)
    h1_plus = _exit_s(h1_plus)
    h1_minus = _exit_s(h1_minus)
    h1_atr = _exit_s(h1_atr)

    h2_madx = _exit_s(h2_madx)
    h2_plus = _exit_s(h2_plus)
    h2_minus = _exit_s(h2_minus)
    h2_atr = _exit_s(h2_atr)

    prev2_madx = _exit_s(prev2_madx)
    prev2_plus = _exit_s(prev2_plus)
    prev2_minus = _exit_s(prev2_minus)
    prev2_atr = _exit_s(prev2_atr)

    now2_madx = _exit_s(now2_madx)
    now2_plus = _exit_s(now2_plus)
    now2_minus = _exit_s(now2_minus)
    now2_atr = _exit_s(now2_atr)

    # =====================================================
    # CORE DERIVED VARIABLES
    # =====================================================
    daily_pressure = today_plus - today_minus
    yesterday_pressure = y_plus - y_minus

    h4_pressure_prev = h1_plus - h1_minus
    h4_pressure = h2_plus - h2_minus

    prev_micro_pressure = prev2_plus - prev2_minus
    micro_pressure = now2_plus - now2_minus

    pressure1 = h4_pressure_prev
    pressure2 = h4_pressure

    pressure_accel = pressure2 - pressure1
    micro_accel = micro_pressure - prev_micro_pressure
    daily_pressure_accel = daily_pressure - yesterday_pressure

    madx_accel = h2_madx - h1_madx
    micro_madx_accel = now2_madx - prev2_madx
    daily_madx_accel = today_madx - y_madx

    atr_accel = h2_atr - h1_atr
    micro_atr_accel = now2_atr - prev2_atr
    daily_atr_change = today_atr - y_atr

    madx_decay = h1_madx - h2_madx
    pressure_decay = h4_pressure_prev - h4_pressure
    atr_decay = h1_atr - h2_atr

    decay_velocity = h1_madx - h2_madx
    decay_acceleration = (h1_madx - h2_madx) - (today_madx - h1_madx)

    dominance1 = h1_plus / max(abs(h1_minus), 1.0)
    dominance2 = h2_plus / max(abs(h2_minus), 1.0)

    dominance_growth = dominance2 - dominance1

    pressure_variance = abs(h4_pressure - micro_pressure)
    atr_stability = _clamp(100 - abs(h2_atr - h1_atr) * 10, 0, 100)

    di_persistence = 0

    if today_plus > today_minus:
        di_persistence += 1
    if h1_plus > h1_minus:
        di_persistence += 1
    if h2_plus > h2_minus:
        di_persistence += 1
    if now2_plus > now2_minus:
        di_persistence += 1

    di_overlap = abs(now2_plus - now2_minus)
    noise_ratio = pressure_variance * 2

    micro_reversal_frequency = 0

    if prev2_plus > prev2_minus and now2_plus < now2_minus:
        micro_reversal_frequency += 1

    if prev2_plus < prev2_minus and now2_plus > now2_minus:
        micro_reversal_frequency += 1

    micro_reversals = micro_reversal_frequency

    if abs(micro_pressure) < 3:
        micro_reversals += 1

    peak_momentum = max(
        y_madx,
        today_madx,
        h1_madx,
        h2_madx,
        prev2_madx,
        now2_madx,
    )

    momentum_decay = peak_momentum - now2_madx

    if any([y_atr, today_atr, h1_atr, h2_atr, prev2_atr, now2_atr]):
        historical_atr_avg = (
            y_atr
            + today_atr
            + h1_atr
            + h2_atr
            + prev2_atr
            + now2_atr
        ) / 6
    else:
        historical_atr_avg = 0

    # =====================================================
    # BASIC DIRECTION STATE
    # =====================================================
    m1_direction = "BUY" if daily_pressure > 0 else "SELL"
    h4_direction = "BUY" if h4_pressure > 0 else "SELL"
    micro_direction = "BUY" if micro_pressure > 0 else "SELL"

    direction_alignment_count = sum(
        [
            m1_direction == trade_direction,
            h4_direction == trade_direction,
            micro_direction == trade_direction,
        ]
    )

    alignment = h4_direction == m1_direction

    # =====================================================
    # ORIGINAL DECAY / REVERSAL / PQS / SURVIVABILITY
    # =====================================================
    decay_score = 0

    if madx_decay > 2:
        decay_score += 25
    if pressure_decay > 4:
        decay_score += 30
    if atr_decay > 0.8:
        decay_score += 20
    if madx_accel < -2.5:
        decay_score += 28
    if atr_accel < -0.8:
        decay_score += 22
    if micro_pressure < 3 and trade_direction == "BUY":
        decay_score += 25
    if micro_pressure > -3 and trade_direction == "SELL":
        decay_score += 25
    if momentum_decay > 12:
        decay_score += 12
    if position_age_bars > 20 and decay_velocity > 1:
        decay_score += 8

    decay_score = _clamp(decay_score, 0, 95)

    reversal_threat = 0

    if madx_accel < -2.5:
        reversal_threat += 25
    if atr_accel < -1.0:
        reversal_threat += 22
    if abs(h4_pressure) > 15 and madx_accel < 0:
        reversal_threat += 20
    if trade_direction == "BUY" and micro_pressure < -5:
        reversal_threat += 30
    if trade_direction == "SELL" and micro_pressure > 5:
        reversal_threat += 30
    if direction_alignment_count <= 1:
        reversal_threat += 15
    if daily_pressure_accel * h4_pressure < 0:
        reversal_threat += 10

    reversal_threat = _clamp(reversal_threat, 0, 95)

    pqs = 68

    if h4_pressure > 10 and trade_direction == "BUY":
        pqs += 18
    if h4_pressure < -10 and trade_direction == "SELL":
        pqs += 18
    if madx_accel > 1.5:
        pqs += 15
    if micro_atr_accel > 0.3:
        pqs += 12
    if decay_score < 30:
        pqs += 14
    if direction_alignment_count == 3:
        pqs += 10
    if entry_quality == "A+ High Conviction":
        pqs += 8
    elif entry_quality == "Weak":
        pqs -= 10

    if decay_score > 50:
        pqs -= 25
    if reversal_threat > 50:
        pqs -= 28
    if atr_accel < -1.2:
        pqs -= 20

    if risk_mode == "Very Conservative":
        pqs -= 5
    elif risk_mode == "Aggressive Hold":
        pqs += 5

    pqs = _clamp(pqs, 10, 95)

    survivability = pqs - (decay_score * 0.45) - (reversal_threat * 0.35)

    if risk_mode == "Protect Profit":
        survivability -= 8
    elif risk_mode == "Aggressive Hold":
        survivability += 5
    elif risk_mode == "Very Conservative":
        survivability -= 12

    survivability = _clamp(survivability, 5, 95)

    # =====================================================
    # ADVANCED STRUCTURE VARIABLES
    # =====================================================
    stability = abs(pressure2) / (abs(pressure_accel) + 1)

    pressure_velocity = abs(pressure2) / (abs(pressure1) + 1)

    trend_efficiency = abs(pressure2) * h2_madx / (abs(pressure_accel) + 1)

    expansion_decay = abs(pressure_accel) / (abs(pressure2) + 1)

    expansion_quality = (
        trend_efficiency * 0.4
        + pressure_velocity * 0.3
        - expansion_decay * 0.3
    )

    exhaustion = abs(pressure2) > 20 and madx_accel < 0

    regime_score = 0

    if alignment:
        regime_score += 2
    if madx_accel > 0:
        regime_score += 1
    if pressure_accel > 0:
        regime_score += 1
    if dominance_growth > 0:
        regime_score += 1
    if stability > 3:
        regime_score += 1
    if abs(h4_pressure) > 10:
        regime_score += 1
    if abs(micro_pressure) > 5:
        regime_score += 1
    if exhaustion:
        regime_score -= 3
    if direction_alignment_count == 3:
        regime_score += 2
    if direction_alignment_count <= 1:
        regime_score -= 2

    environment_trust = (
        regime_score * 0.25
        + expansion_quality * 0.30
        + abs(h4_pressure) * 0.15
        + abs(micro_accel) * 0.10
        + stability * 0.15
        + di_persistence * 2.0
    )

    environment_trust = max(0, environment_trust)

    if environment_trust > 35:
        trust_level = "🔥 VERY HIGH"
    elif environment_trust > 24:
        trust_level = "🟢 HIGH"
    elif environment_trust > 14:
        trust_level = "🟡 MODERATE"
    else:
        trust_level = "🔴 LOW"

    reversal_risk = (
        expansion_decay * 0.35
        + (8 if abs(pressure2) > 20 else 0)
        + (6 if madx_accel < 0 else 0)
        + (5 if dominance_growth < 0 else 0)
        + (4 if stability < 2 else 0)
        + (10 if direction_alignment_count <= 1 else 0)
    )

    if reversal_risk > 24:
        reversal_state = "🚨 EXTREME REVERSAL RISK"
    elif reversal_risk > 13:
        reversal_state = "⚠️ REVERSAL POSSIBLE"
    else:
        reversal_state = "✅ STABLE CONTINUATION"

    continuation_probability = (environment_trust - reversal_risk) * 5
    continuation_probability = _clamp(continuation_probability, 0, 100)

    # =====================================================
    # LIQUIDITY / FALSE SIGNAL / EXECUTION ENGINE
    # =====================================================
    trap_score = (
        pressure_variance * 0.4
        + micro_reversal_frequency * 15
        + max(0, -madx_accel) * 2
    )

    trap_score = _clamp(trap_score, 0, 100)

    exec_stress = abs(atr_accel) * 10 + pressure_variance * 0.5
    exec_stress = _clamp(exec_stress, 0, 100)

    mqi = (
        atr_stability * 0.4
        + di_persistence * 15
        + abs(h4_pressure) * 1.5
    )

    mqi = _clamp(mqi, 0, 100)

    fsp = (
        pressure_variance * 0.35
        + max(0, -madx_accel) * 4
        + micro_reversal_frequency * 12
        + max(0, 5 - di_overlap) * 3
    )

    fsp = _clamp(fsp, 5, 95)

    ev = (continuation_probability / 100) * (abs(h4_pressure) / 10)
    ev = round(ev, 3)

    session_flow = (
        abs(h4_pressure) * 2
        + max(0, madx_accel) * 4
        + atr_stability * 0.4
    )

    session_flow = _clamp(session_flow, 0, 100)

    vqs = (
        atr_stability * 0.5
        + max(0, atr_accel) * 15
        + abs(h4_pressure) * 1.2
    )

    vqs = _clamp(vqs, 0, 100)

    regime_shift_prob = (
        max(0, -madx_accel) * 5
        + pressure_variance * 0.5
        + micro_reversal_frequency * 10
        + max(0, 8 - abs(h4_pressure)) * 3
    )

    regime_shift_prob = _clamp(regime_shift_prob, 0, 95)

    combined_trust = (
        environment_trust * 0.4
        + continuation_probability * 0.3
        + mqi * 0.3
    )

    combined_trust = _clamp(combined_trust, 0, 100)

    dist_to_liquidity = abs(h4_pressure) * 2
    wick_cluster = pressure_variance * 3

    liquidity_sweep_prob = (
        pressure_variance * 0.45
        + max(0, -madx_accel) * 6
        + micro_reversal_frequency * 18
        + max(0, 8 - abs(h4_pressure)) * 3
    )

    liquidity_sweep_prob = _clamp(liquidity_sweep_prob, 5, 95)

    liquidity_pressure = (
        abs(h4_pressure) * 2.2
        + abs(micro_pressure) * 1.5
        + max(0, madx_accel) * 5
        + atr_stability * 0.25
    )

    liquidity_pressure = _clamp(liquidity_pressure, 0, 100)

    if dist_to_liquidity < 25 and wick_cluster > 60:
        liq_zone = "Stop Cluster Zone (Dangerous)"
    elif dist_to_liquidity > 70:
        liq_zone = "Liquidity Void (Unstable)"
    elif 30 <= dist_to_liquidity <= 55:
        liq_zone = "Mid-Range Liquidity (Neutral)"
    else:
        liq_zone = "Liquidity Entry Zone (Safe Continuation)"

    breakout_failures = 0

    if pressure_accel > 0 and madx_accel < 0:
        breakout_failures += 1
    if abs(h4_pressure) > 12 and abs(micro_pressure) < 3:
        breakout_failures += 1
    if atr_accel < 0 and pressure_accel > 0:
        breakout_failures += 1
    if dominance_growth < 0:
        breakout_failures += 1

    hold_value = (
        environment_trust * 0.35
        + continuation_probability * 0.30
        + mqi * 0.20
        + atr_stability * 0.15
    )

    hold_value = _clamp(hold_value, 0, 100)

    candle_efficiency = (
        abs(h4_pressure) * 2
        + max(0, madx_accel) * 6
        + dominance_growth * 8
        - pressure_variance * 1.2
    )

    candle_efficiency = _clamp(candle_efficiency, 5, 100)

    # =====================================================
    # REGIME ADAPTIVE WEIGHTS
    # =====================================================
    adx_strength = h2_madx

    if adx_strength > 28 and noise_ratio < 40:
        regime = "🟢 TREND REGIME"
        regime_weight = 1.0
        decay_weight = 0.25
        liquidity_weight = 0.35
        reversal_weight = 0.20

    elif noise_ratio > 55 or di_overlap >= 4:
        regime = "🟡 TRANSITION / CHOPPY"
        regime_weight = 0.55
        decay_weight = 0.40
        liquidity_weight = 0.45
        reversal_weight = 0.35

    else:
        regime = "🔴 MANIPULATION / DISTRIBUTION"
        regime_weight = 0.35
        decay_weight = 0.30
        liquidity_weight = 0.60
        reversal_weight = 0.50

    momentum_conf = 0.85 if abs(h4_pressure) > 12 else 0.55

    contradiction_level = (
        "HIGH"
        if (decay_score > 60 and trap_score < 40)
        or (reversal_threat > 50 and hold_value > 70)
        else "MEDIUM"
        if abs(micro_pressure - h4_pressure) > 12
        else "LOW"
    )

    adjusted_survivability = survivability * regime_weight * momentum_conf
    adjusted_survivability = _clamp(adjusted_survivability, 0, 100)

    adaptive_exit_prob = (
        decay_score * decay_weight
        + trap_score * liquidity_weight
        + reversal_threat * reversal_weight
    )

    adaptive_exit_prob = _clamp(adaptive_exit_prob * max(0.35, regime_weight), 5, 98)

    final_prob = adaptive_exit_prob

    if risk_mode == "Protect Profit":
        final_prob += 8
    elif risk_mode == "Very Conservative":
        final_prob += 12
    elif risk_mode == "Aggressive Hold":
        final_prob -= 7

    final_prob = _clamp(final_prob, 5, 98)

    if final_prob >= 78 or ("Dangerous" in liq_zone and trap_score > 65):
        exit_type = "⚡ EMERGENCY EXIT (Liquidity Trap)"
    elif trap_score >= 65 or contradiction_level == "HIGH":
        exit_type = "🔴 FULL EXIT"
    elif decay_score > 45 or exec_stress > 60:
        exit_type = "🟠 PARTIAL EXIT"
    elif decay_velocity > 6:
        exit_type = "🟡 TRAIL STOP"
    else:
        exit_type = "🟢 HOLD"

    madx_z = (madx_accel / max(1, pressure_variance)) * 10
    decay_z = (decay_velocity - 5) / 8

    structural_conflict = abs(h4_pressure - micro_pressure) > 15
    tf_conflict = madx_accel > 0 and decay_velocity < -3

    if structural_conflict and tf_conflict:
        conflict_score = 85
    elif structural_conflict:
        conflict_score = 55
    else:
        conflict_score = 25

    half_life = 8 if momentum_decay <= 8 else 5 if momentum_decay <= 18 else 3

    p_continuation = 55 if regime == "🟢 TREND REGIME" else 35
    p_reversal = adaptive_exit_prob * 0.7
    p_manipulation = max(0, 100 - p_continuation - p_reversal)

    edge_score = 100 - (
        noise_ratio * 0.4
        + conflict_score * 0.4
        + (100 - regime_weight * 100) * 0.2
    )

    edge_score = _clamp(edge_score, 0, 100)

    if edge_score >= 70:
        edge_level = "HIGH EDGE"
    elif edge_score >= 45:
        edge_level = "WEAK EDGE"
    else:
        edge_level = "NO EDGE - UNRELIABLE"

    psi = (
        decay_score * 0.3
        + trap_score * 0.3
        + conflict_score * 0.2
        + exec_stress * 0.2
    )

    psi = _clamp(psi, 0, 98)

    base_threshold = (
        65
        if regime == "🟢 TREND REGIME"
        else 50
        if regime == "🟡 TRANSITION / CHOPPY"
        else 40
    )

    final_decision_threshold = base_threshold * (1 + conflict_score / 200)
    final_decision_threshold = _clamp(final_decision_threshold, 25, 95)

    mqs = (
        candle_efficiency * 0.4
        + atr_stability * 0.35
        + min(di_persistence * 8, 100) * 0.25
    )

    mqs = _clamp(mqs, 10, 100)

    tradeability = (
        mqs * 0.22
        + (100 - liquidity_pressure) * 0.18
        + mqi * 0.20
        + (100 - regime_shift_prob) * 0.15
        + session_flow * 0.15
        + combined_trust * 0.05
        + vqs * 0.05
    )

    tradeability = _clamp(tradeability, 10, 100)

    if tradeability >= 80:
        tradeability_level = "A+ Excellent"
    elif tradeability >= 60:
        tradeability_level = "Tradable"
    elif tradeability >= 40:
        tradeability_level = "Risky"
    else:
        tradeability_level = "Avoid"

    # =====================================================
    # ROLLING HISTORY / Z SCORE
    # =====================================================
    if "exit_history_full" not in st.session_state:
        st.session_state.exit_history_full = []

    st.session_state.exit_history_full.append(
        {
            "h4_pressure": h4_pressure,
            "mqs": mqs,
            "mqi": mqi,
            "liquidity_pressure": liquidity_pressure,
            "fsp": fsp,
        }
    )

    if len(st.session_state.exit_history_full) > 50:
        st.session_state.exit_history_full.pop(0)

    h4_z = 0.0

    if len(st.session_state.exit_history_full) > 5:
        pressures = [
            h.get("h4_pressure", 0)
            for h in st.session_state.exit_history_full
        ]

        mean_p = sum(pressures) / len(pressures)

        std_p = (
            sum((x - mean_p) ** 2 for x in pressures)
            / len(pressures)
        ) ** 0.5 + 1e-6

        h4_z = (h4_pressure - mean_p) / std_p

    trend_score = (h4_pressure * 0.4) + (mqs * 0.3) + (mqi * 0.3)

    chop_score = (
        liquidity_pressure * 0.4
        + fsp * 0.3
        + breakout_failures * 0.3
    )

    breakout_score = (abs(atr_accel) * 0.5) + (mqi * 0.5)

    p_trend, p_chop, p_breakout = _softmax3(
        trend_score / 50,
        chop_score / 50,
        breakout_score / 50,
    )

    prior_win = 0.50

    signal_strength = _clamp(
        (mqs + mqi + (100 - fsp)) / 300,
        0.01,
        0.99,
    )

    posterior_win = (
        prior_win * signal_strength
        / (
            prior_win * signal_strength
            + (1 - prior_win) * (1 - signal_strength)
            + 1e-12
        )
    )

    execution_cost = (
        (100 - atr_stability) * 0.10
        + breakout_failures * 5
        + micro_reversals * 3
    )

    execution_cost = _clamp(execution_cost, 0, 100)

    net_edge = ev * (1 - execution_cost / 100)

    # =====================================================
    # DISPLAY: FINAL DECISION
    # =====================================================
    st.markdown("---")
    st.markdown("## 🎯 Final Exit Recommendation")

    if "EMERGENCY" in exit_type or "FULL EXIT" in exit_type:
        st.markdown(
            f'<div class="danger-box">{exit_type}</div>',
            unsafe_allow_html=True,
        )
    elif "PARTIAL" in exit_type or "TRAIL" in exit_type:
        st.markdown(
            f'<div class="warn-box">{exit_type}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="good-box">{exit_type}</div>',
            unsafe_allow_html=True,
        )

    d1, d2, d3, d4 = st.columns(4)

    d1.metric("Exit Probability", f"{final_prob:.1f}%")
    d2.metric("Survivability", f"{survivability:.1f}%")
    d3.metric("Adjusted Survival", f"{adjusted_survivability:.1f}%")
    d4.metric("Tradeability", f"{tradeability:.1f}/100", tradeability_level)

    st.progress(_clamp(survivability, 0, 100) / 100)

    # =====================================================
    # DISPLAY: CORE HOLD/EXIT
    # =====================================================
    st.markdown("## 🧱 Core Hold / Exit Metrics")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("H4 Pressure", f"{h4_pressure:.2f}", h4_direction)
    c2.metric("Micro Pressure", f"{micro_pressure:.2f}", micro_direction)
    c3.metric("Decay Score", f"{decay_score:.1f}%")
    c4.metric("Reversal Threat", f"{reversal_threat:.1f}%")

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("Position Quality", f"{pqs:.1f}/100")
    c6.metric("Next 1-2H", "HOLD" if survivability > 50 else "MONITOR / EXIT")
    c7.metric("3-4H Risk", "HIGH" if reversal_threat > 50 else "LOW")
    c8.metric("Alignment", f"{direction_alignment_count}/3")

    if survivability >= 75 and reversal_threat < 35:
        st.success("🟢 STRONG HOLD — structure still supports the position.")
    elif survivability >= 55 and reversal_threat < 50:
        st.warning("🔵 HOLD CAUTIOUSLY — position can survive but monitor decay.")
    elif survivability >= 35:
        st.warning("🟠 PREPARE TO EXIT — survival is weakening.")
    else:
        st.error("🚨 EXIT / IMMEDIATE EXIT — position survivability is poor.")

    # =====================================================
    # DISPLAY: REGIME / EXPANSION
    # =====================================================
    st.markdown("## 🌐 Regime + Expansion Engine")

    r1, r2, r3, r4 = st.columns(4)

    r1.metric("Market Regime", regime)
    r2.metric("Regime Score", f"{regime_score}")
    r3.metric("Trust Level", trust_level)
    r4.metric("Continuation %", f"{continuation_probability:.1f}%")

    x1, x2, x3, x4 = st.columns(4)

    x1.metric("Pressure Accel", f"{pressure_accel:.2f}")
    x2.metric("MADX Accel", f"{madx_accel:.2f}")
    x3.metric("Dominance Growth", f"{dominance_growth:.2f}")
    x4.metric("Stability", f"{stability:.2f}")

    e1, e2, e3, e4 = st.columns(4)

    e1.metric("Pressure Velocity", f"{pressure_velocity:.2f}")
    e2.metric("Trend Efficiency", f"{trend_efficiency:.2f}")
    e3.metric("Expansion Decay", f"{expansion_decay:.2f}")
    e4.metric("Expansion Quality", f"{expansion_quality:.2f}")

    if expansion_quality > 25:
        st.success("🚀 HIGH QUALITY EXPANSION — strong sustainable directional pressure.")
    elif expansion_quality > 10:
        st.warning("⚠️ MODERATE EXPANSION — expansion exists but sustainability is uncertain.")
    else:
        st.error("❌ WEAK EXPANSION — fake breakout / reversal probability is higher.")

    rr1, rr2, rr3 = st.columns(3)

    rr1.metric("Reversal Risk", f"{reversal_risk:.2f}")
    rr2.metric("Reversal State", reversal_state)
    rr3.metric("Exhaustion", "YES" if exhaustion else "NO")

    if exhaustion:
        st.error("🚨 H4 EXHAUSTION DETECTED — trend may already be near completion.")

    # =====================================================
    # DISPLAY: LIQUIDITY / TRAP / CONFLICT
    # =====================================================
    st.markdown("## 🧲 Liquidity Trap + Conflict Engine")

    l1, l2, l3, l4 = st.columns(4)

    l1.metric("Liquidity Zone", liq_zone)
    l2.metric("Liquidity Sweep %", f"{liquidity_sweep_prob:.1f}%")
    l3.metric("Trap Score", f"{trap_score:.1f}/100")
    l4.metric("False Signal Prob", f"{fsp:.1f}%")

    l5, l6, l7, l8 = st.columns(4)

    l5.metric("Liquidity Pressure", f"{liquidity_pressure:.1f}")
    l6.metric("Signal Conflict", contradiction_level)
    l7.metric("Conflict Score", f"{conflict_score}/100")
    l8.metric("Breakout Failures", breakout_failures)

    if contradiction_level == "HIGH" or trap_score > 65:
        st.error("❌ High contradiction or trap pressure. Exit risk is elevated.")
    elif contradiction_level == "MEDIUM":
        st.warning("⚠️ Medium conflict. Trail stop or partial close may be better.")
    else:
        st.success("✅ Low conflict. Hold conditions are cleaner.")

    # =====================================================
    # DISPLAY: ADAPTIVE EXIT PROBABILITY
    # =====================================================
    st.markdown("## 🧠 Regime-Adaptive Exit Probability")

    a1, a2, a3, a4 = st.columns(4)

    a1.metric("Adaptive Exit %", f"{adaptive_exit_prob:.1f}%")
    a2.metric("Normalized MADX Z", f"{madx_z:.2f}")
    a3.metric("Decay Z", f"{decay_z:.2f}")
    a4.metric("Half-Life", f"{half_life} bars")

    p1, p2, p3 = st.columns(3)

    p1.metric("Continuation Scenario", f"{p_continuation:.1f}%")
    p2.metric("Sharp Reversal / Trap", f"{p_reversal:.1f}%")
    p3.metric("Sideways Manipulation", f"{p_manipulation:.1f}%")

    st.caption(
        "Regime-adaptive weights: trend/chop/manipulation modify how decay, "
        "liquidity, and reversal risk affect exit probability."
    )

    # =====================================================
    # DISPLAY: MARKET QUALITY
    # =====================================================
    st.markdown("## 📊 Market Quality + Tradeability")

    q1, q2, q3, q4 = st.columns(4)

    q1.metric("Market Quality Score", f"{mqs:.1f}/100")
    q2.metric("Market Quality Index", f"{mqi:.1f}/100")
    q3.metric("VQS", f"{vqs:.1f}/100")
    q4.metric("Session Flow", f"{session_flow:.1f}/100")

    q5, q6, q7, q8 = st.columns(4)

    q5.metric("ATR Stability", f"{atr_stability:.1f}%")
    q6.metric("Regime Shift Prob", f"{regime_shift_prob:.1f}%")
    q7.metric("Combined Trust", f"{combined_trust:.1f}%")
    q8.metric("Expected Value", f"{ev:.3f}R")

    st.metric("TRADEABILITY INDEX", f"{tradeability:.1f}/100 — {tradeability_level}")
    st.progress(tradeability / 100)

    # =====================================================
    # DISPLAY: STATISTICAL / BAYESIAN
    # =====================================================
    st.markdown("## 📈 Statistical + Bayesian Exit Layer")

    b1, b2, b3, b4 = st.columns(4)

    b1.metric("H4 Pressure Z-Score", f"{h4_z:.2f}")
    b2.metric("Trend Prob", f"{p_trend * 100:.1f}%")
    b3.metric("Chop Prob", f"{p_chop * 100:.1f}%")
    b4.metric("Breakout Prob", f"{p_breakout * 100:.1f}%")

    b5, b6, b7, b8 = st.columns(4)

    b5.metric("Bayesian Win Prob", f"{posterior_win * 100:.1f}%")
    b6.metric("Execution Cost", f"{execution_cost:.1f}%")
    b7.metric("Net Edge", f"{net_edge:.3f}R")
    b8.metric("Position Stress Index", f"{psi:.1f}/100")

    if edge_level == "NO EDGE - UNRELIABLE":
        st.error(edge_level)
    elif edge_level == "WEAK EDGE":
        st.warning(edge_level)
    else:
        st.success(edge_level)

    st.metric("Adaptive Exit Threshold", f"{final_decision_threshold:.1f}")

    # =====================================================
    # FULL DIAGNOSTIC TABLE
    # =====================================================
    st.markdown("## 🧾 Full Diagnostic Table")

    diag = pd.DataFrame(
        [
            ["Daily Pressure", daily_pressure],
            ["Yesterday Pressure", yesterday_pressure],
            ["Daily Pressure Accel", daily_pressure_accel],
            ["H4 Previous Pressure", h4_pressure_prev],
            ["H4 Current Pressure", h4_pressure],
            ["Micro Previous Pressure", prev_micro_pressure],
            ["Micro Current Pressure", micro_pressure],
            ["Micro Accel", micro_accel],
            ["MADX Accel", madx_accel],
            ["Micro MADX Accel", micro_madx_accel],
            ["Daily MADX Accel", daily_madx_accel],
            ["ATR Accel", atr_accel],
            ["Micro ATR Accel", micro_atr_accel],
            ["Daily ATR Change", daily_atr_change],
            ["MADX Decay", madx_decay],
            ["Pressure Decay", pressure_decay],
            ["ATR Decay", atr_decay],
            ["Decay Velocity", decay_velocity],
            ["Decay Acceleration", decay_acceleration],
            ["Momentum Decay", momentum_decay],
            ["Dominance Ratio Previous", dominance1],
            ["Dominance Ratio Current", dominance2],
            ["Dominance Growth", dominance_growth],
            ["Pressure Variance", pressure_variance],
            ["Noise Ratio", noise_ratio],
            ["DI Overlap", di_overlap],
            ["DI Persistence", di_persistence],
            ["Micro Reversal Frequency", micro_reversal_frequency],
            ["Micro Reversals", micro_reversals],
            ["Peak Momentum", peak_momentum],
            ["Historical ATR Avg", historical_atr_avg],
            ["Distance To Liquidity", dist_to_liquidity],
            ["Wick Cluster", wick_cluster],
            ["Candle Efficiency", candle_efficiency],
            ["Hold Value", hold_value],
            ["Environment Trust", environment_trust],
            ["Reversal Risk", reversal_risk],
            ["Continuation Probability", continuation_probability],
            ["Trap Score", trap_score],
            ["Exec Stress", exec_stress],
            ["FSP", fsp],
            ["EV", ev],
            ["Final Exit Probability", final_prob],
        ],
        columns=["Metric", "Value"],
    )

    diag["Value"] = diag["Value"].apply(
        lambda x: round(float(x), 4)
        if isinstance(x, (int, float))
        else x
    )

    with st.expander("📋 Open survivability diagnostics table", expanded=False):
        st.dataframe(diag, use_container_width=True, hide_index=True)

    # =====================================================
    # MEMORY LOG
    # =====================================================
    st.markdown("## 📌 Setup Memory")

    if "exit_trade_memory_full" not in st.session_state:
        st.session_state.exit_trade_memory_full = []

    if st.button(
        "📌 Log Current Exit Snapshot",
        use_container_width=True,
        key="exit_log_snapshot",
    ):
        st.session_state.exit_trade_memory_full.append(
            {
                "time": pd.Timestamp.now(),
                "direction": trade_direction,
                "exit_type": exit_type,
                "survivability": survivability,
                "final_prob": final_prob,
                "pqs": pqs,
                "decay_score": decay_score,
                "reversal_threat": reversal_threat,
                "trap_score": trap_score,
                "tradeability": tradeability,
                "edge_level": edge_level,
            }
        )

        st.success("Exit snapshot logged.")

    if st.session_state.exit_trade_memory_full:
        st.dataframe(
            pd.DataFrame(st.session_state.exit_trade_memory_full).tail(20),
            use_container_width=True,
        )

    st.caption(
        "✅ Full Exit Survivability Engine active: decay, reversal, liquidity, "
        "conflict, Bayesian, execution stress, edge quality, adaptive threshold."
    )

