DATA VISUALIZATION ORIGINAL + ADVANCED POWER BI ML PATCH

Files changed:
- tabs/home.py

What changed:
1. Kept the mobile fixes from the previous version.
2. Restored Data Visualization as an original-style visual tab first.
3. Added a second separate section under it: Advanced Power BI Price + ML Projection.
4. The two visual blocks are NOT combined and NOT mixed:
   - 1️⃣ Original Data Visualization
   - 🧠 Advanced Power BI Price + ML Projection
5. Uploaded picture / field image remains inside an Open / Close expander.
6. Copy buttons remain upgraded and phone friendly.
7. Original source data is not changed. The visualization works from session_state last_df.
8. Heavy visuals are behind Open / Close expanders and a Build / Refresh button so mobile can still open the page safely.

Copy/paste install:
- Copy the full new7 folder over your existing new7 folder, or replace only tabs/home.py if you want the smallest patch.
- Run your normal Streamlit command.
- Open Home → Data Visualization → Build / Refresh Data Visualization.
