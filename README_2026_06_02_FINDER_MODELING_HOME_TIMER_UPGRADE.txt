Finder Modeling + Home One-Field + Cloud Timer Sound Upgrade - 2026-06-02

What changed:
1. Finder inner tab is upgraded from simple rows to Data Modeling style output:
   - selected-hour metrics
   - deep-frame modeled summary table
   - bar chart for hour move / BUY candles / SELL candles / wick-mixed count
   - current basket P/L comparison field
   - candle preview/model features field
   - line chart
   - copy button exporting the complete selected-hour modeling payload

2. Home start page clutter is reduced:
   - Home Master Command Center, Copy All Home Data, relationship map, latest candle preview, extra panels, and full control center are now inside one open/close field.
   - The main Home page stays cleaner and faster.

3. Streamlit Cloud timer sound improved:
   - Sidebar timer now has a "Enable Cloud Timer Sound" button.
   - Tap it once after opening the app, especially on phone or Streamlit Cloud.
   - Timer still uses browser beeps + vibration where supported.

Original logic preserved:
- The old Doo analysis frame functions remain internally available.
- No trading execution code was added.
- Existing connectors and shared dataframe behavior are unchanged.
