# Fix Report — PowerBI Current Candle, Menu Copy Buttons, Grounded AI

## Fixed
1. Field 2 Power BI renderer now synchronizes to the same latest completed H1 candle used by Lunch Field 1.
2. Non-future cached display rows are removed before validation/charting instead of causing stale timestamp failure.
3. Display anchor is aligned to the latest completed candle close used by Lunch.
4. Blue future candle cache is filtered so only true future candles remain visible.
5. Menu copy controls no longer show long wrapped text in the phone menu; unavailable full copy is a disabled button.
6. Menu helper captions are shortened to prevent the sidebar/menu from becoming unreadable on phone width.
7. Grounded AI Assistant recovery path remains active and uses the newest valid published canonical generation or safe offline diagnostic mode.

## Validation
- Python compile check passed for the full project with compileall.
- No protected trading calculation logic was replaced; fixes are display/cache synchronization and UI button rendering only.
