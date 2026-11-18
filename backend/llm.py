"""Shared OpenAI client and model settings (read from backend/.env)."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
# Must match the vector(N) size of past_projects.embedding in sql/schema.sql.
EMBEDDING_DIMENSIONS = 1536


class LLMNotConfigured(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_client() -> AsyncOpenAI:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise LLMNotConfigured("OPENAI_API_KEY is not set. Add it to backend/.env.")
    return AsyncOpenAI(api_key=api_key)
