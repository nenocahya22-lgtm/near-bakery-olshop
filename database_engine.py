import os
import re
from sqlalchemy import create_engine, text
import streamlit as st
import pandas as pd

# --- SUPABASE CONFIG ---
try:
    DB_URL = st.secrets["DB_URL"]
except:
    DB_URL = "postgresql://postgres.btcsynyxodkonqdpwowx:%23Nenocahyamulan190604@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_size=15, max_overflow=25, pool_recycle=3600, pool_pre_ping=True)

engine = get_engine()

class PostgresCursor:
    def __init__(self, parent):
        self.parent = parent
        self._res = None
    def execute(self, query, params=None):
        self._res = self.parent._execute_raw(query, params)
        return self
    @property
    def description(self):
        if self._res and hasattr(self._res, 'keys'):
            return [(k, None, None, None, None, None, None) for k in self._res.keys()]
        return []
    def fetchall(self): return self._res.fetchall() if self._res else []
    def fetchone(self): return self._res.fetchone() if self._res else None
    def close(self): pass

class PostgresCompat:
    def __init__(self, conn):
        self.conn = conn
        self._res = None
    def _execute_raw(self, query, params=None):
        try:
            if isinstance(query, str):
                query = query.replace("date('now')", "CURRENT_DATE").replace("datetime('now')", "CURRENT_TIMESTAMP")
                pts = re.findall(r'\?', query)
                for i in range(len(pts)): query = query.replace('?', f':p{i+1}', 1)
                q_obj = text(query)
                if params:
                    p_dict = {f'p{i+1}': v for i, v in enumerate(params)} if isinstance(params, (list, tuple)) else params
                    return self.conn.execute(q_obj, p_dict)
                return self.conn.execute(q_obj)
            return self.conn.execute(query, params) if params else self.conn.execute(query)
        except Exception as e:
            try: self.conn.rollback()
            except: pass
            raise e
    def execute(self, query, params=None):
        self._res = self._execute_raw(query, params)
        return self
    def cursor(self): return PostgresCursor(self)
    def fetchall(self): return self._res.fetchall() if self._res else []
    def fetchone(self): return self._res.fetchone() if self._res else None
    def scalar(self): return self._res.scalar() if self._res else None
    def commit(self):
        try: self.conn.commit()
        except: pass
    def close(self):
        try: self.conn.close()
        except: pass
    def __enter__(self): return self
    def __exit__(self, et, ev, etb): self.close()

def get_connection():
    return PostgresCompat(engine.connect())

def init_db():
    """V72: FORCE DATABASE SYNC"""
    with get_connection() as conn:
        # Suppliers
        try: conn.execute("CREATE TABLE IF NOT EXISTS suppliers (id SERIAL PRIMARY KEY, name TEXT, phone TEXT, vendor_name TEXT)")
        except: pass
        try: conn.execute("ALTER TABLE suppliers ADD COLUMN vendor_name TEXT")
        except: pass
        try: conn.execute("ALTER TABLE users ADD COLUMN base_salary INTEGER DEFAULT 0")
        except: pass
        try: conn.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")
        except: pass

        # Purchase Orders
        try: conn.execute("CREATE TABLE IF NOT EXISTS purchase_order_log (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        except: pass
        cols = {
            "inventory_id": "INTEGER", "supplier_id": "INTEGER", "qty_order": "FLOAT",
            "unit_order": "TEXT", "price_total": "FLOAT", "status": "TEXT", "manual_item_name": "TEXT"
        }
        for cn, ct in cols.items():
            try: conn.execute(f"ALTER TABLE purchase_order_log ADD COLUMN {cn} {ct}")
            except: pass
        
        # Inventory
        try: conn.execute("CREATE TABLE IF NOT EXISTS inventory_master (id SERIAL PRIMARY KEY, name TEXT, category TEXT, stock FLOAT, unit_beli TEXT, unit_pakai TEXT, price_per_unit_beli FLOAT, price_per_unit_pakai FLOAT, barcode TEXT UNIQUE, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, isi_ecer_per_grosir FLOAT DEFAULT 1, min_stock FLOAT DEFAULT 0)")
        except: pass
        try: conn.execute("ALTER TABLE inventory_master ADD COLUMN min_stock FLOAT DEFAULT 0")
        except: pass
        try: 
            conn.execute("ALTER TABLE recipe_master ADD COLUMN target_margin_pct FLOAT")
            conn.commit()
        except: pass
        
        # Sales Log & Items
        try: conn.execute("CREATE TABLE IF NOT EXISTS sales_log (id SERIAL PRIMARY KEY, total_revenue FLOAT, total_hpp FLOAT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, profit FLOAT, payment_method TEXT)")
        except: pass
        try: conn.execute("ALTER TABLE sales_log ADD COLUMN profit FLOAT")
        except: pass
        try: conn.execute("ALTER TABLE sales_log ADD COLUMN payment_method TEXT")
        except: pass
        try: conn.execute("ALTER TABLE sales_log ADD COLUMN total_hpp FLOAT DEFAULT 0")
        except: pass
        try: conn.execute("ALTER TABLE sales_log ADD COLUMN tax_amount FLOAT DEFAULT 0")
        except: pass
        try: conn.execute("ALTER TABLE sales_log ADD COLUMN sale_channel TEXT DEFAULT 'TOKO'")
        except: pass

        try: conn.execute("CREATE TABLE IF NOT EXISTS sales_items (id SERIAL PRIMARY KEY, sales_id INTEGER, recipe_id INTEGER, item_name TEXT, qty FLOAT, price FLOAT, subtotal FLOAT)")
        except: pass
        
        # Audit & Opname
        try: conn.execute("CREATE TABLE IF NOT EXISTS stock_opname_log (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, inventory_id INTEGER, stock_system FLOAT, stock_actual FLOAT, difference FLOAT, note TEXT)")
        except: pass
        try: conn.execute("CREATE TABLE IF NOT EXISTS audit_logs (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_actor TEXT, action TEXT, table_name TEXT, old_value TEXT, new_value TEXT, reason TEXT)")
        except: pass

        # CRM & Loyalty
        try: conn.execute("CREATE TABLE IF NOT EXISTS customers (id SERIAL PRIMARY KEY, name TEXT, phone TEXT UNIQUE, points INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        except: pass
        try: conn.execute("CREATE TABLE IF NOT EXISTS loyalty_points_log (id SERIAL PRIMARY KEY, customer_id INTEGER, points_added INTEGER, reason TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        except: pass
        try: conn.execute("CREATE TABLE IF NOT EXISTS attendance_log (id SERIAL PRIMARY KEY, username TEXT, type TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, image_path TEXT, location TEXT)")
        except: pass
        try: conn.execute("CREATE TABLE IF NOT EXISTS user_permissions (id SERIAL PRIMARY KEY, username TEXT, permission_key TEXT)")
        except: pass

        # Global Finance Config (Tax, etc)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS finance_config (config_key TEXT PRIMARY KEY, config_value TEXT)")
            # Set default PB1 Tax to 10%
            conn.execute("INSERT INTO finance_config (config_key, config_value) VALUES ('tax_pct', '10.0') ON CONFLICT (config_key) DO NOTHING")
            conn.commit()
        except: pass

        # user_sessions
        try: conn.execute("CREATE TABLE IF NOT EXISTS user_sessions (token TEXT PRIMARY KEY, username TEXT, expiry TIMESTAMP)")
        except: pass

        # SOP Digital Center
        try: conn.execute("CREATE TABLE IF NOT EXISTS sop_master (id SERIAL PRIMARY KEY, category TEXT, title TEXT, content TEXT, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        except: pass

        conn.commit()

# init_db() # Disabled to prevent hang on Cloud. Run manually if needed.
