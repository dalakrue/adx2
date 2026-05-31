import streamlit as st
import pandas as pd

from core.database import (
    database_health,
    database_relationship_summary,
    list_data_files,
    read_table,
    backup_all_data,
    compact_csv,
    repair_csv,
    delete_data_file,
    export_all_to_excel,
    save_market_cache,
    vacuum_sqlite,
)
from core.system_contract import render_relationship_matrix, timing_dataframe, system_events_dataframe


def _download_csv_button(df: pd.DataFrame, filename: str):
    try:
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Download visible table CSV", data=csv, file_name=filename, mime="text/csv", use_container_width=True)
    except Exception as exc:
        st.warning(f"Download failed: {exc}")


def show():
    st.title("🗄️ Database Center")
    st.caption("Safe database control for all tabs. Original CSV/JSON behavior is kept; this tab only adds stronger viewing, backup, repair, export, and cleanup tools.")

    render_relationship_matrix(location="database", compact=True)

    health = database_relationship_summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Data Files", health.get("files", 0))
    c2.metric("CSV Files", health.get("csv_files", 0))
    c3.metric("Size KB", health.get("total_size_kb", 0))
    c4.metric("SQLite Mirror Rows", health.get("sqlite_event_rows", 0))

    with st.expander("Database + backend relationship health", expanded=False):
        st.json(health)
        st.markdown("#### Tab Timing")
        timing = timing_dataframe()
        if timing.empty:
            st.info("No tab timing recorded yet. Open tabs once to collect timing.")
        else:
            with st.expander("⏱ Open tab timing table", expanded=False):
                st.dataframe(timing, use_container_width=True, hide_index=True)
        st.markdown("#### Latest Runtime Events")
        events = system_events_dataframe(80)
        if events.empty:
            st.info("No runtime events in memory yet.")
        else:
            with st.expander("📜 Open system events table", expanded=False):
                st.dataframe(events, use_container_width=True, hide_index=True, height=260)

    files = list_data_files()
    if files.empty:
        st.info("No database files found yet. Use Home, Engine, Doo Prime, Train Data, or Profile first to create snapshots.")
        return

    st.subheader("📌 Database Index")
    with st.expander("📁 Open data files table", expanded=False):
        st.dataframe(files, use_container_width=True, hide_index=True)

    st.subheader("🔎 Table Viewer")
    csv_files = files[files["type"].astype(str).str.upper().eq("CSV")].copy()
    tables = csv_files["table"].astype(str).tolist() if not csv_files.empty else []
    if not tables:
        st.warning("No CSV tables available to preview.")
        return

    left, right = st.columns([2, 1])
    with left:
        table = st.selectbox("Choose table", tables, key="database_table_choice")
    with right:
        limit = st.number_input("Rows to load", min_value=50, max_value=50000, value=1000, step=50, key="database_limit")

    df = read_table(table, limit=int(limit))
    if df.empty:
        st.warning("This table has no readable rows or may need repair.")
    else:
        search = st.text_input("Quick filter text", value="", key="database_search")
        view = df.copy()
        if search.strip():
            mask = view.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
            view = view[mask]
        st.caption(f"Showing {len(view):,} row(s) from `{table}`")
        with st.expander("📋 Open selected file rows", expanded=True):
            st.dataframe(view, use_container_width=True, hide_index=True)
        _download_csv_button(view, f"{table}_visible_export.csv")

        with st.expander("📊 Auto summary", expanded=False):
            st.write("Columns:", list(view.columns))
            numeric = view.select_dtypes(include="number")
            if not numeric.empty:
                with st.expander("📊 Open numeric summary table", expanded=False):
                    st.dataframe(numeric.describe().T, use_container_width=True)
            else:
                st.info("No numeric columns found for summary.")

    st.subheader("🛠️ Safe Maintenance")
    a, b, c, d = st.columns(4)
    with a:
        if st.button("💾 Backup all", use_container_width=True, key="db_backup_all"):
            out = backup_all_data()
            if out:
                st.success(f"Backup created: {out}")
            else:
                st.error("Backup failed.")
    with b:
        keep = st.number_input("Keep latest rows", min_value=100, max_value=500000, value=250000, step=1000, key="db_keep_rows")
        if st.button("🧹 Compact selected", use_container_width=True, key="db_compact"):
            st.success("Compacted safely." if compact_csv(table, int(keep)) else "Compact failed.")
    with c:
        if st.button("🧯 Repair selected", use_container_width=True, key="db_repair"):
            st.success("Repair finished." if repair_csv(table) else "Repair could not recover rows.")
    with d:
        if st.button("📦 Export Excel", use_container_width=True, key="db_export_excel"):
            out = export_all_to_excel()
            if out:
                st.success(f"Excel export created: {out}")
            else:
                st.error("Excel export failed. Make sure openpyxl is installed.")

    e, f = st.columns(2)
    with e:
        if st.button("📌 Save latest market cache", use_container_width=True, key="db_save_market_cache"):
            ok = save_market_cache(st.session_state.get("last_df"), max_rows=10000)
            st.success("Saved latest market cache to data/latest_market_cache.csv" if ok else "No market dataframe available to cache.")
    with f:
        if st.button("⚙️ Optimize SQLite mirror", use_container_width=True, key="db_vacuum_sqlite"):
            st.success("SQLite mirror optimized." if vacuum_sqlite() else "SQLite optimization failed safely.")

    with st.expander("⚠️ Delete selected table", expanded=False):
        st.warning("This creates a backup first, then deletes the selected CSV. Use only when you truly want to reset a table.")
        confirm = st.text_input(f"Type DELETE {table} to confirm", key="db_delete_confirm")
        if st.button("Delete selected CSV", type="secondary", key="db_delete_selected"):
            if confirm == f"DELETE {table}":
                st.success("Deleted safely." if delete_data_file(table, "csv") else "Delete failed.")
                st.rerun()
            else:
                st.error("Confirmation text did not match.")
