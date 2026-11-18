from schemas.quote_state import QuoteState


async def run(state: QuoteState) -> QuoteState:
    """
    Temporary network solution stub.

    Mock output used only to validate pipeline integration.
    This will later be replaced by the real network module.
    """

    state.network = {
        "recommended_solution": "Multi-site 10G enterprise WAN with dual-cloud connectivity",
        "architecture": {
            "sites": [
                "Mumbai",
                "Chennai",
                "Hyderabad",
            ],
            "topology": "redundant multi-site",
            "bandwidth": "10G",
            "cloud_connectivity": [
                "AWS",
                "Azure",
            ],
        },
        "products": [
            {
                "name": "Enterprise WAN",
                "quantity": 3,
            },
            {
                "name": "AWS Cloud Connectivity",
                "quantity": 1,
            },
            {
                "name": "Azure Cloud Connectivity",
                "quantity": 1,
            },
        ],
        "bom": [
            {
                "item": "Site connectivity",
                "quantity": 3,
            },
            {
                "item": "Cloud connections",
                "quantity": 2,
            },
        ],
        "cost_range": {
            "currency": "USD",
            "minimum": 0,
            "maximum": 0,
            "note": "Placeholder only; pricing engine not connected.",
        },
        "provisioning": {
            "ready_for_provisioning": False,
            "reason": "Stub output requires validation by the real network solution module.",
        },
    }

    return state