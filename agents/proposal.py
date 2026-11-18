"""Proposal generator. Reads the completed QuoteState; writes proposal.

Everything is assembled deterministically from the other agents' output (costs, roadmap, risks, provisioning JSON). Only the
executive summary is written by the LLM, and it is discarded in favour of a plain template if it mentions any number that is
not in the facts it was given.
"""
import json
import math
import re
import statistics

from backend.llm import CHAT_MODEL, get_client
from schemas.proposal import ExecutiveSummary
from schemas.quote_state import QuoteState

WEEKS_PER_MONTH = 4.345
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

SYSTEM_PROMPT = """You write the executive summary of a network and software proposal for a customer decision-maker.
Use ONLY the facts provided. Every number (costs, months, counts) must appear in the facts exactly as written there; never round, convert,
abbreviate (no '$505K') or invent figures. Write amounts in whole dollars as given, e.g. $504,744. Be plain and specific.
Never promise or imply that a delivery date will be met: delivery_lower_bound_months is only a lower bound that excludes site surveys, and
requested_timeline_achievable says whether the customer's date is realistic. If it is false or null, say the timeline is at risk or unconfirmed.
If the design needs conditions (site surveys, open questions), say so honestly instead of promising delivery."""


def _numbers(text: str) -> set[float]:
    values = set()
    for token in _NUMBER.findall(text):
        try:
            values.add(float(token.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return values


def _roadmap(state: QuoteState) -> dict:
    net, sw, req = state.network or {}, state.software or {}, state.requirement or {}
    checks = (state.validation or {}).get("checks", [])
    no_presence = [s for c in checks if c["name"] == "site_coverage" for s in c.get("evidence", {}).get("without_presence", [])]
    tracks, notes = [], []

    net_weeks = 0
    if net.get("status") == "designed":
        net_weeks = max(1, math.ceil((net.get("lead_time_days") or 0) / 7))
        tracks.append({"name": "Network and service", "duration_weeks": net_weeks,
                       "steps": [{"name": "Order and provision (catalog lead time)", "start_week": 0, "end_week": net_weeks}]})
        if no_presence:
            notes.append(f"The network track covers catalog lead time only. Site survey and off-net access for {', '.join(no_presence)} "
                         "have no lead-time data and are not included.")

    sw_weeks = 0
    if sw.get("required"):
        cursor, steps = 0.0, []
        for phase in sw["phases"]:
            steps.append({"name": phase["name"], "start_week": round(cursor, 1), "end_week": round(cursor + phase["duration_weeks"], 1),
                          "milestone": phase["milestone"]})
            cursor += phase["duration_weeks"]
        sw_weeks = cursor
        tracks.append({"name": "Software", "duration_weeks": round(sw_weeks, 1), "steps": steps})

    total_weeks = max(net_weeks, sw_weeks)
    critical = max(tracks, key=lambda t: t["duration_weeks"])["name"] if tracks else None
    requested = req.get("timeline_months")
    durations = [p["duration_months"] for p in state.similar_projects if p.get("duration_months")]
    computed_months = round(total_weeks / WEEKS_PER_MONTH, 1)
    within_computed = (total_weeks <= requested * WEEKS_PER_MONTH) if requested and tracks else None
    # The computed figure uses catalog lead times and the software plan only, so it is a lower bound. A request is only
    # called achievable if it is also no shorter than the shortest comparable past project (same rule as the validator).
    shorter_than_all_similar = bool(requested and durations and requested < min(durations))
    integrated = {
        "go_live_week": round(total_weeks, 1), "total_months": computed_months, "critical_path": critical,
        "requested_months": requested,
        "computed_within_requested": within_computed,
        "fits_requested_timeline": None if within_computed is None else (within_computed and not shorter_than_all_similar),
    }
    if durations:
        median = statistics.median(durations)
        span = f"{min(durations)} months" if min(durations) == max(durations) else f"{min(durations)} to {max(durations)} months"
        integrated["benchmark"] = f"Similar past projects took {span} (median {median:g})."
        integrated["benchmark_median_months"] = median
        if tracks and computed_months < median:
            notes.append(f"The computed {computed_months} months is a lower bound (catalog lead times and the software plan only); "
                         f"similar projects took a median of {median:g} months.")
    return {"tracks": tracks, "integrated": integrated, "notes": notes}


def _costs(state: QuoteState) -> dict:
    net, sw = state.network or {}, state.software or {}
    net_range = net.get("cost_range") or {}
    sw_cost = (sw.get("effort") or {}).get("cost") or {}
    net_min, net_max = net_range.get("minimum", 0), net_range.get("maximum", 0)
    sw_min, sw_max = sw_cost.get("minimum", 0), sw_cost.get("maximum", 0)
    priced = net.get("status") == "designed"
    return {
        "currency": "USD",
        "network": {"first_year_minimum": net_min, "first_year_maximum": net_max, **(net.get("cost_summary") or {})} if priced else None,
        "software": {"minimum": sw_min, "maximum": sw_max},
        # None (not zero) when nothing could be priced, so nobody reads "$0" as a quote.
        "total_first_year": {"minimum": round(net_min + sw_min, 2), "maximum": round(net_max + sw_max, 2)} if priced else None,
        "basis": "Network: catalog list prices (setup + 12 months) with a planning contingency for the maximum. "
                 "Software: model effort estimate x blended day rate. Taxes and discounts excluded.",
    }


def _facts(state, costs, roadmap) -> dict:
    req, net, sw, val = state.requirement, state.network or {}, state.software or {}, state.validation or {}
    integrated = roadmap["integrated"]
    whole = lambda d: {k: round(v) for k, v in d.items()}  # whole dollars read better than 504744.0
    return {
        "requirement": req.get("summary"), "sites": req.get("sites"), "bandwidth": req.get("bandwidth"), "sla": req.get("sla"),
        "clouds": req.get("clouds"), "requested_timeline": req.get("timeline"),
        "network_solution": net.get("recommended_solution"), "network_monthly_cost": round((net.get("cost_summary") or {}).get("monthly") or 0),
        "software_solution": sw.get("recommended_solution") if sw.get("required") else None,
        "software_cost_range": whole(costs["software"]) if sw.get("required") else None,
        "software_weeks": round((sw.get("effort") or {}).get("duration_weeks") or 0) or None,
        "total_first_year_cost_range": whole(costs["total_first_year"]) if costs["total_first_year"] else None, "currency": "USD",
        # A lower bound only: it excludes site surveys and off-net lead times. Do not present it as a delivery date.
        "delivery_lower_bound_months": integrated["total_months"] or None,
        "similar_projects_duration": integrated.get("benchmark"),
        "requested_timeline_achievable": integrated["fits_requested_timeline"],
        "verdict": val.get("verdict"), "confidence": val.get("confidence"),
        "top_risks": [r["description"] for r in sorted(val.get("risks", []), key=lambda r: SEVERITY_ORDER[r["severity"]])[:3]],
        "open_questions": req.get("missing_information"),
    }


def _template_summary(facts: dict, costs: dict) -> dict:
    total = costs["total_first_year"]
    headline = facts["network_solution"] or "Proposal pending more information"
    cost = (f"Estimated first-year cost is ${total['minimum']:,.0f} to ${total['maximum']:,.0f}. " if total
            else "No price can be given until sites and bandwidth are confirmed. ")
    return {
        "headline": headline,
        "summary": (f"{headline}. {cost}"
                    f"Assessment: {str(facts['verdict']).replace('_', ' ')} (confidence {facts['confidence']}). "
                    "Open questions and risks listed below must be resolved before commercial sign-off."),
        "key_points": [f"Top risk: {r}" for r in facts["top_risks"]] or ["No major risks flagged."],
        "next_steps": list(facts["open_questions"] or []) or ["Confirm scope with the customer."],
    }


async def _executive_summary(facts: dict, costs: dict) -> tuple[dict, str]:
    facts_text = json.dumps(facts, indent=1, default=str)
    options = {"temperature": 0.2} if CHAT_MODEL.startswith("gpt-4") else {}
    completion = await get_client().chat.completions.parse(
        model=CHAT_MODEL, response_format=ExecutiveSummary,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"Facts:\n{facts_text}"}], **options)
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        return _template_summary(facts, costs), "template"
    written = parsed.model_dump()
    unknown = _numbers(json.dumps(written)) - _numbers(facts_text) - {0.0, 1.0}
    if unknown:  # the model produced a figure that is not in the facts: don't ship it
        return _template_summary(facts, costs), "template"
    return written, "llm"


async def run(state: QuoteState) -> QuoteState:
    """Proposal generator. Reads the completed QuoteState; writes proposal."""
    if not state.requirement or state.validation is None or state.network is None or state.software is None:
        raise ValueError("proposal needs requirement, validation, network and software")
    net, sw, val = state.network, state.software, state.validation

    costs, roadmap = _costs(state), _roadmap(state)
    facts = _facts(state, costs, roadmap)
    summary, source = await _executive_summary(facts, costs)

    risks = [{**r, "source": "validation"} for r in val.get("risks", [])] + [{**r, "source": "software"} for r in sw.get("risks", [])]
    risks.sort(key=lambda r: SEVERITY_ORDER[r["severity"]])
    designed = net.get("status") == "designed"

    state.proposal = {
        "title": f"Proposal: {summary['headline']}",
        "executive_summary": summary["summary"],
        "summary_detail": {**summary, "source": source},
        "customer_requirements": state.requirement,
        "network_solution": net,
        "software_solution": sw,
        "validation_summary": {
            "verdict": val.get("verdict"), "feasible": val.get("feasible"), "confidence": val.get("confidence"),
            "confidence_basis": val.get("confidence_basis"), "needs_human_review": val.get("needs_human_review"),
            "checks": [{k: c[k] for k in ("name", "status", "message")} for c in val.get("checks", [])],
        },
        "similar_projects": [{k: p.get(k) for k in ("project_id", "name", "similarity", "duration_months", "primary_bandwidth",
                                                    "bandwidth_unit", "source", "lessons_learned")} for p in state.similar_projects],
        "cost_summary": costs,
        "roadmap": roadmap,
        "risks": risks,
        "assumptions": [*state.assumptions, *net.get("assumptions", []), *sw.get("assumptions", []), *roadmap["notes"]],
        "open_questions": state.requirement.get("missing_information") or [],
        "commercial_status": {
            "pricing_available": designed,
            "message": ("Pricing is a planning estimate from catalog list prices; final commercial pricing needs approval."
                        if designed else "Pricing is not available until sites and bandwidth are confirmed."),
        },
        "provisioning_status": {
            "ready": False,
            "message": (net.get("provisioning") or {}).get("reason", "Provisioning requires validation and approved pricing."),
        },
        "provisioning_json": (net.get("provisioning") or {}).get("payload"),
    }
    return state
