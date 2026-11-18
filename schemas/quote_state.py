from typing import Any
from pydantic import BaseModel, Field


class QuoteState(BaseModel):
    # Identity
    request_id: str

    # Original customer input
    raw_text: str

    # Requirement extraction
    requirement: dict[str, Any] | None = None
    assumptions: list[str] = Field(default_factory=list)

    # Retrieval / validation
    similar_projects: list[dict[str, Any]] = Field(default_factory=list)
    validation: dict[str, Any] | None = None

    # Solution branches
    network: dict[str, Any] | None = None
    software: dict[str, Any] | None = None

    # Final output
    proposal: dict[str, Any] | None = None

    # Pipeline metadata
    status: str = "received"
    timings: dict[str, float] = Field(default_factory=dict)