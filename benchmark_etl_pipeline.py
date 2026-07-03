import pandas as pd
from sqlalchemy import create_engine
import yfinance as yf
from datetime import timedelta, datetime
import urllib.parse
from dotenv import load_dotenv
import os
load_dotenv()

# ==========================================
# PHASE 1: ENVIRONMENT SETUP
# ==========================================
print("Phase 1: Initializing Benchmark Environment...")
DB_USER = os.getenv("DB_USER")          
DB_PASS = os.getenv("DB_PASSWORD")    
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")        

encoded_pass = urllib.parse.quote_plus(DB_PASS)
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Define the exact Yahoo Finance tickers
benchmarks = {
    'Nifty 50': '^NSEI',
    'Nifty 500': '^CRSLDX'
}

# ==========================================
# PHASE 2 & 3: THE SMART FETCH & DATABASE LOAD
# ==========================================
print("\nPhase 2: Executing Incremental Load...")

for name, ticker in benchmarks.items():
    print(f"\nProcessing {name} ({ticker})...")
    
    try:
        # 1. Ask PostgreSQL for the most recent date we have for this specific index
        query = f"SELECT MAX(market_date) FROM benchmark_historical WHERE benchmark_name = '{name}';"
        max_date = pd.read_sql(query, engine).iloc[0, 0]
        
        # 2. Determine the start date for the API call
        if pd.isnull(max_date):
            print("  -> No history found. Initiating massive 26-year historical download...")
            start_date = '2000-01-01' 
        else:
            # Add 1 day to the max_date so we don't download data we already have
            start_date = (max_date + timedelta(days=1)).strftime('%Y-%m-%d')
            print(f"  -> Database is up to date until {max_date}. Fetching new data from {start_date}...")
            
        # Stop if the database is already fully synced through today
        if start_date > datetime.today().strftime('%Y-%m-%d'):
            print(f"  -> [OK] {name} is already completely up to date.")
            continue
            
        # 3. Ping Yahoo Finance
        stock = yf.Ticker(ticker)
        df_yf = stock.history(start=start_date)
        
        if not df_yf.empty:
            # 4. Clean and format the data to match our PostgreSQL table
            df_yf = df_yf.reset_index()
            # Force the datetime to just be a standard Date object
            df_yf['Date'] = pd.to_datetime(df_yf['Date']).dt.date
            
            df_clean = pd.DataFrame({
                'benchmark_name': name,
                'market_date': df_yf['Date'],
                'closing_price': round(df_yf['Close'], 2)
            })
            
            # 5. Push exactly the missing rows to the database using 'append'
            df_clean.to_sql('benchmark_historical', con=engine, if_exists='append', index=False)
            print(f"  -> Success! Appended {len(df_clean)} new daily closing prices.")
        else:
            print("  -> No new trading days to fetch (Market might be closed).")
            
    except Exception as e:
        print(f"  -> [!] CRITICAL ERROR processing {name}: {e}")

print("\n✅ BENCHMARK PIPELINE COMPLETE: Market history is locked and loaded!")