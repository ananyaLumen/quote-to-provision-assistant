from schemas.quote_state import QuoteState


async def run(state: QuoteState) -> QuoteState:
    """
    Temporary requirement extraction stub.

    This mock implementation will be replaced by the
    real requirement extraction module.
    """

    state.requirement = {
        "sites": [
            "Mumbai",
            "Chennai",
            "Hyderabad",
        ],
        "bandwidth": "10G",
        "sla": "99.99%",
        "clouds": [
            "AWS",
            "Azure",
        ],
        "integrations": [
            "ServiceNow",
        ],
        "timeline": "5 months",
    }

    state.assumptions = [
        "Customer requires connectivity across all three locations.",
        "Cloud connectivity is required for both AWS and Azure.",
    ]

    return state