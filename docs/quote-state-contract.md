# Quote State Contract v1

QuoteState is the shared state object passed between backend processing modules.

## Core Rule

Each module receives the shared QuoteState and updates only the fields it owns.

## Fields

request_id
- Owner: Backend
- Unique identifier for each quote request.

raw_text
- Owner: Backend
- Original customer requirement text.
- Must not be modified by downstream modules.

requirement
- Owner: Requirement Extraction
- Structured representation of the customer requirement.

assumptions
- Owner: Requirement Extraction
- Assumptions made while interpreting incomplete or ambiguous requirements.

similar_projects
- Owner: Retrieval
- Relevant historical or reference projects.

validation
- Owner: Validation
- Validation results, feasibility findings, risks and warnings.

network
- Owner: Network Solution
- Network architecture, products, BOM, cost and provisioning information.

software
- Owner: Software Solution
- Software stack, architecture, integrations, deployment and implementation information.

proposal
- Owner: Proposal Generation
- Final consolidated proposal/quote output.

status
- Owner: Backend/Pipeline
- Current processing state of the request.

timings
- Owner: Backend/Pipeline
- Processing times for pipeline stages.

## Module Contract

Modules should conceptually follow:

async def run(state: QuoteState) -> QuoteState

Modules should only update their assigned section of QuoteState.

## Change Control

QuoteState v1 is the shared integration contract.

Changes to top-level fields must be agreed with the Team Lead before implementation.

Module-specific internal structures may evolve independently as long as they remain within their assigned top-level field.