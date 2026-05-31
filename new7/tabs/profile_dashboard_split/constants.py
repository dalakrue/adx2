GUIDE_TEXT = r'''
. Basic Understanding (The Foundation)

+DI = Bullish strength (Buying pressure)
-DI = Bearish strength (Selling pressure)
MADX (ADX) = Trend strength (How strong the move is, not direction)

Simple Rule:

If +DI > -DI → Market wants to go UP
If -DI > +DI → Market wants to go DOWN
Higher the difference = Stronger the direction


2. Core Indicators Explained (Easy Language)
IndicatorSimple MeaningGood ValueBad ValueWhat it tells youDSSMain direction power> 0 = Bullish
< -0 = BearishClose to 0Current momentum directionDSS AccelIs momentum speeding up?> 0 = Accelerating< 0 = SlowingVery important for entryCR (+DI/-DI Ratio)How dominant is the winning side> 2.0 = Strong< 1.5 = WeakDominance levelNS (Net Strength)Overall clarity of move> 0.35 = Clear< 0.25 = NoisyHow clean the trend isSTABHow stable the DI lines are< 6 = Stable> 10 = ChoppyNoise levelTCITrend Confidence Index> 1 = Strong< 0.5 = WeakCombined confidenceMOMQMomentum Quality> 0.5 = Good< 0.5 = PoorMomentum healthESIExhaustion Index< 80 = Healthy> 200 = ExhaustedRisk of reversal

3. Entry Rules (When to BUY or SELL)
Strong Entry Conditions (Best Setups)
You should see most of these together:

Direction Clear: DSS > 0 and DSS Accel > 0 → BUY
(or opposite for SELL)
Strong Dominance: CR > 2.0
Good Momentum: MOMQ > 0.5
Clean Move: NS > 0.35 and STAB < 6
High Confidence: TCI > 1.0
No Exhaustion: ESI < 80

Entry Score (from code) → Aim for 5 or more out of 8 filters.

4. Higher Timeframe Filters (Very Important)

MetricThresholdMeaningH4 Pressure> +8Strong bullish biasH4 Pressure< -8Strong bearish biasTrust Score≥ 78High quality setupTrust Score< 45AvoidVQS (Volatility Quality)≥ 68Good volatilityExhaustion> 55Danger - trend may endConflict Score> 45Mixed signals - risky
Golden Rule:
M1 signal must agree with H4 bias.
If H4 says BUY but M1 says SELL → Do not trade.

5. Exit & Hold Rules (Exit Survivability Engine)
Hold the trade if:

Survivability % > 75
Reversal Threat < 35
Decay Score is low
Position Quality Score (PQS) is high

Exit / Take Profit if:

Decay Score > 50
Reversal Threat > 50
Survivability < 55
Micro pressure goes against your trade
Exhaustion appears in higher timeframe

Emergency Exit Signals:

Liquidity Trap detected
Strong opposite micro pressure
MADX dropping fast
High Conflict + Decay

        # 📘 QUICK USER GUIDE

        # 🔹 What This Engine Does

        This engine analyzes:
        - Trend strength
        - Market momentum
        - Volatility
        - Reversal risk
        - Statistical edge
        - Market regime
        - ML-based direction probability

        It transforms raw market data into probability-based market states.

        ---

        # 🔹 Main Logic Flow

        Market Data
        ↓
        Indicators
        ↓
        Feature Engineering
        ↓
        Probability Models
        ↓
        Risk Engine
        ↓
        ML Confirmation
        ↓
        Regime Classification
        ↓
        Final Environment State

        ---

        # 🔹 Understanding the Main Metrics

        ## ADX

        Measures trend strength only.

        Important:
        ADX does NOT tell direction.

        Direction comes from:
        - +DI
        - -DI
        - Pressure

        Thresholds:
        - Below 20 → Weak trend
        - Above 25 → Strong trend
        - Above 30 → Powerful trend

        ---

        # 🔹 Pressure

        Equation:

        Pressure = +DI − -DI

        Purpose:
        Measures which side controls the market.

        Interpretation:
        - Positive → Bullish dominance
        - Negative → Bearish dominance
        - Near zero → Balance/chop

        ---

        # 🔹 ATR

        Measures volatility.

        High ATR:
        - Large price movement
        - Fast market

        Low ATR:
        - Small movement
        - Slow market

        Used for:
        - Dynamic SL/TP
        - Volatility normalization

        ---

        # 🔹 Trend Energy

        Equation:

        Trend Energy = ADX × ATR Pressure Ratio

        Purpose:
        Measures trend efficiency.

        High trend energy means:
        - Strong movement
        - Strong participation
        - Strong directional conviction

        ---

        # 🔹 Reversal Probability

        Purpose:
        Measures probability of market reversal.

        Built from:
        - DI crossover
        - ADX weakening
        - Weak pressure structure

        Interpretation:
        - Low → Stable trend
        - High → Unstable trend

        ---

        # 🔹 Continuation Probability

        Purpose:
        Measures probability that current trend continues.

        Uses:
        - ADX strength
        - Pressure dominance
        - Momentum acceleration

        High value:
        - Trend continuation more likely

        Low value:
        - Trend weakening

        ---

        # 🔹 Trade Quality

        Equation:

        Trade Quality =
        (Trend Energy × 0.6)
        + (Continuation × 0.3)
        − (Reversal × 0.4)

        Purpose:
        Measures overall setup quality.

        Higher score:
        - Better environment quality

        Lower score:
        - Poor environment

        ---

        # 🔹 Machine Learning Layer

        The ML model studies:
        - ADX
        - DI structure
        - ATR
        - Momentum
        - Pressure behavior

        Then predicts:
        Future direction after 5 candles.

        Output:
        - Direction prediction
        - Confidence probability

        ---

        # 🔹 Bayesian Win Probability

        Purpose:
        Estimate statistical edge using multiple probabilities.

        Combines:
        - Trend strength
        - Breakout strength
        - Chop conditions

        Interpretation:
        - High value → Better edge
        - Low value → Weak edge

        ---

        # 🔹 Conflict Score

        Purpose:
        Detect model disagreement.

        High conflict means:
        - Trend model disagrees with breakout model
        - Market structure unstable
        - Increased uncertainty

        Thresholds:
        - Below 20 → Stable
        - 20–40 → Mixed
        - Above 40 → Dangerous/unstable

        ---

        # 🔹 Risk Score

        Measures:
        - ML uncertainty
        - Conflict
        - Liquidity problems

        Higher risk score means:
        - Lower environment quality
        - Higher instability

        ---

        # 🔹 Tradeability Index

        Equation:

        Tradeability =
        Bayesian Win − (Conflict × 0.4)

        Purpose:
        Final market quality measurement.

        Interpretation:
        - High → Clean market structure
        - Medium → Selective conditions
        - Low → Weak/no edge

        ---

        # 🔹 Market Regimes

        ## Strong Trend
        Characteristics:
        - High ADX
        - Strong pressure
        - Positive acceleration

        Meaning:
        Market moving efficiently.

        ---

        ## Exhaustion
        Characteristics:
        - High ADX
        - Falling acceleration

        Meaning:
        Trend losing energy.

        ---

        ## Chop
        Characteristics:
        - Low pressure
        - Weak directional dominance

        Meaning:
        Sideways/noisy market.

        ---

        ## Reversal Risk
        Characteristics:
        - Weakening pressure
        - Directional instability

        Meaning:
        Possible structure transition.

        ---

        # 🔹 Why Multiple Models Are Used

        Single indicators fail frequently.

        This engine combines:
        - Trend analysis
        - Volatility analysis
        - Probability analysis
        - Regime analysis
        - Machine learning
        - Bayesian weighting

        Purpose:
        Reduce noise and improve environment filtering.

        ---

        # 🔹 Why Probability Matters

        Markets are uncertain.

        This engine does NOT predict certainty.

        It estimates:
        - Relative edge
        - Statistical probability
        - Market quality
        - Structural stability

        The goal is:
        Improve decision quality, not predict perfectly.

        ---

        # 🔹 System Philosophy

        Main principles:
        - Probability over prediction
        - Structure over emotion
        - Risk-adjusted analysis
        - Regime-aware filtering
        - Multi-layer confirmation

        The engine focuses on:
        - Detecting favorable environments
        - Avoiding unstable conditions
        - Measuring structural quality
        - Quantifying uncertainty
        1. Market is always a 2-force system: BUYERS vs SELLERS<br>
        2. +DI represents buyer pressure<br>
        3. -DI represents seller pressure<br>
        4. Price direction = dominance of stronger side<br><br>

        5. When +DI > -DI → bullish structure forms<br>
        6. When -DI > +DI → bearish structure forms<br><br>

        7. MADX measures strength of trend expansion<br>
        8. High MADX = strong directional continuation<br>
        9. Low MADX = consolidation / fake movement<br><br>

        10. DSS measures directional strength stability<br>
        11. Positive DSS = controlled bullish flow<br>
        12. Negative DSS = controlled bearish flow<br><br>

        13. Your system is NOT prediction based<br>
        14. It is STRUCTURE CONFIRMATION based<br>
        15. It avoids random market noise<br><br>

        16. Key idea: trade only when structure aligns across timeframes<br>
        17. M1 = execution layer<br>
        18. H4 = institutional direction layer<br>
        19. Alignment between layers = high probability setup<br><br>

        20. If M1 disagrees with H4 → avoid trade<br>
        21. If both align → continuation probability increases<br>




        1. TCI = Trend Confidence Index<br>
        → measures structural confidence of trend continuation<br><br>

        2. MOMQ = Momentum Quality<br>
        → detects acceleration or weakening momentum<br><br>

        3. CR = Control Ratio<br>
        → dominance strength between buyers and sellers<br><br>

        4. DSS = Direction Strength Stability<br>
        → prevents fake spike entries<br><br>

        5. High TCI + High MOMQ = strong trend phase<br>
        6. Low TCI = unstable market = no trade zone<br><br>

        7. MOMQ rising = trend acceleration phase<br>
        8. MOMQ falling = exhaustion phase<br><br>

        9. CR > 2 = strong dominance condition<br>
        10. CR < 1 = weak/no control zone<br><br>

        11. Your system filters low-quality volatility<br>
        12. It only accepts structured movement<br>




        STEP 1: Check H4 direction<br>
        STEP 2: Check M1 direction<br>
        STEP 3: Confirm alignment<br><br>

        STEP 4: Validate TCI > 1<br>
        STEP 5: Validate MOMQ > 0.5<br>
        STEP 6: Confirm DSS positive trend<br><br>

        ENTRY RULES:<br>
        - Only enter when ALL conditions align<br>
        - Avoid mixed signals<br>
        - Avoid low MADX environment<br><br>

        INVALID SETUPS:<br>
        - M1 opposite H4<br>
        - MOMQ dropping<br>
        - DSS unstable<br>





        FILTER 1: Trend Strength Filter (TCI)<br>
        FILTER 2: Momentum Filter (MOMQ)<br>
        FILTER 3: Control Filter (CR)<br>
        FILTER 4: Stability Filter (DSS)<br><br>

        PURPOSE:<br>
        → Remove fake breakouts<br>
        → Remove news spikes<br>
        → Remove low probability trades<br><br>

        RESULT INTERPRETATION:<br>
        - ALL filters aligned = HIGH probability<br>
        - 2 filters missing = WARNING<br>
        - 3+ filters missing = NO TRADE<br>


# 📘 Restored Original Guide + Quant Upgrade

## Basic Understanding
+DI = Bullish strength / buying pressure.
-DI = Bearish strength / selling pressure.
MADX / ADX = trend strength, not direction.

If +DI > -DI, market wants to go up. If -DI > +DI, market wants to go down. The bigger the difference, the stronger the direction.

## Core Indicators
DSS = Direction Strength Stability. Positive DSS supports BUY, negative DSS supports SELL.
DSS Accel = whether momentum is speeding up or slowing down.
CR = Control Ratio, +DI divided by -DI. Above 2.0 means stronger dominance.
NS = Net Strength. Above 0.35 means cleaner trend.
STAB = line stability. Lower is cleaner.
TCI = Trend Confidence Index. Higher means stronger trend confidence.
MOMQ = Momentum Quality. Rising means better momentum health.
ESI = Exhaustion Index. Too high means reversal/exhaustion risk.

## Entry Logic
Best setup usually needs: clear DSS direction, DSS acceleration, CR > 2, MOMQ > 0.5, NS > 0.35, STAB < 6, TCI > 1, and no exhaustion. M1 should agree with H4. If M1 and H4 disagree, avoid or reduce risk.

## Exit / Hold Logic
Hold when survivability is high, reversal threat is low, decay score is low, and PQS is high. Exit or scale out when decay score rises, reversal threat rises, micro pressure goes against your trade, or exhaustion appears on higher timeframe.

## Why Advanced History Matching Matters
The system compares current ADX, DI pressure, ATR, volatility, wick/body behavior, momentum, and regime features against previous days and times. The most similar day/time table helps you adjust strategy based on what usually happened after similar market conditions.



## Last-120 Similar Day Ranking Upgrade
The upgraded backtest matcher now compares **today's latest 120 candles** against candidate 120-candle windows from the **last 60 days**. It intentionally excludes **today and yesterday**, so the result is not biased by the same live session or yesterday's very recent structure.

Ranking uses ADX, +DI, -DI, ATR, pressure, ADX slope, returns, wick/body behavior, volatility regime, trend power, momentum velocity, range expansion, fat-tail risk, and mean-distance features. The table shows which historical day/time is most similar, the similarity percentage, future move after the selected horizon, and whether that historical pattern became bullish or bearish.

Priority use: when the top similar windows agree with the ML bias, the bias is safer. When they conflict, reduce lot size, wait, or use partial entry only.

## System Philosophy
Probability over prediction. Structure over emotion. Risk-adjusted analysis. Regime-aware filtering. Use the app to reduce bad trades, not to guarantee any trade.
'''
