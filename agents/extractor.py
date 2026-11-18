from backend.llm import CHAT_MODEL, get_client
from schemas.quote_state import QuoteState
from schemas.requirement import ExtractionResult

SYSTEM_PROMPT = """You are a solutions engineer at a network and cloud provider. Turn the customer's request into a structured requirement.

Rules:
- Record only what the customer stated or what follows directly from it. Never invent sites, bandwidth, SLAs, clouds or dates.
- If something is not stated, use null (or an empty list) and add a question to missing_information.
- Normalise numbers: 10G -> bandwidth_mbps 10000; '99.99%' -> sla_uptime_pct 99.99; '5 months' -> timeline_months 5.
- sites are place names exactly as written (e.g. 'Mumbai'). Fill regions only when the place clearly implies a country/region.
- Put anything that needs software to be built (portals, dashboards, API integrations, automation) in software_components.
- Put each interpretation you had to make in assumptions, one short sentence each.
- Keep summary to one or two sentences."""


class ExtractionError(RuntimeError):
    pass


def _check(result: ExtractionResult) -> None:
    req = result.requirement
    if req.sla_uptime_pct is not None and not 0 < req.sla_uptime_pct <= 100:
        raise ExtractionError(f"Extracted SLA of {req.sla_uptime_pct}% is not a valid percentage")
    if req.bandwidth_mbps is not None and req.bandwidth_mbps <= 0:
        raise ExtractionError(f"Extracted bandwidth of {req.bandwidth_mbps} Mbps is not valid")
    if req.timeline_months is not None and req.timeline_months <= 0:
        raise ExtractionError(f"Extracted timeline of {req.timeline_months} months is not valid")


async def run(state: QuoteState) -> QuoteState:
    """Requirement extractor. Reads raw_text; writes requirement and assumptions."""
    text = state.raw_text.strip()
    if not text:
        raise ExtractionError("raw_text is empty")

    options = {}
    if CHAT_MODEL.startswith("gpt-4"):  # newer reasoning models reject a custom temperature
        options["temperature"] = 0

    completion = await get_client().chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format=ExtractionResult,
        **options,
    )
    message = completion.choices[0].message
    if message.refusal:
        raise ExtractionError(f"The model declined to process this request: {message.refusal}")
    if message.parsed is None:
        raise ExtractionError("The model did not return a structured requirement")
    _check(message.parsed)

    state.requirement = message.parsed.requirement.model_dump()
    state.assumptions = message.parsed.assumptions
    return state
