from schemas.quote_state import QuoteState


async def run(state: QuoteState) -> QuoteState:
    """
    Temporary proposal generation stub.

    Combines upstream mock outputs into a consolidated
    proposal structure for end-to-end integration testing.
    """

    state.proposal = {
        "title": "Quote-to-Provision Solution Proposal",

        "executive_summary": (
            "Proposed solution for multi-site 10G connectivity "
            "with AWS and Azure cloud connectivity, supported by "
            "a customer monitoring portal and ServiceNow integration."
        ),

        "customer_requirements": state.requirement,

        "network_solution": state.network,

        "software_solution": state.software,

        "validation_summary": state.validation,

        "assumptions": state.assumptions,

        "commercial_status": {
            "pricing_available": False,
            "message": "Final commercial pricing has not yet been calculated.",
        },

        "provisioning_status": {
            "ready": False,
            "message": (
                "Provisioning requires final technical validation "
                "and approved commercial pricing."
            ),
        },
    }

    return state