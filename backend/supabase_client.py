"""Supabase client for the backend. Server-side only: uses the secret key, which bypasses RLS."""
import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
# The secret key is required: every table has RLS enabled with no policies, so the publishable key sees nothing.
SUPABASE_SECRET_KEY = (os.getenv("SUPABASE_SECRET_KEY") or "").strip()

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SECRET_KEY in backend/.env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def get_supabase() -> Client:
    return supabase
