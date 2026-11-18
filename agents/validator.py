"""Validator. Reads requirement and similar_projects; writes validation.

Every check is computed from the database (catalog, locations, inventory, order history); nothing here calls an LLM.
Output keeps the shape of the original stub (feasible / confidence / checks / risks / needs_human_review).
"""
import asyncio
import statistics

from backend import design, queries
from schemas.quote_state import QuoteState

# How much each check contributes to the confidence score, and how a status is scored.
WEIGHTS = {"completeness": 0.15, "bandwidth": 0.15, "sla": 0.15, "site_coverage": 0.20,
           "cloud_connectivity": 0.10, "timeline": 0.15, "delivery_history": 0.10}
STATUS_SCORE = {"passed": 1.0, "review": 0.5, "failed": 0.0}

HIGH_FAILURE_RATE = 15.0  # % of finished orders that failed
ELEVATED_FAILURE_RATE = 5.0
IPVPN_FAMILIES = {"dycon_ipvpn": ("ACTIVATE", "Dycon IPVPN activation"), "edge_ipvpn": ("BUILD", "Edge IPVPN build")}
INTERNET_FAMILIES = {"edge_internet": ("BUILD", "Edge Internet build")}


def _check(name, status, message, **evidence):
    return {"name": name, "status": status, "message": message, **({"evidence": evidence} if evidence else {})}


def _names(items):
    return ", ".join(items)


def _completeness(req):
    missing = [label for key, label in (("sites", "sites"), ("bandwidth_mbps", "bandwidth"), ("sla_uptime_pct", "SLA"),
                                        ("timeline_months", "timeline")) if not req.get(key)]
    open_questions = req.get("missing_information") or []
    if missing:
        return _check("completeness", "review", f"Not stated by the customer: {_names(missing)}. "
                      f"{len(open_questions)} open question(s) for the customer.", missing=missing)
    if open_questions:
        return _check("completeness", "review", f"{len(open_questions)} open question(s) remain, e.g. {open_questions[0]}")
    return _check("completeness", "passed", "Sites, bandwidth, SLA and timeline are all stated.")


def _bandwidth(req, products):
    needed = (req.get("bandwidth_mbps") or 0) / 1000 or None
    sizes = sorted({g for p in products if design.is_site_connectivity(p)
                    and (g := design.to_gbps(p.get("bandwidth_value"), p.get("bandwidth_unit")))})
    if needed is None:
        return _check("bandwidth", "review", "Bandwidth is not stated, so the connectivity cannot be sized.")
    if design.site_options(products, needed, design.effective_sla(req)):
        return _check("bandwidth", "passed", f"{design.gbps_label(needed)} per site is available in the catalog "
                      f"(connectivity products from {design.gbps_label(sizes[0])} up to {design.gbps_label(sizes[-1])}).")
    return _check("bandwidth", "failed", f"{design.gbps_label(needed)} per site exceeds the largest catalog connectivity "
                  f"product ({design.gbps_label(sizes[-1])}).")


def _sla(req, products):
    needed = (req.get("bandwidth_mbps") or 0) / 1000 or None
    sla = req.get("sla_uptime_pct")
    if sla is None:
        return _check("sla", "review", f"No SLA stated; assuming the enterprise default of {design.DEFAULT_SLA_PCT}% "
                      "(best-effort products below it are excluded) until the customer confirms.")
    if needed is None:
        return _check("sla", "review", f"{sla}% SLA requested but bandwidth is unknown, so product SLAs cannot be compared.")
    options = design.site_options(products, needed, sla)
    singles = [o for o in options if o.redundancy == 1]
    if not design.site_options(products, needed, None):
        return _check("sla", "review", f"SLA can't be assessed: no catalog product supports {design.gbps_label(needed)} per site.")
    best_single = max((float(p["sla_uptime"] or 0) for p in products if design.is_site_connectivity(p)
                       and (design.to_gbps(p.get("bandwidth_value"), p.get("bandwidth_unit")) or 0) >= needed), default=0)
    if singles:
        single, cheapest = singles[0], options[0]
        single_gbps = design.to_gbps(single.product["bandwidth_value"], single.product["bandwidth_unit"])
        message = f"{sla}% is met by a single {single.product['name']} (rated {single.product['sla_uptime']}%)."
        if single_gbps > needed and cheapest.redundancy > 1:
            message += (f" That is a {design.gbps_label(single_gbps)} tier for a {design.gbps_label(needed)} need; "
                        f"{cheapest.label} also meets it for less (${cheapest.monthly_per_site:,.0f} vs "
                        f"${single.monthly_per_site:,.0f} per site per month).")
        return _check("sla", "passed", message)
    if options:
        cheapest = options[0]
        return _check("sla", "review", f"No single product at {design.gbps_label(needed)} or larger is rated {sla}% "
                      f"(best single rating is {best_single}%). It can be met with {cheapest.label} "
                      f"({cheapest.availability_pct:.4f}% if the two paths are fully independent).",
                      cheapest_option=cheapest.label, best_single_rating=best_single)
    return _check("sla", "failed", f"{sla}% cannot be met even with a redundant pair of the best product (single rating {best_single}%).")


def _site_coverage(req, presence):
    sites = req.get("sites") or []
    if not sites:
        return _check("site_coverage", "review", "No sites stated, so network presence cannot be checked.")
    absent = [row["site"] for row in presence if not (row["locations"] or row["uni_sites"] or row["ports"])]
    if not absent:
        return _check("site_coverage", "passed", "Existing network presence found at every requested site.", presence=presence)
    which = (f"any of the {len(sites)} requested sites ({_names(absent)})" if len(absent) == len(sites) else _names(absent))
    return _check("site_coverage", "review", f"No existing Lumen network presence found in the inventory for {which} "
                  f"(searched sites, ports and locations by name). New build or off-net access and a site survey will be needed.",
                  without_presence=absent, presence=presence)


def _cloud(req, locations):
    clouds = req.get("clouds") or []
    if not clouds:
        return _check("cloud_connectivity", "passed", "No cloud connectivity requested.")
    region = design.region_for(req)
    hubs = design.rank_cloud_hubs(locations, region, clouds)
    where = region or "any region"
    if not hubs:
        return _check("cloud_connectivity", "review", f"No on-ramp location in {where} offers all of: {_names(clouds)}.")
    top = ", ".join(f"{h['name'].replace('[MOCK] ', '')} ({h['aws_available_ports']} AWS ports, "
                    f"{h['azure_available_circuits']} Azure circuits)" for h in hubs[:3])
    note = " The region could not be determined from the requirement, so all regions were considered." if not region else ""
    status = "passed" if region else "review"
    return _check("cloud_connectivity", status, f"{_names(clouds)} on-ramps are available in {where}: {top}. "
                  f"On-ramp capacity in the dataset is mock data; distance and latency are not modelled.{note}",
                  hubs=[h["site_id"] for h in hubs[:3]])


def _plural(months):
    return f"{months:g} month" + ("" if months == 1 else "s")


def _timeline(req, products, similar):
    months = req.get("timeline_months")
    if not months:
        return _check("timeline", "review", "No delivery timeline stated.")
    needed = (req.get("bandwidth_mbps") or 0) / 1000 or None
    options = design.site_options(products, needed, design.effective_sla(req)) if needed else []
    lead_months = (options[0].product["lead_time_days"] / 30.4) if options and options[0].product.get("lead_time_days") else None
    durations = [p["duration_months"] for p in similar if p.get("duration_months")]
    if lead_months and months < lead_months:
        return _check("timeline", "failed", f"{_plural(months)} is shorter than the {lead_months:.1f}-month catalog lead time "
                      f"of {options[0].product['name']}.")
    if durations and months < min(durations):
        return _check("timeline", "review", f"{_plural(months)} is shorter than all {len(durations)} similar past projects "
                      f"(shortest {min(durations)}, median {statistics.median(durations):g} months).",
                      similar_durations=durations)
    if durations:
        return _check("timeline", "passed", f"{_plural(months)} is within the range of similar projects "
                      f"({min(durations)} to {max(durations)} months).", similar_durations=durations)
    return _check("timeline", "review", f"{_plural(months)} can't be benchmarked: no similar projects with durations were found.")


def _history(req, outcomes, reasons):
    ipvpn = len(req.get("sites") or []) >= 2 or bool(req.get("clouds"))
    wanted = IPVPN_FAMILIES if ipvpn else INTERNET_FAMILIES
    rows = [(o, wanted[o["product_family"]][1]) for o in outcomes
            if o["product_family"] in wanted and o["operation"] == wanted[o["product_family"]][0]]
    if not rows:
        return _check("delivery_history", "review", "No order history found for this kind of service."), []
    parts = [f"{label} fails {o['failure_rate_pct']}% ({o['failures']} of {o['finished']} finished orders)" for o, label in rows]
    worst = max(float(o["failure_rate_pct"] or 0) for o, _ in rows)
    cause = f" Most common build-failure cause across Internet/VPN orders: '{reasons[0]['reason']}' ({reasons[0]['share_pct']}%)." if reasons else ""
    status = "passed" if worst < ELEVATED_FAILURE_RATE else "review"
    return _check("delivery_history", status, "; ".join(parts) + "." + cause,
                  worst_failure_rate_pct=worst), [o for o, _ in rows]


def _risks(checks, history_rows):
    by_name = {c["name"]: c for c in checks}
    risks = []

    def add(severity, description, mitigation):
        risks.append({"severity": severity, "description": description, "mitigation": mitigation})

    for c in checks:
        if c["status"] == "failed":
            add("high", c["message"], "Revisit scope or the catalog before quoting.")
    cov = by_name["site_coverage"]
    if cov["status"] == "review" and cov.get("evidence", {}).get("without_presence"):
        add("high", cov["message"], "Schedule site surveys and confirm off-net/partner access early; treat site readiness as the critical path.")
    if by_name["sla"]["status"] == "review" and "independent" in by_name["sla"]["message"]:
        add("medium", by_name["sla"]["message"], "Use diverse physical paths and confirm they share no failure domain before committing to the SLA.")
    if by_name["timeline"]["status"] == "review":
        add("medium", by_name["timeline"]["message"], "Phase the delivery or agree a reduced first-release scope.")
    if by_name["completeness"]["status"] == "review":
        add("low", by_name["completeness"]["message"], "Send the open questions to the customer before finalising the quote.")
    worst = max((float(o["failure_rate_pct"] or 0) for o in history_rows), default=0)
    if worst >= ELEVATED_FAILURE_RATE:
        add("high" if worst >= HIGH_FAILURE_RATE else "medium", by_name["delivery_history"]["message"],
            "Plan extra provisioning time and retries; serialise changes on the same devices to avoid lock failures.")
    return risks


async def run(state: QuoteState) -> QuoteState:
    """Validator. Reads requirement and similar_projects; writes validation."""
    req = state.requirement
    if not req:
        raise ValueError("validator needs state.requirement; run the extractor first")

    products, locations, presence, outcomes, reasons = await asyncio.gather(
        queries.connectivity_products(), queries.cloud_locations(), queries.site_presence(req.get("sites") or []),
        queries.provisioning_outcomes(), queries.common_failure_reasons(["vpn", "internet"], "BUILD", 3))

    history_check, history_rows = _history(req, outcomes, reasons)
    checks = [
        _completeness(req),
        _bandwidth(req, products),
        _sla(req, products),
        _site_coverage(req, presence),
        _cloud(req, locations),
        _timeline(req, products, state.similar_projects),
        history_check,
    ]
    risks = _risks(checks, history_rows)
    confidence = round(sum(WEIGHTS[c["name"]] * STATUS_SCORE[c["status"]] for c in checks), 2)
    status = {c["name"]: c["status"] for c in checks}

    if "failed" in status.values():
        verdict, feasible = "not_feasible", False
        confidence = min(confidence, 0.3)  # one failed check outweighs the others passing
    elif not req.get("sites") or not req.get("bandwidth_mbps"):
        verdict, feasible = "insufficient_information", None  # can't say yes or no without sites and bandwidth
    elif "review" in status.values():
        verdict, feasible = "feasible_with_conditions", True
    else:
        verdict, feasible = "feasible", True

    state.validation = {
        "feasible": feasible,
        "verdict": verdict,
        "confidence": confidence,
        "confidence_basis": "Weighted share of checks passed (passed = 1, needs review = 0.5, failed = 0); weights: "
                            + ", ".join(f"{k} {v:.0%}" for k, v in WEIGHTS.items()),
        "needs_human_review": any(c["status"] == "failed" for c in checks) or confidence < 0.7
                              or any(r["severity"] == "high" for r in risks),
        "checks": checks,
        "risks": risks,
        "metrics": {"provisioning_outcomes": outcomes, "common_failure_reasons": reasons},
    }
    return state
