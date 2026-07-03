from sqlalchemy import create_engine
from mftool import Mftool
import pandas as pd
import urllib.parse
import time
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

# ==========================================
# 1. DATABASE SETUP
# ==========================================
DB_USER = os.getenv("DB_USER")          
DB_PASS = os.getenv("DB_PASSWORD")    
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")       

encoded_pass = urllib.parse.quote_plus(DB_PASS)
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

mf = Mftool()

# Define your strict Lookback Window
CUTOFF_DATE = pd.to_datetime('2020-01-01').date()

# ==========================================
# 2. AUTOMATED FUND DETECTION
# ==========================================
query = "SELECT DISTINCT amfi_code FROM transactions WHERE amfi_code IS NOT NULL;"
df_unique_funds = pd.read_sql(query, engine)
unique_codes = df_unique_funds['amfi_code'].astype(str).tolist()

print(f"Detected {len(unique_codes)} unique mutual funds.")
print(f"Enforcing strict data cutoff: {CUTOFF_DATE}. Starting backfill...")

# ==========================================
# 3. THE SMART FETCH & FILTER LOOP
# ==========================================
for code in unique_codes:
    print(f"\nFetching history for AMFI: {code}...")
    try:
        # 1. Ask PostgreSQL for the most recent date we have for this specific fund
        query = f"SELECT MAX(nav_date) FROM historical_navs WHERE amfi_code = '{code}';"
        max_date = pd.read_sql(query, engine).iloc[0, 0]
        
        # 2. Fetch raw data from AMFI
        df_history = mf.get_scheme_historical_nav(code, as_Dataframe=True)
        
        # Clean and format
        df_history = df_history.reset_index()
        df_history['date'] = pd.to_datetime(df_history['date'], format="%d-%m-%Y").dt.date
        df_history['nav'] = df_history['nav'].astype(float)
        
        # 3. THE DUPLICATION SHIELD (Filter logic)
        if pd.notnull(max_date):
            # If we have data, only keep rows newer than our latest recorded date
            df_filtered = df_history[df_history['date'] > max_date]
            print(f"  -> Database has data up to {max_date}. Filtering for new days only.")
        else:
            # If this is a brand new fund in the DB, fall back to our 2020 cutoff
            df_filtered = df_history[df_history['date'] >= CUTOFF_DATE]
            print(f"  -> Brand new fund detected. Enforcing 2020 cutoff.")
            
        # 4. Check if we even need to insert anything
        if df_filtered.empty:
            print(f"  -> [OK] AMFI {code} is already 100% up to date. Skipping.")
            continue
            
        # Format for our single database table
        df_clean = pd.DataFrame({
            'amfi_code': code,
            'nav_date': df_filtered['date'],
            'nav': df_filtered['nav']
        })
        
        # Append to the master table safely
        df_clean.to_sql('historical_navs', con=engine, if_exists='append', index=False)
        print(f"  -> Success! Added {len(df_clean)} missing historical days.")
        
        # Pause to respect AMFI server limits
        time.sleep(1) 
        
    except Exception as e:
        print(f"  -> [!] Failed to process AMFI {code}. Error: {e}")

print("\n✅ DUPLICATE-PROOF BACKFILL COMPLETE!")