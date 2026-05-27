"""
Database connection module for Turso (SQLite in the cloud).
Uses libsql-client for HTTP-based SQLite access.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# We use libsql-client which works with Turso via HTTP
# If not available, we fall back to aiosqlite or requests-based approach
try:
    import libsql_client
    _client = None

    def get_client():
        global _client
        if _client is None:
            _client = libsql_client.create_client_sync(
                url=TURSO_DATABASE_URL,
                auth_token=TURSO_AUTH_TOKEN,
            )
        return _client
except ImportError:
    # Fallback: use requests to call Turso HTTP API directly
    import requests
    _client = None

    def get_client():
        global _client
        if _client is None:
            _client = TursoHttpClient(TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
        return _client


class TursoHttpClient:
    """Simple HTTP client for Turso database using the /v2/pipeline endpoint."""
    
    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.token = token
        self.base_url = f"{self.url}/v2/pipeline"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def execute(self, sql, params=None):
        """Execute a single SQL statement and return results."""
        stmt = {"q": sql, "params": params or []}
        if params:
            stmt["params"] = {"args": params, "named": []}
        
        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt}
            ]
        }
        
        resp = requests.post(self.base_url, json=payload, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for response in data.get("responses", []):
            if "result" in response:
                cols = response["result"].get("cols", [])
                col_names = [c["name"] for c in cols]
                rows = response["result"].get("rows", [])
                for row in rows:
                    obj = {}
                    for i, val in enumerate(row):
                        obj[col_names[i]] = val.get("value") if isinstance(val, dict) else val
                    results.append(obj)
        return results

    def execute_raw(self, sql, params=None):
        """Execute SQL without returning rows (INSERT, UPDATE, DELETE)."""
        stmt = {"q": sql}
        if params:
            if all(isinstance(p, (int, float, str, type(None))) for p in params):
                stmt["params"] = params
        
        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt}
            ]
        }
        
        resp = requests.post(self.base_url, json=payload, headers=self.headers)
        resp.raise_for_status()


# ─── Public API ───

def query(sql, params=None):
    """Execute a SELECT query and return list of dicts."""
    client = get_client()
    if hasattr(client, 'execute'):
        # libsql_client style
        result = client.execute(sql, params or [])
        return [dict(row) for row in result.rows]
    else:
        # HTTP client style
        return client.execute(sql, params)


def execute(sql, params=None):
    """Execute INSERT/UPDATE/DELETE statement."""
    client = get_client()
    if hasattr(client, 'execute'):
        client.execute(sql, params or [])
    else:
        client.execute_raw(sql, params)


def init_db():
    """Create tables if they don't exist."""
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

    # Verify tables exist
    tables = query("SELECT name FROM sqlite_master WHERE type='table'")
    return tables