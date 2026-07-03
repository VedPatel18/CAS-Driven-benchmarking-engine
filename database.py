import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()

def sync_to_postgres(cas_data):
    """Securely inserts parsed CAS data, handling NULLs to prevent tax/stamp duty duplicates."""
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"), 
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    
    try:
        info = cas_data.investor_info
        
        # 1. UPSERT INVESTOR
        cursor.execute('''
            INSERT INTO investors (name, email, mobile, address)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING investor_id;
        ''', (info.name, info.email, info.mobile, info.address))
        
        result = cursor.fetchone()
        if result:
            investor_id = result[0]
        else:
            cursor.execute('SELECT investor_id FROM investors WHERE email = %s', (info.email,))
            investor_id = cursor.fetchone()[0]

        # 2. UPSERT FOLIOS
        for folio in cas_data.folios:
            cursor.execute('''
                INSERT INTO folios (investor_id, amc_name, folio_number)
                VALUES (%s, %s, %s)
                ON CONFLICT (folio_number, investor_id) DO NOTHING
                RETURNING folio_id;
            ''', (investor_id, folio.amc, folio.folio))
            
            f_result = cursor.fetchone()
            if f_result:
                folio_id = f_result[0]
            else:
                cursor.execute('SELECT folio_id FROM folios WHERE folio_number = %s AND investor_id = %s', 
                               (folio.folio, investor_id))
                folio_id = cursor.fetchone()[0]

            # 3. UPSERT TRANSACTIONS
            for scheme in folio.schemes:
                scheme_name = getattr(scheme, 'scheme', getattr(scheme, 'name', 'Unknown Scheme'))
                isin = getattr(scheme, 'isin', None)
                amfi_code = getattr(scheme, 'amfi', None) # <-- NEW: Grab AMFI Code
                
                for txn in scheme.transactions:
                    t_amount = txn.amount if txn.amount is not None else 0.0
                    t_units = txn.units if txn.units is not None else 0.0
                    t_nav = txn.nav if txn.nav is not None else 0.0
                    t_balance = txn.balance if txn.balance is not None else 0.0

                    cursor.execute('''
                        INSERT INTO transactions 
                        (folio_id, scheme_name, isin, amfi_code, transaction_date, description, amount, units, nav, balance, transaction_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (folio_id, transaction_date, description, amount, units) DO NOTHING;
                    ''', (
                        folio_id, scheme_name, isin, amfi_code, txn.date, txn.description, 
                        t_amount, t_units, t_nav, t_balance, txn.type
                    ))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        raise e
        
    finally:
        cursor.close()
        conn.close()








