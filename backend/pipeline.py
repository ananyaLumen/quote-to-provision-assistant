import time

from schemas.quote_state import QuoteState


async def run_pipeline(state: QuoteState) -> QuoteState:
    """
    Main orchestration function for processing a quote request.

    Individual processing modules will be connected here as they
    become available.
    """

    pipeline_start = time.perf_counter()

    state.status = "processing"

    # Future pipeline stages:
    #
    # state = await extractor.run(state)
    # state = await retriever.run(state)
    # state = await validator.run(state)
    #
    # network + software processing
    #
    # state = await proposal.run(state)

    state.status = "completed"

    state.timings["total"] = round(
        time.perf_counter() - pipeline_start,
        4,
    )

    return state
