"""Which tables get embeddings, and the text each row is embedded as.

Only free-text sources are listed. Structured tables (ports, EVCs, UNI sites, provisioning requests) are
identifiers and numbers: SQL filters answer questions about them better than embeddings, and embedding
~50,000 such rows would cost several hundred MB of database space for no gain.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from backend.api.data_routes import PROJECT_COLUMNS
from backend.embeddings import _clean, _join, project_text

MAX_CHARS = 2000  # keeps a single input far below the model's token limit


@dataclass(frozen=True)
class Source:
    table: str
    key: str
    columns: str
    build: Callable[[dict], Optional[str]]  # returns None/"" when the row has nothing worth embedding


def product_text(row: dict) -> str:
    parts = [f"{_clean(row['name'])}. Type: {row['product_type']}."]
    if row.get("description"):
        parts.append(_clean(row["description"]))
    if row.get("bandwidth_value") is not None:
        parts.append(f"Bandwidth: {row['bandwidth_value']} {row.get('bandwidth_unit') or ''} {row.get('bandwidth_symmetry') or ''}.".replace("  ", " "))
    if row.get("latency_ms") is not None:
        parts.append(f"Latency: {row['latency_ms']} ms.")
    if row.get("sla_uptime") is not None:
        parts.append(f"SLA: {row['sla_uptime']}% uptime.")
    if row.get("lead_time_days") is not None:
        parts.append(f"Lead time: {row['lead_time_days']} days.")
    if row.get("features"):
        parts.append(f"Features: {_join(row['features'])}.")
    return " ".join(parts)


def location_text(row: dict) -> str:
    parts = [f"{_clean(row['name'])}."]
    if row.get("address"):
        parts.append(f"Address: {_clean(row['address'])}.")
    if row.get("region"):
        parts.append(f"Region: {row['region']}.")
    if row.get("data_center_tier"):
        parts.append(f"Data centre tier: {row['data_center_tier']}.")
    onramps = [label for flag, label in (("aws_direct_connect", "AWS Direct Connect"),
                                         ("azure_expressroute", "Azure ExpressRoute"),
                                         ("gcp_interconnect", "GCP Interconnect")) if row.get(flag)]
    if onramps:
        parts.append(f"Cloud on-ramps: {', '.join(onramps)}.")
    return " ".join(parts)


def pricing_text(row: dict) -> str:
    parts = [f"Multi-cloud gateway component {row.get('component_id') or ''} ({row.get('component_type') or 'unknown type'})."]
    for field, label in (("description", "Description"), ("category", "Category"), ("class_of_service", "Class of service")):
        if row.get(field):
            parts.append(f"{label}: {row[field]}.")
    if row.get("hourly_rate") is not None:
        parts.append(f"Hourly rate {row['hourly_rate']}.")
    if row.get("monthly_rate") is not None:
        parts.append(f"Monthly rate {row['monthly_rate']}.")
    return " ".join(parts)


def failure_text(row: dict) -> Optional[str]:
    if not row.get("message"):
        return None
    head = " ".join(str(x) for x in (row.get("service_family"), row.get("operation"), row.get("status")) if x)
    return f"{head} order failure: {row['message']}"[:MAX_CHARS]


def _messages(node) -> list[str]:
    """Collect the 'message' / 'detail' strings anywhere inside a nested exception structure."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("message", "detail") and isinstance(value, str):
                found.append(value.strip().strip('"'))
            else:
                found.extend(_messages(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_messages(item))
    return found


def dq_issue_text(row: dict) -> Optional[str]:
    unique = list(dict.fromkeys(m for m in _messages(row.get("issues")) if m))
    if not unique:
        return None
    return f"Inventory data-quality issues on {row.get('uni_service_id') or 'a service'}: {' | '.join(unique)}"[:MAX_CHARS]


SOURCES = {
    "past_projects": Source("past_projects", "project_id", PROJECT_COLUMNS, project_text),
    "product_catalog": Source("product_catalog", "product_id",
                              "product_id,name,product_type,description,bandwidth_value,bandwidth_unit,bandwidth_symmetry,"
                              "latency_ms,sla_uptime,lead_time_days,features", product_text),
    "locations": Source("locations", "site_id",
                        "site_id,name,address,region,data_center_tier,aws_direct_connect,azure_expressroute,gcp_interconnect",
                        location_text),
    "mcgw_pricing": Source("mcgw_pricing", "id",
                           "id,component_id,component_type,description,hourly_rate,monthly_rate,category,class_of_service",
                           pricing_text),
    "service_order_failures": Source("service_order_failures", "id", "id,service_family,operation,status,message", failure_text),
    "inventory_dq_issues": Source("inventory_dq_issues", "id", "id,uni_service_id,issues", dq_issue_text),
}
