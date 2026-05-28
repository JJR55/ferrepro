#!/usr/bin/env python
"""
Test script for Supabase connection validation.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL", "").strip()

print(f"[TEST] Loading environment from: {env_path}")
print(f"[TEST] SUPABASE_DATABASE_URL configured: {bool(SUPABASE_DATABASE_URL)}")

if not SUPABASE_DATABASE_URL:
    print("[ERROR] SUPABASE_DATABASE_URL not set in .env")
    sys.exit(1)

# Mask the password in output for security
masked_url = SUPABASE_DATABASE_URL.replace(SUPABASE_DATABASE_URL.split(':')[2].split('@')[0], "***PASSWORD***")
print(f"[TEST] Connection string (masked): {masked_url}")

try:
    import psycopg
    from psycopg.rows import dict_row
    print("[OK] psycopg module imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import psycopg: {e}")
    sys.exit(1)

print("\n[TEST] Attempting connection to Supabase...")
try:
    with psycopg.connect(SUPABASE_DATABASE_URL, autocommit=True) as conn:
        print("[OK] Connected to Supabase!")
        
        # Test: Create a simple test table
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"[OK] PostgreSQL version: {version}")
            
            # Verify our expected tables structure
            cur.execute("""
                SELECT tablename FROM pg_catalog.pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            tables = cur.fetchall()
            if tables:
                table_names = [t["tablename"] for t in tables]
                print(f"[OK] Found {len(table_names)} tables: {table_names}")
            else:
                print("[INFO] No tables found yet (database is empty)")
    
    print("\n[SUCCESS] Supabase connection validated successfully!")
    sys.exit(0)
    
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    print(f"[ERROR] Error type: {type(e).__name__}")
    sys.exit(1)
