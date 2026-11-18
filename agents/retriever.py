from schemas.quote_state import QuoteState


async def run(state: QuoteState) -> QuoteState:
    """
    Temporary historical-project retrieval stub.

    This mock implementation will later be replaced
    by the real retrieval/RAG module.
    """

    state.similar_projects = [
        {
            "project_id": "SIM-001",
            "summary": "Multi-site 10G connectivity with dual-cloud integration",
            "similarity": 0.91,
            "technologies": [
                "10G WAN",
                "AWS",
                "Azure",
            ],
        },
        {
            "project_id": "SIM-002",
            "summary": "Three-site enterprise connectivity with ServiceNow integration",
            "similarity": 0.84,
            "technologies": [
                "Enterprise WAN",
                "ServiceNow",
            ],
        },
    ]

    return state