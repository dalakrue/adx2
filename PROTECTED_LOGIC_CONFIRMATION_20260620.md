# Protected Logic and Visible Structure Confirmation

The implementation is additive and does not introduce a replacement decision engine.

Confirmed by static inspection and regression tests:

- Full Metric Detail + History remains canonical authority.
- Master, Entry, Hold, TP, Exit Risk, Trend Capacity Remaining, Alpha, Delta, regime, KNN, Greedy, priority, Power BI, forecast, NLP, Similar-Day, history, database, copy/export, API, authentication, timer, logout, and mobile paths remain present.
- Existing score scales and meanings were not redefined.
- Red, yellow, and blue central Power BI forecast paths were not replaced.
- No new top-level tab/page/sidebar/menu item was added.
- No Lunch principal field or duplicate Run Calculation button was added.
- Research calculations do not execute in renderers.
- Tab navigation reads the already-published canonical generation.
- The research layer cannot reverse BUY to SELL or SELL to BUY.
- The only decision mutation permitted is an exact-reason BUY/SELL tradeability downgrade to WAIT through CRC.
- Insufficient evidence preserves the existing protected decision and lowers/skips research influence.

A copy-on-write regression found during testing was fixed so calibrated forecast probability fields cannot mutate the protected pre-research canonical mapping in place.
