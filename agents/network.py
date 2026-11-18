"""Network solution. Reads requirement and validation; writes network.

Deterministic: products, prices and lead times come from the product_catalog, mcgw_pricing and locations tables.
Output keeps the keys of the original stub and adds the design, BOM, cost summary and a draft provisioning payload
in the format of schemas/provisioning_schema.json.
"""
import asyncio
import re
import uuid
from datetime import date, timedelta

from backend import design, queries
from schemas.quote_state import QuoteState

CURRENCY = "USD"
# Planning contingency added to the list price to form the top of the cost range. These are assumptions, not data:
# higher when some sites have no existing network presence (off-net / last-mile / survey costs are unknown).
CONTINGENCY_NO_PRESENCE = 0.20
CONTINGENCY_DEFAULT = 0.05
CLOUD_NAMES = {"aws": "AWS", "azure": "Azure", "gcp": "GCP"}
# schemas/provisioning_schema.json only allows a fixed list of product types and NP-XXX-NNN ids, which is narrower than
# the catalog (dycon_ipvpn, gateway) and the MCGW rate card. Map to the schema and keep the originals in customization_config.
SCHEMA_PRODUCT_TYPE = {"dycon_ipvpn": "connectivity", "gateway": "connectivity"}
MCGW_SCHEMA_IDS = {"MCGW-TIER": "NP-MCGW-001", "MCGW-CSP": "NP-MCGW-002", "MCGW-INTERFACE": "NP-MCGW-003"}


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").upper()


def _smallest_at_least(components: list[dict], gbps: float) -> dict | None:
    sized = [(design.parse_gbps(c["component_id"]), c) for c in components]
    sized = [(g, c) for g, c in sized if g is not None]
    if not sized:
        return None
    fitting = [(g, c) for g, c in sized if g >= gbps]
    return min(fitting, key=lambda item: item[0])[1] if fitting else max(sized, key=lambda item: item[0])[1]


def _mcgw(components: list[dict], gbps: float, clouds: list[str]) -> list[dict]:
    """Cloud-connectivity price lines from the MCGW rate card (monthly list rates; the dataset has no setup fees)."""
    tier = _smallest_at_least([c for c in components if c["component_type"] == "gatewayTier"], gbps)
    connection = _smallest_at_least([c for c in components if c["component_type"] == "connectionBandwidth"
                                     and c["category"] == "csp" and c["class_of_service"] == "dedicated"], gbps)
    interfaces = [c for c in components if c["component_type"] == "interface"]
    interface = max(interfaces, key=lambda c: float(c["monthly_rate"] or 0)) if interfaces else None
    lines = []
    if tier:
        lines.append({"product_id": f"MCGW-TIER-{_slug(tier['component_id'])}", "product_name": f"Multi-Cloud Gateway tier {tier['component_id']}",
                      "product_type": "gateway", "quantity": 1, "unit": "units", "setup": 0.0, "monthly": float(tier["monthly_rate"] or 0), "role": "gateway"})
    for cloud in clouds:
        key = design.cloud_key(cloud)
        label = CLOUD_NAMES.get(key, cloud)
        if connection:
            lines.append({"product_id": f"MCGW-CSP-{_slug(connection['component_id'])}", "product_name": f"MCGW {label} connection {connection['component_id']} (dedicated)",
                          "product_type": "connectivity", "quantity": 1, "unit": "circuits", "setup": 0.0, "monthly": float(connection["monthly_rate"] or 0),
                          "role": "cloud", "cloud": label})
        if interface:
            lines.append({"product_id": "MCGW-INTERFACE", "product_name": f"MCGW interface for {label}", "product_type": "gateway", "quantity": 1,
                          "unit": "units", "setup": 0.0, "monthly": float(interface["monthly_rate"] or 0), "role": "cloud", "cloud": label})
    return lines


def _totals(site_lines: list[dict], cloud_lines: list[dict]) -> dict:
    setup = sum(l["setup"] * l["quantity"] for l in site_lines + cloud_lines)
    monthly = sum(l["monthly"] * l["quantity"] for l in site_lines + cloud_lines)
    return {"setup": round(setup, 2), "monthly": round(monthly, 2), "first_year": round(setup + 12 * monthly, 2),
            "three_year_tco": round(setup + 36 * monthly, 2)}


def _site_line(option: design.SiteOption, n_sites: int) -> dict:
    p = option.product
    return {"product_id": p["product_id"], "product_name": p["name"], "product_type": p["product_type"],
            "quantity": n_sites * option.redundancy, "unit": "circuits", "setup": float(p["setup_cost"] or 0),
            "monthly": float(p["monthly_cost"] or 0), "role": "site", "source": p["source"], "lead_time_days": p.get("lead_time_days")}


def _insufficient(state: QuoteState, reason: str) -> QuoteState:
    state.network = {
        "recommended_solution": None,
        "status": "insufficient_information",
        "provisioning": {"ready_for_provisioning": False, "reason": reason},
    }
    return state


def _payload(req, chosen_line, site_lines, cloud_lines, hub, totals, needed_gbps, option, region, lead_days, label) -> dict:
    today = date.today()
    months = req.get("timeline_months")
    finish = today + timedelta(days=round(months * 30.4)) if months else today + timedelta(days=lead_days or 30)
    sites = req.get("sites") or []
    bom = []
    for i, line in enumerate(site_lines + cloud_lines, start=1):
        if line["role"] == "site":
            # SITE-000 = not yet in the inventory (the schema requires SITE-NNN); the real name is in site_name.
            allocation = [{"site_id": "SITE-000", "site_name": s, "quantity_at_site": option.redundancy, "deployment_role": "primary"}
                          for s in sites]
        else:
            allocation = [{"site_id": hub["site_id"], "site_name": hub["name"], "quantity_at_site": line["quantity"], "deployment_role": "primary"}] if hub else []
        schema_id = next((sid for prefix, sid in MCGW_SCHEMA_IDS.items() if line["product_id"].startswith(prefix)), line["product_id"])
        config = {}
        if schema_id != line["product_id"]:
            config["rate_card_id"] = line["product_id"]
        if line["product_type"] != SCHEMA_PRODUCT_TYPE.get(line["product_type"], line["product_type"]):
            config["catalog_type"] = line["product_type"]
        bom.append({
            "line_item_id": f"BOM-{i:04d}", "product_id": schema_id, "product_name": line["product_name"],
            "product_type": SCHEMA_PRODUCT_TYPE.get(line["product_type"], line["product_type"]),
            "quantity": line["quantity"], "unit_of_measure": line["unit"],
            "site_allocation": allocation,
            **({"customization_config": config} if config else {}),
            "pricing": {"unit_setup_cost": line["setup"], "unit_monthly_cost": line["monthly"],
                        "total_setup_cost": round(line["setup"] * line["quantity"], 2),
                        "total_monthly_cost": round(line["monthly"] * line["quantity"], 2), "discount_percent": 0, "currency": CURRENCY},
        })
    mock = any(l.get("source") == "mock" for l in site_lines) or (hub or {}).get("source") == "mock"
    return {
        "provisioning_id": f"PROV-{today.year}-{uuid.uuid4().hex[:6].upper()}",
        "provisioning_date": today.isoformat(),
        "status": "draft",
        "customer_info": {"customer_id": "TO_BE_CONFIRMED", "customer_name": "TO_BE_CONFIRMED", "customer_contact": {"name": "TO_BE_CONFIRMED", "email": "TO_BE_CONFIRMED"}},
        "deployment_schedule": {
            "planned_start_date": today.isoformat(), "planned_completion_date": finish.isoformat(),
            "deployment_phases": [{"phase_number": 1, "phase_name": "Order and provision",
                                   "description": "Catalog lead time of the longest-lead product.",
                                   "start_date": today.isoformat(), "end_date": (today + timedelta(days=lead_days or 0)).isoformat(),
                                   "affected_sites": sites}],
        },
        "bill_of_materials": bom,
        "network_architecture": {
            "architecture_type": "mesh", "regions_covered": [region] if region else [], "total_sites": len(sites),
            "total_bandwidth": {"value": needed_gbps, "unit": "Gbps"},
            "redundancy_model": "active_active" if option.redundancy > 1 else "none",
        },
        "cost_summary": {"total_setup_cost": totals["setup"], "total_monthly_cost": totals["monthly"],
                         "first_year_total": totals["first_year"], "three_year_tco": totals["three_year_tco"], "currency": CURRENCY},
        "data_quality_label": "MOCK" if mock else "REAL",
    }


async def run(state: QuoteState) -> QuoteState:
    """Network solution. Reads requirement and validation; writes network."""
    req = state.requirement
    if not req:
        raise ValueError("network solution needs state.requirement")
    sites = req.get("sites") or []
    clouds = req.get("clouds") or []
    needed = (req.get("bandwidth_mbps") or 0) / 1000 or None
    if not sites or not needed:
        return _insufficient(state, "Sites and bandwidth must be confirmed before the network can be designed or priced.")

    products, locations, components = await asyncio.gather(
        queries.connectivity_products(), queries.cloud_locations(), queries.mcgw_components())

    options = design.site_options(products, needed, design.effective_sla(req))
    if not options:
        return _insufficient(state, f"No catalog product meets {design.gbps_label(needed)} per site at {design.effective_sla(req)}% availability.")

    region = design.region_for(req)
    hubs = design.rank_cloud_hubs(locations, region, clouds) if clouds else []
    hub = hubs[0] if hubs else None
    cloud_lines = _mcgw(components, needed, clouds) if clouds else []

    designs = []
    for option in options[:3]:  # cheapest compliant designs, for the cost range
        lines = [_site_line(option, len(sites))]
        designs.append((option, lines, _totals(lines, cloud_lines)))
    option, site_lines, totals = designs[0]
    lead_days = max((l.get("lead_time_days") or 0 for l in site_lines), default=0)
    label = design.gbps_label(needed)
    redundancy_text = f"a redundant pair of {option.product['name']} per site" if option.redundancy > 1 else f"{option.product['name']} per site"
    validation = state.validation or {}
    no_presence = any(c["name"] == "site_coverage" and c.get("evidence", {}).get("without_presence")
                      for c in validation.get("checks", []))
    contingency = CONTINGENCY_NO_PRESENCE if no_presence else CONTINGENCY_DEFAULT
    high = {k: round(v * (1 + contingency), 2) for k, v in totals.items()}

    payload = _payload(req, site_lines[0], site_lines, cloud_lines, hub, totals, needed, option, region, lead_days, label)
    blockers = ["Customer details (id, name, contact) are not captured yet", "Technical and financial approval", "Commercial pricing sign-off"]
    for check in validation.get("checks", []):
        if check["name"] == "site_coverage" and check["status"] != "passed":
            blockers.insert(0, "Site survey / off-net availability for sites without existing network presence")

    state.network = {
        "recommended_solution": (f"{len(sites)}-site {label} IP VPN: {redundancy_text}"
                                 + (f", with {' and '.join(clouds)} connectivity through the Multi-Cloud Gateway" if clouds else "")),
        "status": "designed",
        "architecture": {
            "sites": sites, "topology": "any-to-any IP VPN" + (" with redundant access" if option.redundancy > 1 else ""),
            "bandwidth": label, "cloud_connectivity": clouds,
            "availability_pct": round(option.availability_pct, 4), "redundancy": option.redundancy,
            "cloud_hub": ({"site_id": hub["site_id"], "name": hub["name"], "region": hub["region"], "source": hub["source"]} if hub else None),
            "cloud_hub_alternatives": [h["name"] for h in hubs[1:3]],
        },
        "products": [{"name": l["product_name"], "quantity": l["quantity"]} for l in site_lines + cloud_lines],
        "bom": [{"item": l["product_name"], "quantity": l["quantity"], "unit_monthly_cost": l["monthly"], "unit_setup_cost": l["setup"]}
                for l in site_lines + cloud_lines],
        "bill_of_materials": payload["bill_of_materials"],
        "alternatives": [{"design": o.label, "availability_pct": round(o.availability_pct, 4), "setup": t["setup"], "monthly": t["monthly"],
                          "first_year": t["first_year"]} for o, _, t in designs],
        "lead_time_days": lead_days,
        "cost_summary": {"currency": CURRENCY, **totals},
        "cost_range": {
            "currency": CURRENCY, "minimum": totals["first_year"], "maximum": high["first_year"],
            "monthly": {"minimum": totals["monthly"], "maximum": high["monthly"]},
            "setup": {"minimum": totals["setup"], "maximum": high["setup"]},
            "contingency_pct": round(contingency * 100),
            "note": (f"First-year cost (setup + 12 months). Minimum is the list price of the recommended design; maximum adds a "
                     f"{contingency:.0%} planning contingency ("
                     + ("some requested sites have no existing network presence, so off-net/last-mile and survey costs are unknown"
                        if no_presence else "list-price variance")
                     + "). The contingency is a planning assumption, not derived from data. Taxes and discounts are excluded."),
        },
        "assumptions": [
            *([f"No SLA was stated, so an enterprise default of {design.DEFAULT_SLA_PCT}% was assumed."] if not req.get("sla_uptime_pct") else []),
            *([f"The smallest suitable catalog product is {design.gbps_label(design.to_gbps(option.product['bandwidth_value'], option.product['bandwidth_unit']))}, "
               f"so the {label} requirement was sized up."]
              if design.to_gbps(option.product["bandwidth_value"], option.product["bandwidth_unit"]) > needed else []),
            "Prices are list prices from product_catalog (setup + monthly) and the MCGW rate card (monthly only; no setup fees in the dataset).",
            "A redundant pair is assumed to use fully independent physical paths; availability is computed as 1 - (1 - single)^2.",
            "Each site gets one access into an any-to-any IP VPN, not a full mesh of point-to-point circuits.",
            "MCGW lines are: one gateway tier, plus one dedicated cloud connection and one interface per cloud; LCI components are excluded pending confirmation.",
            "The cloud hub is chosen by free on-ramp ports in the customer's region; distance and latency are not modelled, and on-ramp capacity data is mock.",
        ],
        "provisioning": {
            "ready_for_provisioning": False,
            "reason": "Draft only. Blocked by: " + "; ".join(blockers) + ".",
            "blockers": blockers,
            "payload": payload,
        },
    }
    return state
