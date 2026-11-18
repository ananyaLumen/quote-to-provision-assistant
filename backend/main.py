import logging
import os
import re
import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.data_routes import router as data_router
from backend.api.routes import router

log = logging.getLogger("uvicorn.error")


def _cors_origin_regex() -> str:
    """Origins allowed to call the API from a browser.

    Vite runs with --host 0.0.0.0, so the UI can be opened as localhost, a private IP,
    or this machine's hostname, on any port. Extra origins go in CORS_ORIGINS (comma-separated).
    """
    hosts = {"localhost", "127.0.0.1", socket.gethostname(), socket.getfqdn()}
    hosts |= {
        re.sub(r"^https?://|:\d+$", "", o.strip().rstrip("/"))
        for o in os.getenv("CORS_ORIGINS", "").split(",")
        if o.strip()
    }
    named = "|".join(re.escape(h) for h in sorted(hosts) if h)
    private = r"10(\.\d{1,3}){3}|192\.168(\.\d{1,3}){2}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2}"
    return rf"(?i)^https?://({named}|{private})(:\d+)?$"


CORS_ORIGIN_REGEX = _cors_origin_regex()

app = FastAPI(
    title="Quote-to-Provision Assistant API",
    description="Backend API for the Quote-to-Provision hackathon solution",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_rejected_origin(request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin and request.method == "OPTIONS" and response.status_code == 400:
        log.warning("CORS preflight rejected for origin %s (set CORS_ORIGINS to allow it)", origin)
    return response


app.include_router(router)
app.include_router(data_router)