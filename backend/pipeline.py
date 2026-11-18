import time
import asyncio
import time

from agents import extractor, retriever, validator, network, software, proposal
from schemas.quote_state import QuoteState


async def run_pipeline(state: QuoteState) -> QuoteState:
    pipeline_start = time.perf_counter()

    state.status = "processing"

    # 1. Requirement extraction
    extractor_start = time.perf_counter()

    state = await extractor.run(state)

    state.timings["extractor"] = round(
        time.perf_counter() - extractor_start,
        4,
    )

    # 2. Historical project retrieval
    retriever_start = time.perf_counter()

    state = await retriever.run(state)

    state.timings["retriever"] = round(
        time.perf_counter() - retriever_start,
        4,
    )

    # 3. Validation
    validator_start = time.perf_counter()

    state = await validator.run(state)

    state.timings["validator"] = round(
        time.perf_counter() - validator_start,
        4,
    )

        # 4. Network and Software solutioning in parallel
    solution_start = time.perf_counter()

    network_state = state.model_copy(deep=True)
    software_state = state.model_copy(deep=True)

    network_result, software_result = await asyncio.gather(
        network.run(network_state),
        software.run(software_state),
    )

    state.network = network_result.network
    state.software = software_result.software

    state.timings["solutioning"] = round(
        time.perf_counter() - solution_start,
        4,
    )
    
        # 5. Proposal generation
    proposal_start = time.perf_counter()

    state = await proposal.run(state)

    state.timings["proposal"] = round(
        time.perf_counter() - proposal_start,
        4,
    )

    state.status = "completed"

    state.timings["total"] = round(
        time.perf_counter() - pipeline_start,
        4,
    )

    return state
