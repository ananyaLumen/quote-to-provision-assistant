from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    requirement_text: str = Field(
        ...,
        min_length=1,
        description="Customer requirement in natural language",
    )