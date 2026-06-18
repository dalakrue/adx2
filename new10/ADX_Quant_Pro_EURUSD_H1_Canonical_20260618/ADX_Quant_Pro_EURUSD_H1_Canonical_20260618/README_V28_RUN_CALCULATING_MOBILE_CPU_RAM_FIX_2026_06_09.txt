V28 RUN CALCULATING + MOBILE CPU/RAM FIX — 2026-06-09

What changed:
1. Data Visualization tab now shows the exact big button: ▶ Run Calculating.
2. The old button text is also kept under it for backward compatibility.
3. The “Open / Close — Original PowerBI + ML Projection” expander now receives the calculated 5-layer result, so it no longer only says “Click Run Calculating” after calculation.
4. Heavy Data Visualization logic is manual-run only. It does not auto-run when the tab opens.
5. Default rows reduced from 10,000 to 6,000 and slider max reduced from 20,000 to 12,000 for lower RAM/CPU on iPhone 11 and Streamlit Cloud.
6. Default forecast horizon reduced from 36 to 24 candles and max reduced from 96 to 60 for faster plotting.
7. Backtest summary max reduced from 500 to 360 bars for faster phone rendering.
8. Added Phone UI Big Mode button. It makes buttons/cards larger and reduces blur/shadow effects that cost GPU/CPU on mobile.
9. Added mobile CSS so sidebar width, dataframes, charts, and buttons behave better on phone.
10. Streamlit Cloud timer sound logic is already present: tap “Enable Cloud Timer Sound” once in the sidebar, then Start timer. Browser/mobile audio policies require this tap before alarm sound can play.
11. Added .streamlit/config.toml for Streamlit Cloud deploy defaults.

Run:
streamlit run adx_dashpoard.py

Important Streamlit Cloud phone sound note:
Mobile browsers and Streamlit Cloud cannot autoplay sound without a user tap. Open sidebar -> Trade Timer / Sound Alert -> tap Enable Cloud Timer Sound once -> start timer.
