from schemas.quote_state import QuoteState


async def run(state: QuoteState) -> QuoteState:
    """
    Temporary software solution stub.

    Mock output used only to validate pipeline integration.
    This will later be replaced by the real software module.
    """

    state.software = {
        "recommended_solution": "Customer monitoring and service-management portal",

        "stack": [
            "React",
            "FastAPI",
            "REST API",
        ],

        "architecture": {
            "frontend": "React web portal",
            "backend": "FastAPI service layer",
            "integration": "REST-based integration",
        },

        "features": [
            "Bandwidth monitoring",
            "Service status visibility",
            "Ticket creation",
            "Ticket status tracking",
        ],

        "integrations": [
            {
                "system": "ServiceNow",
                "purpose": "Ticket creation and status synchronization",
                "status": "planned",
            }
        ],

        "deployment": {
            "environment": "Cloud-hosted",
            "timeline": "Aligned with 5-month customer delivery target",
        },

        "risks": [
            {
                "severity": "medium",
                "description": "ServiceNow API access and integration details must be confirmed.",
            }
        ],
    }

    return state