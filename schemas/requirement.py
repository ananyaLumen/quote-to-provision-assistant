"""Structured customer requirement produced by the extractor agent.

The first group of fields keeps the key names of the original extractor stub, so modules written
against it keep working. The numeric fields exist so later modules can compute with the values
instead of re-parsing strings.
"""
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    summary: str = Field(description="One or two sentences describing what the customer wants.")
    sites: list[str] = Field(description="Named locations, data centres or offices to connect. Empty if none stated.")
    bandwidth: str | None = Field(description="Bandwidth as the customer stated it, e.g. '10G'. Null if not stated.")
    sla: str | None = Field(description="Availability SLA as stated, e.g. '99.99%'. Null if not stated.")
    clouds: list[str] = Field(description="Cloud providers to connect to, e.g. ['AWS', 'Azure']. Empty if none.")
    integrations: list[str] = Field(description="Third-party systems to integrate with, e.g. ['ServiceNow']. Empty if none.")
    timeline: str | None = Field(description="Delivery timeline as stated, e.g. '5 months'. Null if not stated.")

    regions: list[str] = Field(description="Countries or regions inferred from the sites. Empty if unclear.")
    topology: str | None = Field(description="e.g. 'full mesh', 'hub-and-spoke', 'point-to-point'. Null unless stated or obvious.")
    bandwidth_mbps: float | None = Field(description="Per-link bandwidth in Mbps (1G = 1000). Null if bandwidth is not stated.")
    sla_uptime_pct: float | None = Field(description="SLA as a number, e.g. 99.99. Null if not stated.")
    timeline_months: float | None = Field(description="Timeline in months (weeks / 4.345, days / 30). Null if not stated.")
    security: list[str] = Field(description="Security or compliance needs, e.g. ['encryption', 'PCI-DSS']. Empty if none.")
    software_components: list[str] = Field(
        description="Software to build, e.g. ['customer portal', 'ticketing integration', 'reporting dashboard']. Empty if none."
    )
    budget: str | None = Field(description="Budget as stated. Null if not stated.")
    missing_information: list[str] = Field(
        description="Questions a solution engineer must answer before quoting (unstated bandwidth, sites, SLA, dates...)."
    )


class ExtractionResult(BaseModel):
    requirement: Requirement
    assumptions: list[str] = Field(
        description="Assumptions made while interpreting incomplete or ambiguous text. Empty if none were needed."
    )
