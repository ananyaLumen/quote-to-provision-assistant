# Module Integration Contract v1

All processing modules integrate through the shared QuoteState.

## Standard Interface

Each module should expose an asynchronous run function:

async def run(state: QuoteState) -> QuoteState

A module may read fields required for its processing but should only modify fields assigned to that module.

## Module Ownership

### Requirement Extractor

Reads:
- raw_text

Writes:
- requirement
- assumptions

### Retriever

Reads:
- requirement

Writes:
- similar_projects

### Validator

Reads:
- requirement
- similar_projects

Writes:
- validation

### Network Solution

Reads:
- requirement
- validation

Writes:
- network

### Software Solution

Reads:
- requirement
- validation

Writes:
- software

### Proposal Generator

Reads:
- completed QuoteState

Writes:
- proposal

### Pipeline

Writes:
- status
- timings

The pipeline controls execution order and orchestration.

## Rules

1. Modules must accept QuoteState as their integration input.
2. Modules return QuoteState.
3. Modules should modify only their owned output fields.
4. Modules must not rename top-level QuoteState fields.
5. Module-specific internal data structures may evolve inside the module's assigned field.
6. Changes to shared fields must be coordinated before implementation.
7. Modules should raise an exception rather than silently returning invalid state.