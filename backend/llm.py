"""Shared OpenAI client and model settings (read from backend/.env)."""
import asyncio
import os
import weakref
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
# Must match the vector(N) size of past_projects.embedding in sql/schema.sql.
EMBEDDING_DIMENSIONS = 1536


class LLMNotConfigured(RuntimeError):
    pass


# An AsyncOpenAI client's connection pool is bound to the event loop it was first used on,
# so keep one client per loop (uvicorn has a single loop; test clients create one per request).
_clients: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, AsyncOpenAI]" = weakref.WeakKeyDictionary()


def _new_client() -> AsyncOpenAI:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise LLMNotConfigured("OPENAI_API_KEY is not set. Add it to backend/.env.")
    return AsyncOpenAI(api_key=api_key)  # base URL comes from OPENAI_BASE_URL when set


def get_client() -> AsyncOpenAI:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # called outside async code: nothing to bind to, so don't cache
        return _new_client()
    if loop not in _clients:
        _clients[loop] = _new_client()
    return _clients[loop]
