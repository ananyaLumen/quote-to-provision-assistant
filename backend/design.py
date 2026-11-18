"""Shared sizing rules used by both the validator and the network agent, so they cannot disagree.

Pure functions: no database or network access. Inputs are plain dicts as returned by the data layer.
"""
import re
from dataclasses import dataclass

SITE_CONNECTIVITY_TYPES = {"connectivity", "dycon_ipvpn"}
MAX_REDUNDANCY = 2  # single link or a redundant pair
DEFAULT_SLA_PCT = 99.9  # enterprise default when the customer states no SLA; excludes best-effort products


def effective_sla(requirement: dict) -> float:
    return requirement.get("sla_uptime_pct") or DEFAULT_SLA_PCT

# Requirement regions/countries -> the region names used in the `locations` table.
REGION_KEYWORDS = {
    "Asia-Pacific": ["india", "singapore", "japan", "australia", "china", "korea", "hong kong", "indonesia", "malaysia",
                     "thailand", "vietnam", "philippines", "new zealand", "asia", "apac"],
    "Europe": ["united kingdom", "uk", "england", "germany", "france", "netherlands", "spain", "italy", "ireland",
               "sweden", "switzerland", "poland", "europe", "emea"],
    "North America": ["united states", "usa", "us", "canada", "mexico", "north america"],
    "South America": ["brazil", "argentina", "chile", "colombia", "peru", "south america", "latam"],
}


def to_gbps(value, unit) -> float | None:
    if value is None:
        return None
    factor = {"mbps": 0.001, "gbps": 1.0, "tbps": 1000.0}.get(str(unit or "gbps").lower())
    return None if factor is None else float(value) * factor


def parse_gbps(label: str) -> float | None:
    """'10 Gbps' -> 10.0, '500 Mbps' -> 0.5."""
    match = re.fullmatch(r"\s*([\d.]+)\s*([A-Za-z]+)\s*", label or "")
    return to_gbps(float(match.group(1)), match.group(2)) if match else None


def gbps_label(gbps: float) -> str:
    return f"{gbps:g}G" if gbps >= 1 else f"{gbps * 1000:g}M"


def availability_pct(single_pct: float, copies: int) -> float:
    """Availability of `copies` independent parallel links, each at `single_pct`."""
    return 100.0 * (1.0 - (1.0 - single_pct / 100.0) ** copies)


def is_site_connectivity(product: dict) -> bool:
    features = " ".join(product.get("features") or [])
    return (product["product_type"] in SITE_CONNECTIVITY_TYPES
            and "Direct Connect" not in features   # cloud interconnects are priced separately
            and "Best effort" not in features)     # shared best-effort internet is not VPN access, even as a redundant pair


@dataclass(frozen=True)
class SiteOption:
    product: dict
    redundancy: int
    availability_pct: float
    setup_per_site: float
    monthly_per_site: float

    @property
    def label(self) -> str:
        return f"{self.redundancy} x {self.product['name']}" if self.redundancy > 1 else self.product["name"]


def site_options(products: list[dict], needed_gbps: float, required_sla_pct: float | None) -> list[SiteOption]:
    """Every way to build one site's access that meets bandwidth and SLA, cheapest monthly cost first.

    Real products win ties over mock ones.
    """
    options = []
    for product in products:
        gbps = to_gbps(product.get("bandwidth_value"), product.get("bandwidth_unit"))
        if not is_site_connectivity(product) or gbps is None or gbps < needed_gbps:
            continue
        sla = float(product["sla_uptime"] or 0)
        for copies in range(1, MAX_REDUNDANCY + 1):
            achieved = availability_pct(sla, copies)
            if required_sla_pct is not None and achieved < required_sla_pct:
                continue
            options.append(SiteOption(product, copies, achieved,
                                      copies * float(product["setup_cost"] or 0),
                                      copies * float(product["monthly_cost"] or 0)))
    options.sort(key=lambda o: (o.monthly_per_site, o.setup_per_site, o.product["source"] != "real", o.redundancy))
    return options


def region_for(requirement: dict) -> str | None:
    """Best-effort mapping of the requirement's regions/sites to a `locations` region."""
    text = " ".join([*requirement.get("regions", []), *requirement.get("sites", [])]).lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(word)}\b", text) for word in keywords):
            return region
    return None


CLOUD_COLUMNS = {
    "aws": ("aws_direct_connect", "aws_available_ports"),
    "azure": ("azure_expressroute", "azure_available_circuits"),
    "gcp": ("gcp_interconnect", None),  # the dataset has no port count for GCP
}


def cloud_key(name: str) -> str | None:
    lowered = name.lower()
    for key, alias in (("aws", "amazon"), ("azure", "microsoft"), ("gcp", "google")):
        if key in lowered or alias in lowered:
            return key
    return None


def rank_cloud_hubs(locations: list[dict], region: str | None, clouds: list[str]) -> list[dict]:
    """On-ramp locations in `region` that offer every requested cloud, most free ports first.

    Distance and latency are not in the dataset, so ranking is by free on-ramp ports only.
    """
    keys = [cloud_key(c) for c in clouds]
    ranked = []
    for loc in locations:
        if region and loc.get("region") != region:
            continue
        ports = []
        for key in keys:
            if key is None:
                continue
            flag, count = CLOUD_COLUMNS[key]
            if not loc.get(flag):
                break
            ports.append(loc.get(count) if count else 99)
        else:
            free = min((p for p in ports if p is not None), default=0)
            if free > 0:
                ranked.append((free, loc))
    ranked.sort(key=lambda item: (-item[0], item[1]["site_id"]))
    return [loc for _, loc in ranked]
