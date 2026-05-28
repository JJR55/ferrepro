"""
Database connection module for Supabase Postgres.
Falls back to Turso HTTP if no Supabase DB URL is configured.
"""
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (ferrepro folder)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL", "").strip().replace(" ", "")
SUPABASE_DEBUG = os.getenv("SUPABASE_DEBUG", "false").lower() in ("1", "true", "yes")

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None

import requests

class SupabaseClient:
    """PostgreSQL client for Supabase using psycopg."""

    def __init__(self, conninfo):
        if psycopg is None:
            raise ImportError("psycopg[binary] is required for Supabase support. Install it in requirements.txt")
        self.conninfo = conninfo
        print(f"[Supabase] Connected to: {conninfo[:60]}...")

    def execute(self, sql, params=None):
        if SUPABASE_DEBUG:
            print(f"[Supabase] SQL: {sql} | params: {params}")
        with psycopg.connect(self.conninfo, autocommit=True) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Compatibilidad: Postgres usa %s en lugar de ? para parámetros
                if params:
                    sql = sql.replace("?", "%s")
                if params is None:
                    cur.execute(sql)
                else:
                    cur.execute(sql, params)
                if cur.description:
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
                return []

    def execute_raw(self, sql, params=None):
        self.execute(sql, params)


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
        else:
            raise Exception("No database provider configured. Set SUPABASE_DATABASE_URL or TURSO_DATABASE_URL.")
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
        descripcion TEXT, proveedor_id INTEGER, unidad TEXT DEFAULT 'u.'
    )""" % pk_type)

    execute("""CREATE TABLE IF NOT EXISTS proveedores (
        id %s,
        empresa TEXT, contacto TEXT, telefono TEXT, email TEXT,
        departamento TEXT, direccion TEXT, rnc TEXT,
        dias_credito INTEGER DEFAULT 30, notas TEXT
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
        departamento TEXT,
        estado TEXT DEFAULT 'pendiente',
        creado_at TIMESTAMPTZ
    )""" % pk_type)

    # Verify tables exist
    if using_supabase:
        tables = query("SELECT tablename AS name FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
    else:
        tables = query("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t["name"] for t in tables] if tables else []
    print(f"[DB] Tables: {table_names}")
    return tables