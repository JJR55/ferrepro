"""
Database connection module for Supabase Postgres.
Falls back to Turso HTTP if no Supabase DB URL is configured.
"""
import os
import json
import atexit
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (ferrepro folder)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL", "").strip().replace(" ", "")
SUPABASE_DEBUG = os.getenv("SUPABASE_DEBUG", "false").lower() in ("1", "true", "yes")
SUPABASE_POOL_MIN_SIZE = int(os.getenv("SUPABASE_POOL_MIN_SIZE", "1"))
SUPABASE_POOL_MAX_SIZE = int(os.getenv("SUPABASE_POOL_MAX_SIZE", "1"))

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
except ImportError:
    psycopg = None
    ConnectionPool = None

import requests

class SupabaseClient:
    """PostgreSQL client for Supabase using psycopg with connection pooling."""

    def __init__(self, conninfo):
        if psycopg is None:
            raise ImportError("psycopg[binary] is required for Supabase support. Install it in requirements.txt")
        self.conninfo = conninfo
        print(f"[Supabase] Connected to: {conninfo[:60]}...")
        
        # Crear pool de conexiones (limitado para Supabase)
        if ConnectionPool:
            try:
                self.pool = ConnectionPool(
                    conninfo,
                    min_size=SUPABASE_POOL_MIN_SIZE,
                    max_size=SUPABASE_POOL_MAX_SIZE,
                    timeout=5
                )
                print(f"[Supabase] Connection pool initialized (min={SUPABASE_POOL_MIN_SIZE}, max={SUPABASE_POOL_MAX_SIZE})")
            except Exception as e:
                print(f"[Supabase] Warning: Connection pool failed: {e}")
                self.pool = None
        else:
            self.pool = None

    def execute(self, sql, params=None):
        if SUPABASE_DEBUG:
            print(f"[Supabase] SQL: {sql} | params: {params}")
        
        max_retries = 3
        retry_delay = 0.5  # segundos
        
        for attempt in range(max_retries):
            try:
                if self.pool:
                    # Usar connection pool con reintentos
                    try:
                        with self.pool.connection(timeout=10) as conn:
                            with conn.cursor(row_factory=dict_row) as cur:
                                if params:
                                    sql_exe = sql.replace("?", "%s")
                                else:
                                    sql_exe = sql
                                
                                if params is None:
                                    cur.execute(sql_exe)
                                else:
                                    cur.execute(sql_exe, params)
                                
                                if cur.description:
                                    rows = cur.fetchall()
                                    return [dict(r) for r in rows]
                                return []
                    except Exception as pool_err:
                        # Si el pool falla, reintentar o usar fallback
                        if "EMAXCONNSESSION" in str(pool_err) or "max clients" in str(pool_err):
                            if attempt < max_retries - 1:
                                print(f"[Supabase] Pool exhausted, retrying in {retry_delay}s...")
                                time.sleep(retry_delay)
                                retry_delay *= 1.5
                                continue
                        raise
                else:
                    # Fallback: conexión individual con reintentos
                    try:
                        with psycopg.connect(self.conninfo, autocommit=False, connect_timeout=5) as conn:
                            with conn.cursor(row_factory=dict_row) as cur:
                                if params:
                                    sql_exe = sql.replace("?", "%s")
                                else:
                                    sql_exe = sql
                                
                                if params is None:
                                    cur.execute(sql_exe)
                                else:
                                    cur.execute(sql_exe, params)
                                
                                conn.commit()
                                if cur.description:
                                    rows = cur.fetchall()
                                    return [dict(r) for r in rows]
                                return []
                    except Exception as conn_err:
                        if "EMAXCONNSESSION" in str(conn_err) or "max clients" in str(conn_err):
                            if attempt < max_retries - 1:
                                print(f"[Supabase] Connection limit reached, retrying in {retry_delay}s...")
                                time.sleep(retry_delay)
                                retry_delay *= 1.5
                                continue
                        raise
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[Supabase] Error after {max_retries} attempts: {e}")
                    raise
                print(f"[Supabase] Attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)


    def execute_raw(self, sql, params=None):
        self.execute(sql, params)
    
    def close(self):
        """Cerrar el pool de conexiones."""
        if self.pool:
            self.pool.close()



# ─── Client singleton ───
_client = None

def get_client():
    global _client
    if _client is None:
        # Try Supabase first if configured
        if not SUPABASE_DATABASE_URL:
            raise Exception("SUPABASE_DATABASE_URL is not configured.")
        _client = SupabaseClient(SUPABASE_DATABASE_URL)
        print("[DB] Using Supabase Postgres")
    if _client is None:
        raise Exception("No database provider configured. Set SUPABASE_DATABASE_URL.")
    return _client


# ─── Public API ───

def query(sql, params=None):
    """Execute a SELECT query and return list of dicts."""
    client = get_client()
    return client.execute(sql, params)


def execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE statement."""
    client = get_client()
    client.execute_raw(sql, params)


def init_db():
    """Create tables if they don't exist."""
    print("[DB] Initializing database...")
    using_supabase = bool(SUPABASE_DATABASE_URL)
    pk_type = "SERIAL PRIMARY KEY" if using_supabase else "INTEGER PRIMARY KEY AUTOINCREMENT"

    execute("""CREATE TABLE IF NOT EXISTS articulos (
        id %s,
        codigo TEXT UNIQUE, nombre TEXT, departamento TEXT,
        precio_costo DOUBLE PRECISION DEFAULT 0, precio_venta DOUBLE PRECISION DEFAULT 0,
        stock INTEGER DEFAULT 0, stock_min INTEGER DEFAULT 5,
        descripcion TEXT, proveedor_id INTEGER, unidad TEXT DEFAULT 'u.',
        codigo_barras TEXT DEFAULT ''
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS proveedores (
        id %s,
        empresa TEXT, contacto TEXT, telefono TEXT, email TEXT,
        departamento TEXT, direccion TEXT, rnc TEXT,
        dias_credito INTEGER DEFAULT 30, notas TEXT
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS clientes (
        id %s,
        nombre TEXT, telefono TEXT, rnc_cedula TEXT, direccion TEXT, 
        creado_at TIMESTAMPTZ DEFAULT NOW()
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS cotizaciones (
        id %s,
        cliente_id INTEGER,
        items TEXT, -- JSON con los productos
        total DOUBLE PRECISION DEFAULT 0,
        validez_dias INTEGER DEFAULT 15,
        creado_at TIMESTAMPTZ DEFAULT NOW()
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS cuentas_cobrar (
        id %s,
        cliente_id INTEGER,
        concepto TEXT,
        monto DOUBLE PRECISION DEFAULT 0,
        saldo_pendiente DOUBLE PRECISION DEFAULT 0,
        estado TEXT DEFAULT 'pendiente', -- pendiente, pagada
        fecha_vencimiento TEXT,
        creado_at TIMESTAMPTZ DEFAULT NOW()
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS facturas (
        id %s,
        numero TEXT, proveedor_id INTEGER, monto DOUBLE PRECISION DEFAULT 0,
        fecha_emision TEXT, fecha_vencimiento TEXT, fecha_pago TEXT,
        estado TEXT DEFAULT 'pendiente', descripcion TEXT
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS backups (
        id %s,
        filename TEXT, size INTEGER, created_at TEXT,
        data TEXT
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS lista_compras (
        id %s,
        nombre TEXT,
        cantidad INTEGER DEFAULT 1,
        articulo_id INTEGER,
        departamento TEXT,
        estado TEXT DEFAULT 'pendiente',
        encargado TEXT DEFAULT '',
        creado_at TIMESTAMPTZ,
        completado_at TIMESTAMPTZ
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS movimientos_inventario (
        id %s,
        articulo_id INTEGER NOT NULL,
        tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'salida', 'ajuste')),
        cantidad INTEGER NOT NULL,
        stock_anterior INTEGER NOT NULL,
        stock_nuevo INTEGER NOT NULL,
        referencia TEXT DEFAULT '',
        motivo TEXT DEFAULT '',
        creado_at TIMESTAMPTZ DEFAULT NOW()
    )""" % pk_type)

    # Add codigo_barras column if it doesn't exist (for existing databases)
    try:
        execute("ALTER TABLE articulos ADD COLUMN IF NOT EXISTS codigo_barras TEXT DEFAULT ''")
    except Exception:
        pass  # Column already exists or not supported

    # Asegurar que articulo_id exista en lista_compras para vinculación
    try:
        execute("ALTER TABLE lista_compras ADD COLUMN IF NOT EXISTS articulo_id INTEGER")
    except Exception:
        pass

    # Asegurar que las columnas encargado y completado_at existan en lista_compras
    try:
        execute("ALTER TABLE lista_compras ADD COLUMN IF NOT EXISTS encargado TEXT DEFAULT ''")
        execute("ALTER TABLE lista_compras ADD COLUMN IF NOT EXISTS completado_at TIMESTAMPTZ")
    except Exception:
        pass

    # Asegurar que la columna moneda exista en facturas
    try:
        execute("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS moneda TEXT DEFAULT 'DOP'")
    except Exception:
        pass

    # Verify tables exist
    if using_supabase:
        tables = query("SELECT tablename AS name FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
    else:
        tables = query("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t["name"] for t in tables] if tables else []
    print(f"[DB] Tables: {table_names}")
    return tables

@atexit.register
def close_db():
    """Cierra el pool de conexiones explícitamente al apagar el programa para evitar errores de finalización."""
    global _client
    if _client:
        _client.close()
        _client = None