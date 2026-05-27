"""
Database connection module for Turso (SQLite in the cloud).
Uses requests-based HTTP client to communicate with Turso's HTTP API.
"""
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (ferrepro folder)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")


def normalize_turso_url(url):
    """
    Convert Turso URL to HTTPS format.
    - 'libsql://ferrepro-jjr55.aws-us-east-1.turso.io' 
      → 'https://ferrepro-jjr55.aws-us-east-1.turso.io'
    - If already https://, keep as is
    """
    url = url.strip()
    # Remove libsql:// protocol prefix
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    # Ensure it starts with https://
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip('/')


import requests

class TursoHttpClient:
    """HTTP client for Turso database using the /v2/pipeline endpoint."""
    
    def __init__(self, url, token):
        self.original_url = url
        self.token = token
        # Convert libsql:// to https://
        self.db_url = normalize_turso_url(url)
        self.base_url = f"{self.db_url}/v2/pipeline"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        print(f"[Turso] Connected to: {self.db_url}")

    def execute(self, sql, params=None):
        """Execute a SQL query and return results as list of dicts.
        
        Uses the correct Turso HTTP API format:
        { "type": "execute", "stmt": { "sql": "...", "args": [...] } }
        ""
        stmt = {"sql": sql}

        # Turso /v2/pipeline expects args as typed internal enum values.
        # If we send raw strings/ints, Turso can reject with:
        # "JSON parse error: invalid type ... expected internally tagged enum Value"
        if params is not None:
            def to_turso_value(v):
                if v is None:
                    return {"type": "null"}
                if isinstance(v, bool):
                    return {"type": "bool", "value": v}
                if isinstance(v, int) and not isinstance(v, bool):
                    return {"type": "integer", "value": str(v)}
                if isinstance(v, float):
                    return {"type": "float", "value": v}
                return {"type": "text", "value": str(v)}


            stmt["args"] = [to_turso_value(p) for p in params]

        payload = {"requests": [{"type": "execute", "stmt": stmt}]}

        resp = requests.post(self.base_url, json=payload, headers=self.headers)

        if not resp.ok:
            raise Exception(f"Turso error. URL: {self.base_url}. Status: {resp.status_code}. Body: {resp.text[:300]}")
        
        data = resp.json()
        
        # Parse Turso HTTP API response
        # Response format: {"results": [{"type": "ok", "response": {"type": "execute", "result": {"cols": [...], "rows": [[...]]}}}]}
        # or: {"responses": [{"result": {"cols": [...], "rows": [[...]]}}]}
        
        raw_results = data.get("results", data.get("responses", []))
        parsed_rows = []
        
        for item in raw_results:
            # Handle both v2/pipeline and v2 formats
            if "response" in item:
                inner = item["response"]
            else:
                inner = item
            
            if "result" in inner:
                result_part = inner["result"]
            else:
                result_part = inner
            
            cols = result_part.get("cols", [])
            if not cols:
                continue
            
            col_names = [c.get("name", str(i)) for i, c in enumerate(cols)]
            rows = result_part.get("rows", [])
            
            for row in rows:
                obj = {}
                for i, val in enumerate(row):
                    # Turso returns: {"type": "integer", "value": "1"}, {"type": "null"} or null
                    if val is None:
                        obj[col_names[i]] = None
                    elif isinstance(val, dict):
                        t = val.get("type")
                        if t == "null":
                            obj[col_names[i]] = None
                        else:
                            obj[col_names[i]] = val.get("value", val)
                    else:
                        obj[col_names[i]] = val
                parsed_rows.append(obj)
        
        return parsed_rows

    def execute_raw(self, sql, params=None):
        """Execute SQL without returning rows (INSERT, UPDATE, DELETE)."""
        self.execute(sql, params)
        return


# ─── Client singleton ───
_client = None

def get_client():
    global _client
    if _client is None:
        _client = TursoHttpClient(TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
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
    print(f"[Turso] Initializing database...")
    
    execute("""CREATE TABLE IF NOT EXISTS articulos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE, nombre TEXT, departamento TEXT,
        precio_costo REAL DEFAULT 0, precio_venta REAL DEFAULT 0,
        stock INTEGER DEFAULT 0, stock_min INTEGER DEFAULT 5,
        descripcion TEXT, proveedor_id INTEGER, unidad TEXT DEFAULT 'u.'
    )""")
    
    execute("""CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa TEXT, contacto TEXT, telefono TEXT, email TEXT,
        departamento TEXT, direccion TEXT, rnc TEXT,
        dias_credito INTEGER DEFAULT 30, notas TEXT
    )""")
    
    execute("""CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT, proveedor_id INTEGER, monto REAL DEFAULT 0,
        fecha_emision TEXT, fecha_vencimiento TEXT,
        estado TEXT DEFAULT 'pendiente', descripcion TEXT
    )""")

    execute("""CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT, size INTEGER, created_at TEXT,
        data TEXT
    )""")

    execute("""CREATE TABLE IF NOT EXISTS lista_compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        cantidad INTEGER DEFAULT 1,
        departamento TEXT,
        estado TEXT DEFAULT 'pendiente', -- 'pendiente', 'recibido', 'faltante'
        creado_at TEXT
    )""")

    # Verify tables exist
    tables = query("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t["name"] for t in tables] if tables else []
    print(f"[Turso] Tables: {table_names}")
    return tables