import time
import os
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parent
load_dotenv(dotenv_path=root / '.env')
print('ENV SUPABASE_DATABASE_URL configured:', bool(os.getenv('SUPABASE_DATABASE_URL')))
start = time.time()
try:
    import backend.db as db
    print('import elapsed:', time.time() - start)
    start2 = time.time()
    try:
        tables = db.init_db()
        print('init_db elapsed:', time.time() - start2)
        print('tables count:', len(tables) if tables else 0)
    except Exception as e:
        print('init_db failed after:', time.time() - start2)
        print(type(e).__name__, e)
except Exception as e:
    print('import failed after:', time.time() - start)
    print(type(e).__name__, e)
