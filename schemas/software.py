"""Structured software plan produced by the software agent (the LLM fills this in; code computes the totals)."""
from typing import Literal

from pydantic import BaseModel, Field


class Epic(BaseModel):
    name: str
    description: str
    person_days_min: float = Field(description="Optimistic effort for this epic in person-days.")
    person_days_max: float = Field(description="Pessimistic effort for this epic in person-days (>= min).")


class Phase(BaseModel):
    name: Literal["Requirements", "Design", "Build", "Test", "Deployment"]
    epics: list[Epic]
    milestone: str = Field(description="What is true when this phase is done.")
    duration_weeks: float = Field(description="Calendar duration of the phase assuming a small team working in parallel.")


class Integration(BaseModel):
    system: str
    purpose: str
    approach: str = Field(description="How it is integrated, e.g. REST API, webhook, scheduled sync.")


class Entity(BaseModel):
    name: str
    purpose: str
    key_fields: list[str]
    existing_table: bool = Field(description="True if this is a table that already exists in the platform, False if it must be created.")


class Architecture(BaseModel):
    frontend: str
    backend: str
    integration: str
    hosting: str


class Database(BaseModel):
    engine: str
    rationale: str
    entities: list[Entity]
    data_integration: list[str] = Field(description="How data from the customer's systems and Lumen's tables flows in and out.")


class Deployment(BaseModel):
    environments: list[str]
    ci_cd: str
    rollout: str


class Risk(BaseModel):
    severity: Literal["low", "medium", "high"]
    description: str
    mitigation: str


class SoftwarePlan(BaseModel):
    recommended_solution: str
    stack: list[str]
    architecture: Architecture
    features: list[str]
    integrations: list[Integration]
    database: Database
    phases: list[Phase] = Field(description="Exactly the five phases, in order: Requirements, Design, Build, Test, Deployment.")
    deployment: Deployment
    risks: list[Risk]
