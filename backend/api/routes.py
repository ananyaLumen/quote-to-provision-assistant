from uuid import uuid4

from fastapi import APIRouter

from schemas.quote_request import QuoteRequest
from schemas.quote_state import QuoteState


router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "quote-to-provision-backend",
    }


@router.post("/quote", response_model=QuoteState)
async def create_quote(request: QuoteRequest):
    state = QuoteState(
        request_id=str(uuid4()),
        raw_text=request.requirement_text,
    )

    return state