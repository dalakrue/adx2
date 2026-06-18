2026-06-01 Doo Prime MT5 Independent Connector + Compact Glass UI Patch

What changed:
1) Doo Prime Account button now uses a dedicated Doo Prime / MetaTrader channel.
   - Sidebar API connector can stay on TwelveData/fallback.
   - Doo Prime inner Account button connects local Doo Prime MT5 account and optional MT5 candles.
   - OFF by default: Doo Prime MT5 does not overwrite the shared sidebar dataframe.
   - Optional: click/use "Sync to shared df" or "Use Doo MT5 For All Tabs" to let MT5 candles feed all tabs.

2) Doo Prime live analytics now prefers dedicated Doo MT5 candles.
   - If Doo MT5 candles are not available, it falls back to the existing shared/sidebar dataframe.

3) Fixed compact Doo Prime section helper relation.
   - Added missing safe imports for time and choice_buttons.
   - Refresh button now refreshes the dedicated Doo MT5 account/market connector instead of calling undefined helper code.

4) UI/UX upgraded globally.
   - Smaller transparent glass expanders/open-close fields.
   - Smaller sidebar open/close fields.
   - Transparent input boxes.
   - Button shine animation.
   - Popup/floating animation effects.

Run:
streamlit run adx_dashpoard.py --server.port 8501

For Doo Prime MT5 account connection:
- Open Doo Prime MetaTrader 5 locally.
- Login to the correct account.
- Make sure the symbol, for example XAUUSD, is visible in Market Watch.
- Open Home > Doo Prime > Account.
- Click "Connect Doo Prime MT5 Account".
