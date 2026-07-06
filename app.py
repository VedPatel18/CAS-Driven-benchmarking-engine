import streamlit as st
import subprocess
import sys
from ingestion import process_cas_file
from database import sync_to_postgres

st.set_page_config(page_title="CAS Ingestion Engine", layout="centered")

# 1. Initialize a session state counter to manage widget clearing
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

st.title("CAMS CAS Ingestion Engine")
st.markdown("Upload your statement to parse it, sync it, and refresh all dashboard metrics.")

# 2. Attach the dynamic key to the inputs
uploaded_file = st.file_uploader(
    "Upload CAMS/KFintech CAS (PDF)", 
    type=["pdf"], 
    key=f"uploader_{st.session_state.form_key}" # Bound to session state
)
password = st.text_input(
    "Enter CAS Password", 
    type="password", 
    key=f"password_{st.session_state.form_key}" # Bound to session state
)

if uploaded_file and password:
    if st.button("Parse, Sync & Update DB", type="primary", use_container_width=True):
        
        with st.spinner("Processing document and rebuilding database metrics..."):
            try:
                # Step A: Parse the raw bytes
                cas_data, csv_data = process_cas_file(uploaded_file.getvalue(), password)
                
                # Step B: Sync raw ledger to PostgreSQL
                sync_to_postgres(cas_data)
                
                # Optional: A little popup to show progress
                st.toast("Raw data synced! Triggering metric calculations...", icon="⏳")

                # Step C: The Orchestrator (Runs your background Python scripts)
                # 1. Historical NAV backfill (MUST go first to fetch history for any new funds parsed in Step A)
                subprocess.run([sys.executable, "one_time_backfill.py"], check=True)
                
                # 2. Market Data second (Locks in benchmark history)
                subprocess.run([sys.executable, "benchmark_etl_pipeline.py"], check=True)
                
                # 3. Master Portfolio Math LAST (Now it has all raw data, NAVs, and Benchmarks ready to calculate)
                subprocess.run([sys.executable, "master_etl_pipeline.py"], check=True)
                
                # Step D: Success UI
                st.success("✅ System Fully Updated! Document parsed, synced, and all Alpha metrics calculated.")
                
                st.download_button(
                    label="⬇️ Download Raw CSV",
                    data=csv_data,
                    file_name=uploaded_file.name.replace('.pdf', '.csv'),
                    mime="text/csv",
                    use_container_width=True
                )

                # Step E: The UI Wipe
                # Incrementing this number forces the file uploader and password field above to instantly reset
                st.session_state.form_key += 1
                
            except subprocess.CalledProcessError as e:
                st.error(f"ETL Pipeline Failed! The background math script crashed. Error: {e}")
            except Exception as e:
                st.error(f"Error processing document.\nDetails: {e}")