"""Software solution. Reads requirement and validation; writes software.

The LLM proposes the stack, architecture, database/data-integration design, phases and per-epic effort ranges; code then
computes the totals and cost from those ranges and checks the plan against the customer's timeline.
Output keeps the keys of the original stub and adds database, phases, effort and assumptions.
"""
import os

from backend.llm import CHAT_MODEL, get_client
from schemas.quote_state import QuoteState
from schemas.software import SoftwarePlan

DAY_RATE_USD = float(os.getenv("SOFTWARE_DAY_RATE_USD", "800"))  # blended rate, an assumption: set it to your delivery rate card
WEEKS_PER_MONTH = 4.345

# The data layer the solution can build on, so the database design reuses what exists.
PLATFORM_CONTEXT = """Existing platform (reuse it rather than redesigning it):
- Stack already in use: React frontend, FastAPI backend, Supabase (PostgreSQL) with Row Level Security.
- Tables available: product_catalog, locations (data centres, cloud on-ramps), uni_sites and whitelisted_ports (network ports and devices),
  evcs (Ethernet connections), provisioning_requests (history of build/modify/delete orders with status), service_order_failures,
  inventory_dq_issues, mcgw_pricing, provisioning_orders / bom_items / site_allocations (quotes and their BOM).
- Customer-facing data must go through the backend API; the browser never gets direct database access."""

SYSTEM_PROMPT = f"""You are a software architect planning delivery of the custom software in a customer's network project.

{PLATFORM_CONTEXT}

Rules:
- Plan only what the requirement asks for (software_components and integrations). Do not add unrelated features.
- Provide exactly five phases in this order: Requirements, Design, Build, Test, Deployment. Each has epics with person_days_min and person_days_max
  (max >= min) and a milestone. Keep effort realistic for a small team (3-6 people) and per-phase duration_weeks consistent with that effort.
- Name the real systems the customer mentioned in integrations; do not invent integrations.
- Where the customer's request leaves something open (API access, authentication, data volumes), state it as a risk with a mitigation.
- Prefer the existing stack unless the requirement forces otherwise.
- database.entities must list both the existing tables you reuse (existing_table true) and every NEW table the software needs, such as
  tickets, usage/bandwidth samples or integration sync state (existing_table false). A portal that stores its own data always needs new tables.
- List only software-delivery risks. The network project risks you are given are context for scheduling: do not repeat them as risks."""


def _facts(state: QuoteState) -> str:
    req = state.requirement
    lessons = [line for p in state.similar_projects[:3] for line in (p.get("lessons_learned") or [])][:6]
    risks = [r["description"] for r in (state.validation or {}).get("risks", []) if r["severity"] in ("high", "medium")][:4]
    return "\n".join([
        f"Customer requirement: {req.get('summary')}",
        f"Software to build: {', '.join(req.get('software_components') or []) or 'none listed'}",
        f"Integrations: {', '.join(req.get('integrations') or []) or 'none'}",
        f"Security needs: {', '.join(req.get('security') or []) or 'none stated'}",
        f"Target delivery: {req.get('timeline') or 'not stated'}",
        f"Network project risks to be aware of: {'; '.join(risks) or 'none flagged'}",
        f"Lessons from similar past projects: {'; '.join(lessons) or 'none available'}",
    ])


def _not_required(state: QuoteState) -> QuoteState:
    state.software = {
        "required": False,
        "recommended_solution": "No custom software was requested.",
        "stack": [], "features": [], "integrations": [], "phases": [], "risks": [],
        "effort": {"person_days": {"minimum": 0, "maximum": 0}, "duration_weeks": 0,
                   "cost": {"currency": "USD", "minimum": 0, "maximum": 0}},
    }
    return state


async def run(state: QuoteState) -> QuoteState:
    """Software solution. Reads requirement and validation; writes software."""
    req = state.requirement
    if not req:
        raise ValueError("software solution needs state.requirement")
    if not (req.get("software_components") or req.get("integrations")):
        return _not_required(state)

    options = {"temperature": 0.2} if CHAT_MODEL.startswith("gpt-4") else {}
    completion = await get_client().chat.completions.parse(
        model=CHAT_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": _facts(state)}],
        response_format=SoftwarePlan,
        **options,
    )
    message = completion.choices[0].message
    if message.refusal or message.parsed is None:
        raise RuntimeError(f"The model did not return a software plan: {message.refusal or 'empty response'}")
    plan = message.parsed

    names = [phase.name for phase in plan.phases]
    if names != ["Requirements", "Design", "Build", "Test", "Deployment"]:
        raise RuntimeError(f"Software plan has unexpected phases: {names}")

    day_min = sum(e.person_days_min for p in plan.phases for e in p.epics)
    day_max = sum(max(e.person_days_max, e.person_days_min) for p in plan.phases for e in p.epics)
    weeks = sum(p.duration_weeks for p in plan.phases)

    risks = [r.model_dump() for r in plan.risks]
    target_months = req.get("timeline_months")
    if target_months and weeks > target_months * WEEKS_PER_MONTH:
        risks.append({"severity": "high", "description": f"The plan needs about {weeks:.0f} weeks ({weeks / WEEKS_PER_MONTH:.1f} months) "
                      f"but the customer wants delivery in {target_months:g} months.",
                      "mitigation": "Reduce first-release scope, add capacity, or agree a later go-live for the software."})

    state.software = {
        "required": True,
        "recommended_solution": plan.recommended_solution,
        "stack": plan.stack,
        "architecture": plan.architecture.model_dump(),
        "features": plan.features,
        "integrations": [{**i.model_dump(), "status": "planned"} for i in plan.integrations],
        "database": plan.database.model_dump(),
        "phases": [p.model_dump() for p in plan.phases],
        "deployment": {**plan.deployment.model_dump(), "environment": plan.architecture.hosting,
                       "timeline": f"About {weeks:.0f} weeks in total across the five phases."},
        "risks": risks,
        "effort": {
            "person_days": {"minimum": round(day_min, 1), "maximum": round(day_max, 1)},
            "duration_weeks": round(weeks, 1),
            "day_rate_usd": DAY_RATE_USD,
            "cost": {"currency": "USD", "minimum": round(day_min * DAY_RATE_USD, 2), "maximum": round(day_max * DAY_RATE_USD, 2)},
        },
        "assumptions": [
            f"Cost uses a blended rate of ${DAY_RATE_USD:,.0f} per person-day (SOFTWARE_DAY_RATE_USD); replace it with your delivery rate card.",
            "Effort and duration are model estimates from the requirement scope, not from past delivery data: calibrate them with the delivery team.",
            "The five phases run sequentially; the duration is the sum of the phase durations.",
        ],
    }
    return state
