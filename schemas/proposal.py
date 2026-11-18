"""Executive summary written by the proposal agent (the rest of the proposal is assembled deterministically)."""
from pydantic import BaseModel, Field


class ExecutiveSummary(BaseModel):
    headline: str = Field(description="One line naming the solution, e.g. '3-site 10G network with AWS and Azure and a customer portal'.")
    summary: str = Field(description="Three or four sentences for a customer decision-maker. Use only figures present in the facts.")
    key_points: list[str] = Field(description="Three to five bullet points: scope, cost, timeline, main risk.")
    next_steps: list[str] = Field(description="Concrete next actions, taken from the open questions and risks in the facts.")
