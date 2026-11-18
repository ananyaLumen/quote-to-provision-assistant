from schemas.quote_state import QuoteState


async def run(state: QuoteState) -> QuoteState:
    """
    Temporary validation stub.

    This mock implementation will later be replaced
    by the real validation module.
    """

    state.validation = {
        "feasible": True,
        "confidence": 0.92,
        "checks": [
            {
                "name": "bandwidth",
                "status": "passed",
                "message": "10G bandwidth requirement is supported.",
            },
            {
                "name": "cloud_connectivity",
                "status": "passed",
                "message": "AWS and Azure connectivity can be included.",
            },
            {
                "name": "sla",
                "status": "passed",
                "message": "99.99% SLA requirement is feasible.",
            },
            {
                "name": "timeline",
                "status": "review",
                "message": "Five-month delivery timeline requires implementation planning.",
            },
        ],
        "risks": [
            {
                "severity": "medium",
                "description": "Delivery timeline depends on site readiness and provisioning lead times.",
            }
        ],
        "needs_human_review": False,
    }

    return state