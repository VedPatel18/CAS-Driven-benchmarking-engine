import pandas as pd
from sqlalchemy import create_engine, text
from mftool import Mftool
import pyxirr
from datetime import datetime
import urllib.parse
from dotenv import load_dotenv
import os
load_dotenv()

# ==========================================
# PHASE 1: ENVIRONMENT SETUP
# ==========================================
print("Phase 1: Initializing environment...")
DB_USER = os.getenv("DB_USER")          
DB_PASS = os.getenv("DB_PASSWORD")    
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")      

encoded_pass = urllib.parse.quote_plus(DB_PASS)
connection_string = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(connection_string)

# ==========================================
# PHASE 2: DATA EXTRACTION
# ==========================================
print("\nPhase 2: Extracting joined ledger from the database...")
query = """
    SELECT 
        t.transaction_date, 
        t.amount, 
        t.units, 
        t.amfi_code, 
        t.folio_id,
        f.investor_id 
    FROM transactions t
    JOIN folios f ON t.folio_id = f.folio_id;
"""
try:
    df_transactions = pd.read_sql_query(query, engine)
    print(f"Success! Loaded {len(df_transactions)} transactions.")
except Exception as e:
    print(f"CRITICAL: Database connection failed. {e}")
    exit()

# ==========================================
# PHASE 3: LIVE AMFI SYNC
# ==========================================
print("\nPhase 3: Fetching live NAVs from AMFI...")
try:
    unique_amfi_codes = df_transactions['amfi_code'].dropna().unique()
    mf = Mftool()
    live_prices_list = []

    for code in unique_amfi_codes:
        str_code = str(int(code)) if isinstance(code, (float, int)) else str(code) 
        quote = mf.get_scheme_quote(str_code)
        
        if isinstance(quote, dict) and 'nav' in quote:
            api_date = quote.get('date') or quote.get('Date') or datetime.today().strftime('%d-%m-%Y')
            live_prices_list.append({
                'amfi_code': str_code,
                'live_nav': float(quote['nav']),
                'nav_date': api_date
            })
            print(f"  -> Synced AMFI: {str_code} | Live NAV: ₹{quote['nav']}")

    if live_prices_list:
        df_live_navs = pd.DataFrame(live_prices_list)
        df_live_navs['nav_date'] = pd.to_datetime(df_live_navs['nav_date'], format="mixed", dayfirst=True).dt.date
        df_live_navs.to_sql('live_navs', con=engine, if_exists='replace', index=False)
except Exception as e:
    print(f"CRITICAL: Live Sync failed. {e}")

# ==========================================
# PHASE 4 & 5: MATH ENGINE & XIRR
# ==========================================
print("\nPhase 4 & 5: Calculating Granular, Portfolio, and Benchmark Metrics...")
df_transactions['amfi_code'] = df_transactions['amfi_code'].astype(str)
df_live_navs['amfi_code'] = df_live_navs['amfi_code'].astype(str)
df_merged = pd.merge(df_transactions, df_live_navs[['amfi_code', 'live_nav']], on='amfi_code', how='left')

# --- Helper Function 1: Standard Metrics ---
def calculate_metrics(group_df, identifier_col):
    results = []
    for identifier, group in group_df.groupby(identifier_col):
        total_invested = group['amount'].sum()
        
        fund_balances = group.groupby('amfi_code').agg(
            total_units=('units', 'sum'),
            live_nav=('live_nav', 'last') 
        )
        current_value = (fund_balances['total_units'] * fund_balances['live_nav']).sum()
        
        dates = pd.to_datetime(group['transaction_date']).tolist()
        cashflows = (-group['amount']).tolist() 
        dates.append(datetime.today().date())
        cashflows.append(current_value)
        
        try:
            xirr_pct = round(pyxirr.xirr(dates, cashflows) * 100, 2)
        except:
            xirr_pct = 0.0
            
        results.append({
            identifier_col: identifier,
            'total_invested': round(total_invested, 2),
            'current_value': round(current_value, 2),
            'overall_xirr_pct': xirr_pct
        })
    return pd.DataFrame(results)

# --- Helper Function 2: VECTORIZED Shadow Portfolio Benchmark ---
def calculate_benchmark_shadow_daily(df_tx, benchmark_name, eng):
    query = f"SELECT market_date, closing_price FROM benchmark_historical WHERE benchmark_name = '{benchmark_name}';"
    df_history = pd.read_sql(query, eng)
    
    if df_history.empty:
        return 0.0, pd.DataFrame()
        
    df_history['market_date'] = pd.to_datetime(df_history['market_date'])
    df_history = df_history.sort_values('market_date')
    
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date'])
    daily_tx = df_tx.groupby('transaction_date')['amount'].sum().reset_index()
    daily_tx.rename(columns={'transaction_date': 'market_date'}, inplace=True)
    
    daily_tx = pd.merge_asof(
        daily_tx.sort_values('market_date'), 
        df_history.dropna(subset=['closing_price']),
        on='market_date', 
        direction='backward'
    )
    
    daily_tx['units_bought'] = daily_tx['amount'] / daily_tx['closing_price']
    
    start_date = daily_tx['market_date'].min()
    end_date = pd.to_datetime(datetime.today().date())
    master_dates = pd.DataFrame({'market_date': pd.date_range(start=start_date, end=end_date)})
    
    df_daily = pd.merge(master_dates, df_history, on='market_date', how='left')
    df_daily['closing_price'] = df_daily['closing_price'].ffill()
    
    df_daily = pd.merge(df_daily, daily_tx[['market_date', 'units_bought']], on='market_date', how='left')
    df_daily['units_bought'] = df_daily['units_bought'].fillna(0)
    df_daily['cumulative_units'] = df_daily['units_bought'].cumsum()
    
    df_daily['shadow_value'] = df_daily['cumulative_units'] * df_daily['closing_price']
    df_daily['benchmark_name'] = benchmark_name
    
    dates = daily_tx['market_date'].dt.date.tolist()
    cashflows = (-daily_tx['amount']).tolist()
    
    dates.append(end_date.date())
    cashflows.append(df_daily['shadow_value'].iloc[-1])
    
    try:
        xirr_val = round(pyxirr.xirr(dates, cashflows) * 100, 2)
    except:
        xirr_val = 0.0
        
    df_daily = df_daily[['market_date', 'benchmark_name', 'shadow_value']]
    return xirr_val, df_daily


# --- Helper Function 3: VECTORIZED Actual Portfolio Daily History (Segmented by Investor) ---
def calculate_actual_portfolio_daily(df_tx, eng):
    unique_funds = df_tx['amfi_code'].dropna().unique().tolist()
    funds_str = "','".join([str(f) for f in unique_funds])
    
    query = f"SELECT nav_date AS market_date, amfi_code, nav FROM historical_navs WHERE amfi_code IN ('{funds_str}');"
    try:
        df_navs = pd.read_sql(query, eng)
    except Exception as e:
        print(f"  -> [!] Failed to fetch historical_navs. Error: {e}")
        return pd.DataFrame()
        
    if df_navs.empty:
        return pd.DataFrame()
        
    df_navs['market_date'] = pd.to_datetime(df_navs['market_date'])
    df_navs['amfi_code'] = df_navs['amfi_code'].astype(str)
    
    # 1. Group transactions by Date, Investor, and Fund
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date'])
    daily_tx = df_tx.groupby(['transaction_date', 'investor_id', 'amfi_code'])['units'].sum().reset_index()
    daily_tx.rename(columns={'transaction_date': 'market_date'}, inplace=True)
    
    # 2. Build continuous master calendar cross-joined with actual holdings
    start_date = daily_tx['market_date'].min()
    end_date = pd.to_datetime(datetime.today().date())
    master_dates = pd.DataFrame({'market_date': pd.date_range(start=start_date, end=end_date)})
    
    unique_holdings = daily_tx[['investor_id', 'amfi_code']].drop_duplicates()
    master_grid = master_dates.merge(unique_holdings, how='cross')
    
    # 3. Merge transactions and calculate rolling units per investor/fund
    df_daily = pd.merge(master_grid, daily_tx, on=['market_date', 'investor_id', 'amfi_code'], how='left')
    df_daily['units'] = df_daily['units'].fillna(0)
    df_daily = df_daily.sort_values(['investor_id', 'amfi_code', 'market_date'])
    df_daily['cumulative_units'] = df_daily.groupby(['investor_id', 'amfi_code'])['units'].cumsum()
    
    # 4. Merge NAVs, forward-fill gaps, and calculate final values
    df_daily = pd.merge(df_daily, df_navs, on=['market_date', 'amfi_code'], how='left')
    df_daily = df_daily.sort_values(['amfi_code', 'market_date'])
    df_daily['nav'] = df_daily.groupby('amfi_code')['nav'].ffill()
    df_daily['nav'] = df_daily['nav'].fillna(0)
    
    df_daily['fund_value'] = df_daily['cumulative_units'] * df_daily['nav']
    
    # 5. Roll up the total value by Date and Investor
    portfolio_daily = df_daily.groupby(['market_date', 'investor_id'])['fund_value'].sum().reset_index()
    portfolio_daily.rename(columns={'fund_value': 'portfolio_value'}, inplace=True)
    portfolio_daily['portfolio_value'] = portfolio_daily['portfolio_value'].round(2)
    
    return portfolio_daily


# Pass A: Calculate Fund-Level Metrics (Section 2)
df_fund_metrics = calculate_metrics(df_merged, 'folio_id')
print("  -> Fund metrics processed.")

# Pass B: Calculate Overall Portfolio Metrics (Section 1)
df_portfolio_metrics = calculate_metrics(df_merged, 'investor_id')
print("  -> Portfolio metrics processed.")

# Pass C: Calculate Benchmark Alpha Metrics AND Daily History (Section 3)
nifty50_xirr, nifty50_df = calculate_benchmark_shadow_daily(df_transactions, 'Nifty 50', engine)
nifty500_xirr, nifty500_df = calculate_benchmark_shadow_daily(df_transactions, 'Nifty 500', engine)

df_benchmark_metrics = pd.DataFrame([
    {'benchmark_name': 'Nifty 50', 'xirr_pct': nifty50_xirr},
    {'benchmark_name': 'Nifty 500', 'xirr_pct': nifty500_xirr}
])

combined_shadow_df = pd.concat([nifty50_df, nifty500_df], ignore_index=True)
print(f"  -> Shadow Portfolio Benchmarks processed (Nifty 50: {nifty50_xirr}%, Nifty 500: {nifty500_xirr}%).")

# Pass D: Calculate Actual Daily Portfolio History (Section 3)
df_portfolio_history = calculate_actual_portfolio_daily(df_transactions, engine)
print("  -> Actual Portfolio historical timeline processed.")


# ==========================================
# PHASE 6: THE DATABASE LOAD (FULL REFRESH)
# ==========================================
print("\nPhase 6: Pushing all calculations to PostgreSQL...")
try:
    with engine.begin() as conn:
        # Wipe all FIVE tables clean instantly
        conn.execute(text("TRUNCATE TABLE folio_metrics;"))
        conn.execute(text("TRUNCATE TABLE portfolio_metrics;"))
        conn.execute(text("TRUNCATE TABLE benchmark_metrics;"))
        conn.execute(text("TRUNCATE TABLE shadow_benchmark_values;"))
        conn.execute(text("TRUNCATE TABLE portfolio_history_daily;")) 
        print("  -> Cleared legacy data.")
        
    # Push all fresh data back to the database safely
    df_fund_metrics.to_sql('folio_metrics', con=engine, if_exists='append', index=False)
    df_portfolio_metrics.to_sql('portfolio_metrics', con=engine, if_exists='append', index=False)
    df_benchmark_metrics.to_sql('benchmark_metrics', con=engine, if_exists='append', index=False)
    
    if not combined_shadow_df.empty:
        combined_shadow_df.to_sql('shadow_benchmark_values', con=engine, if_exists='append', index=False)
        print(f"  -> Success! Inserted {len(combined_shadow_df)} daily timeline rows for Benchmarks.")
        
    if not df_portfolio_history.empty:
        df_portfolio_history.to_sql('portfolio_history_daily', con=engine, if_exists='append', index=False)
        print(f"  -> Success! Inserted {len(df_portfolio_history)} daily timeline rows for Actual Portfolio.")
    
    print(f"  -> Success! Inserted {len(df_fund_metrics)} fund records, {len(df_portfolio_metrics)} portfolio records, and 2 benchmark records.")
    print("\n✅ MASTER PIPELINE COMPLETE: Your dashboard database is 100% up to date!")
    
except Exception as e:
    print(f"\n[!] CRITICAL: Phase 6 Database Load failed. Error details: {e}")