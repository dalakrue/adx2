Doo Prime Analysis upgrade - Current Data Session Intelligence

Added a large st.metric block at the top of the Doo Prime Analysis inner tab.
It calculates from the currently loaded M1/shared Doo dataframe and account snapshot:

- Session Now: ASIA / LONDON / LONDON-NY OVERLAP / NEW YORK / ROLLOVER
- Problem Score: live danger score combining session, margin gap, M1 movement, DVE, trust, fat-tail, and 120-candle range
- Best Action Now: HOLD / WAIT, WATCH EXIT SELL, WATCH EXIT BUY, or PAIRED REDUCE ONLY
- Pressure: BUY PRESSURE / SELL PRESSURE / MIXED based on deep-frame votes
- Margin Gap vs broker stop-out
- Next Session In based on latest candle timestamp
- Last Close, M1 Last Move %, 10 Candle Move %, 60 Candle Move %, 120 Range %
- DVE / Trust
- Margin Level, Equity, Margin Used, Floating P/L, Open Positions

Important behavior:
- Uses latest loaded candle time first, not only computer clock.
- Uses current app account_snapshot if available.
- If margin gap is thin, it prioritizes survival and shows PAIRED REDUCE ONLY.
- It does not remove or break existing 4-frame deep dashboard logic.
