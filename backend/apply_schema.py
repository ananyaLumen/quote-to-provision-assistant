"""Create the database schema from sql/schema.sql using a direct Postgres connection.

Requires DATABASE_URL in backend/.env (Supabase > Connect > connection string). If the password
contains special characters such as '@', URL-encode them (e.g. '@' -> '%40').
If you prefer, paste sql/schema.sql into the Supabase SQL Editor instead.
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

url = (os.getenv("DATABASE_URL") or "").strip()
if not url:
    sys.exit("DATABASE_URL is not set in backend/.env. Paste sql/schema.sql into the Supabase SQL Editor instead.")

schema = (Path(__file__).parent / "sql" / "schema.sql").read_text(encoding="utf-8")

try:
    with psycopg2.connect(url, connect_timeout=15) as conn, conn.cursor() as cur:
        cur.execute(schema)
except psycopg2.OperationalError as exc:
    sys.exit(f"Could not connect: {exc}\nIf the host is IPv6-only, use the Session pooler connection string instead.")

print("Schema applied.")
