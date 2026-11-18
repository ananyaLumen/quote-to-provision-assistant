"""Extract and transform the files in ../data into rows for the Supabase tables.

Every `rows_*` generator yields plain dicts whose keys are table column names.
Run `python etl.py --stats` for a dry run that reports row counts, how well the
promoted columns are populated, and the size of the JSON payloads.
"""
import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import openpyxl

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_PATH_TOKEN = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


# --------------------------------------------------------------------------- #
# Value helpers
# --------------------------------------------------------------------------- #

def fix_text(value):
    """Repair UTF-8 text that was decoded as cp1252 (e.g. 'LÃ„RCHENSTR' -> 'LÄRCHENSTR')."""
    if isinstance(value, str) and ("Ã" in value or "Â" in value):
        try:
            return value.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value


def clean(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str):
        value = fix_text(value.strip())
    return value


def to_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def to_num(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", ""))
    except ValueError:
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return int(number) if number.is_integer() else number


def to_ts(value):
    text = to_str(value)
    if text is None:
        return None
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return text


def to_date(value):
    text = to_str(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


def to_bool(value):
    return value if isinstance(value, bool) else None


# --------------------------------------------------------------------------- #
# Excel helpers
# --------------------------------------------------------------------------- #

def read_sheet(path):
    """Yield (row_number, {column: value}) for each data row; empty cells are omitted."""
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    sheet.reset_dimensions()
    rows = sheet.iter_rows(values_only=True)
    header = [None if h is None else str(h).strip() for h in next(rows)]
    for number, row in enumerate(rows, start=1):
        flat = {}
        for name, value in zip(header, row):
            if name is None or value is None or value == "":
                continue
            flat[name] = clean(value)
        if flat:
            yield number, flat
    workbook.close()


def unflatten(flat):
    """Turn {'a.b[0].c': 1} into {'a': {'b': [{'c': 1}]}}. Sparse arrays keep their index as a string key."""
    root = {}
    for key, value in flat.items():
        parts = [name or int(index) for name, index in _PATH_TOKEN.findall(key)]
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return _normalize(root)


def _normalize(node):
    if not isinstance(node, dict):
        return node
    out = {key: _normalize(val) for key, val in node.items()}
    if out and all(isinstance(key, int) for key in out):
        if set(out) == set(range(len(out))):
            return [out[i] for i in range(len(out))]
        return {str(key): out[key] for key in sorted(out)}
    return out


def pick(flat, mapping):
    """Build a row from `mapping` = [(column, source_key, converter)] and return (row, consumed_keys)."""
    row, used = {}, set()
    for column, key, convert in mapping:
        row[column] = convert(flat.get(key))
        used.add(key)
    return row, used


def details_of(flat, used, drop_prefixes=()):
    rest = {k: v for k, v in flat.items() if k not in used and not k.startswith(drop_prefixes)}
    return unflatten(rest)


def stamp(row, file_name, number, **extra):
    row.update(source_file=file_name, source_row=number, **extra)
    return row


# --------------------------------------------------------------------------- #
# Curated JSON sources
# --------------------------------------------------------------------------- #

def _load_json(relative):
    with open(DATA_DIR / relative, encoding="utf-8") as handle:
        return json.load(handle)


def _fix_tree(value):
    if isinstance(value, dict):
        return {k: _fix_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_fix_tree(v) for v in value]
    return fix_text(value)


def _leftover(record, consumed):
    """Keys of `record` not consumed by the column mapping (kept in the `extra` column)."""
    return {k: v for k, v in record.items() if k not in consumed}


def rows_product_catalog():
    for relative, source in (("catalog/product_catalog.json", "mock"), ("catalog/product_catalog_real.json", "real")):
        for rec in _fix_tree(_load_json(relative)):
            bw = rec.get("bandwidth") or {}
            yield {
                "product_id": rec["id"],
                "name": rec["name"],
                "product_type": rec["type"],
                "description": rec.get("description"),
                "bandwidth_value": to_num(bw.get("value")),
                "bandwidth_unit": bw.get("unit"),
                "bandwidth_symmetry": bw.get("symmetry"),
                "latency_ms": to_num(rec.get("latency_ms")),
                "sla_uptime": to_num(rec.get("sla_uptime")),
                "setup_cost": to_num(rec.get("setup_cost")),
                "monthly_cost": to_num(rec.get("monthly_cost")),
                "lead_time_days": to_num(rec.get("lead_time_days")),
                "currency": rec.get("currency") or "USD",
                "features": rec.get("features") or [],
                "extra": _leftover(rec, {"id", "name", "type", "description", "bandwidth", "latency_ms", "sla_uptime",
                                         "setup_cost", "monthly_cost", "lead_time_days", "currency", "features",
                                         "data_quality_label"}),
                "source": source,
                "data_quality_label": rec.get("data_quality_label"),
            }


def rows_locations():
    for relative, source in (("inventory/inventory.json", "mock"), ("inventory/inventory_real.json", "real")):
        for rec in _fix_tree(_load_json(relative)):
            cap = rec.get("capacity") or {}
            cloud = rec.get("cloud_onramp") or {}
            conn = rec.get("connectivity") or {}
            coords = rec.get("coordinates") or {}
            extra = _leftover(rec, {"id", "name", "location", "region", "data_center_tier", "coordinates",
                                    "capacity", "cloud_onramp", "connectivity", "inventory_last_updated",
                                    "data_quality_label"})
            site_id = rec["id"]
            if source == "real":
                # The real file truncates every Mongo _id to the same 20 characters, so it can't identify a site;
                # the name slug matches uni_sites.name. Its capacity figures are identical for all sites
                # (placeholders), so they are kept aside instead of being presented as measured capacity.
                site_id = rec["name"].removeprefix("[REAL]").strip()
                extra["source_id_truncated"] = rec["id"]
                extra["unverified_capacity"] = {"capacity": cap, "cloud_onramp": cloud, "connectivity": conn}
                cap, cloud, conn = {}, {}, {}
            yield {
                "site_id": site_id,
                "name": rec["name"],
                "address": rec.get("location"),
                "region": rec.get("region"),
                "data_center_tier": rec.get("data_center_tier"),
                "latitude": to_num(coords.get("latitude")),
                "longitude": to_num(coords.get("longitude")),
                "rack_units": to_num(cap.get("rack_units")),
                "available_rack_units": to_num(cap.get("available_rack_units")),
                "power_capacity_kw": to_num(cap.get("power_capacity_kw")),
                "available_power_kw": to_num(cap.get("available_power_kw")),
                "cooling_capacity_kw": to_num(cap.get("cooling_capacity_kw")),
                "available_cooling_kw": to_num(cap.get("available_cooling_kw")),
                "aws_direct_connect": to_bool(cloud.get("aws_direct_connect")),
                "aws_available_ports": to_num(cloud.get("aws_available_ports")),
                "azure_expressroute": to_bool(cloud.get("azure_expressroute")),
                "azure_available_circuits": to_num(cloud.get("azure_available_circuits")),
                "gcp_interconnect": to_bool(cloud.get("gcp_interconnect")),
                "internet_uplink_gbps": to_num(cloud.get("internet_uplink_gbps")),
                "metro_ethernet_ports": to_num(conn.get("metro_ethernet_ports")),
                "mpls_vpn_capacity": conn.get("mpls_vpn_capacity"),
                "dark_fiber_strands": to_num(conn.get("dark_fiber_strands")),
                "inventory_last_updated": to_date(rec.get("inventory_last_updated")),
                "extra": extra,
                "source": source,
                "data_quality_label": rec.get("data_quality_label"),
            }


def rows_past_projects():
    for relative, source in (("projects/past_projects.json", "synthetic"), ("projects/past_projects_real.json", "real")):
        for rec in _fix_tree(_load_json(relative)):
            bw = rec.get("bandwidth_requirements") or {}
            sla = rec.get("sla") or {}
            timeline = rec.get("timeline") or {}
            costs = rec.get("costs") or {}
            yield {
                "project_id": rec["id"],
                "name": rec["name"],
                "description": rec.get("description"),
                "client": rec.get("client"),
                "location": rec.get("location"),
                "region": rec.get("region"),
                "primary_bandwidth": to_num(bw.get("primary")),
                "secondary_bandwidth": to_num(bw.get("secondary")),
                "bandwidth_unit": bw.get("unit"),
                "cloud_platforms": rec.get("cloud_platforms") or [],
                "cloud_distribution": rec.get("cloud_distribution") or {},
                "sla_uptime_pct": to_num(sla.get("uptime_percentage")),
                "sla_response_time_ms": to_num(sla.get("response_time_ms")),
                "sla_support_level": sla.get("support_level"),
                "start_date": to_date(timeline.get("start_date")),
                "completion_date": to_date(timeline.get("completion_date")),
                "duration_months": to_num(timeline.get("duration_months")),
                "total_cost": to_num(costs.get("total_project_cost")),
                "setup_cost": to_num(costs.get("setup_cost")),
                "monthly_operational": to_num(costs.get("monthly_operational")),
                "currency": costs.get("currency") or "USD",
                "lessons_learned": rec.get("lessons_learned") or [],
                "extra": _leftover(rec, {"id", "name", "description", "client", "location", "region",
                                         "bandwidth_requirements", "cloud_platforms", "cloud_distribution", "sla",
                                         "timeline", "costs", "lessons_learned", "data_quality_label",
                                         "created_date"}),
                "source": source,
                "data_quality_label": rec.get("data_quality_label"),
                "created_date": to_date(rec.get("created_date")),
            }


# --------------------------------------------------------------------------- #
# Excel sources
# --------------------------------------------------------------------------- #

def rows_mcgw_pricing():
    name = "MultiCloudGateway Advisor-MCGW-GroupedPricing.xlsx"
    for number, flat in read_sheet(DATA_DIR / name):
        rates = {}
        for key, value in flat.items():
            match = re.fullmatch(r"prices\[(\d+)\]\.period", key)
            if match:
                rates[str(value).lower()] = to_num(flat.get(f"prices[{match.group(1)}].rate"))
        yield stamp({
            "source_id": to_str(flat.get("_id")),
            "component_id": to_str(flat.get("componentId")),
            "component_type": to_str(flat.get("componentType")),
            "description": to_str(flat.get("description")),
            "hourly_rate": rates.get("hourly"),
            "monthly_rate": rates.get("monthly"),
            "category": to_str(flat.get("attributes.category")),
            "class_of_service": to_str(flat.get("attributes.classOfService")),
        }, name, number)


UNI_SITE_MAP = [
    ("source_id", "_id", to_str), ("name", "name", to_str), ("uni_service_id", "uniServiceId", to_str),
    ("uni_type", "uniType", to_str), ("status", "status", to_str), ("network_type", "networkType", to_str),
    ("ring_type", "ringType", to_str), ("ring_id", "ringId", to_str),
    ("billing_account_number", "billingAccountNumber", to_str),
    ("location_id", "location.locationId", to_str), ("service_address", "location.serviceAddress", to_str),
    ("latitude", "location.latitude", to_num), ("longitude", "location.longitude", to_num),
    ("site_id", "location.siteId", to_str), ("created_at_source", "createDt", to_ts),
    ("device_name", "device.name", to_str), ("device_port", "device.port", to_str),
    ("device_port_speed", "device.portSpeedInMbps", to_num), ("device_model", "device.model", to_str),
    ("device_vendor", "device.vendor", to_str), ("device_role_code", "device.roleCode", to_str),
    ("pe_device_name", "peDevice.name", to_str), ("pe_device_port", "peDevice.port", to_str),
    ("pe_device_model", "peDevice.model", to_str), ("pe_device_vendor", "peDevice.vendor", to_str),
    ("pe_device_role_code", "peDevice.roleCode", to_str),
    ("customer_name", "customer.name", to_str), ("customer_bus_org_id", "customer.busOrgId", to_str),
    ("customer_ban", "customer.ban", to_str),
]


def rows_uni_sites():
    name = "Location_Site.xlsx"
    for number, flat in read_sheet(DATA_DIR / name):
        row, used = pick(flat, UNI_SITE_MAP)
        row["details"] = details_of(flat, used)
        yield stamp(row, name, number)


def rows_customer_ports():
    name = "CustomerPorts.xlsx"
    for number, flat in read_sheet(DATA_DIR / name):
        yield stamp({
            "source_id": to_str(flat.get("_id")),
            "uni_service_id": to_str(flat.get("uniServiceId")),
            "status": to_str(flat.get("status")),
            "customer_ban": to_str(flat.get("customer.ban")),
        }, name, number)


WHITELISTED_PORT_MAP = [
    ("name", "name", to_str), ("billing_account_number", "billingAccountNumber", to_str),
    ("uni_type", "uniType", to_str), ("uni_service_id", "uniServiceId", to_str), ("status", "status", to_str),
    ("network_type", "networkType", to_str), ("ring_type", "ringType", to_str), ("ring_id", "ringId", to_str),
    ("location_id", "location.locationId", to_str), ("service_address", "location.serviceAddress", to_str),
    ("site_id", "location.siteId", to_str),
    ("device_name", "device.name", to_str), ("device_port", "device.port", to_str),
    ("device_port_speed", "device.portSpeedInMbps", to_num), ("device_model", "device.model", to_str),
    ("device_network", "device.network", to_str), ("device_vendor", "device.vendor", to_str),
    ("device_role_code", "device.roleCode", to_str), ("device_wan_port", "device.wanPort", to_str),
    ("mc_device_1", "mcDevices[0].name", to_str), ("mc_device_2", "mcDevices[1].name", to_str),
    ("agg_device_name", "aggDevice.name", to_str), ("agg_device_port", "aggDevice.port", to_str),
    ("pe_device_name", "peDevice.name", to_str), ("pe_device_port", "peDevice.port", to_str),
    ("pe_device_port_speed", "peDevice.portSpeedInMbps", to_num), ("pe_device_role_code", "peDevice.roleCode", to_str),
    ("pe_device_model", "peDevice.model", to_str), ("pe_device_network", "peDevice.network", to_str),
    ("pe_device_vendor", "peDevice.vendor", to_str),
    ("port_product_instance_id", "portProductInstanceId", to_str),
    ("customer_name", "customer.name", to_str), ("customer_bus_org_id", "customer.busOrgId", to_str),
    ("customer_ban", "customer.ban", to_str), ("customer_eid", "customer.eid", to_str),
    ("customer_invoice_display_ban", "customer.invoiceDisplayBan", to_str),
]


def rows_whitelisted_ports():
    name = "WhitelistedPorts.xlsx"
    for number, flat in read_sheet(DATA_DIR / name):
        row, _ = pick(flat, WHITELISTED_PORT_MAP)
        yield stamp(row, name, number)


def rows_evcs():
    name = "EVCs 1.xlsx"
    for number, flat in read_sheet(DATA_DIR / name):
        yield stamp({
            "evc_id": to_str(flat.get("evcId")), "evc_name": to_str(flat.get("evcName")),
            "bandwidth": to_num(flat.get("bandwidth")), "billing_type": to_str(flat.get("billingType")),
            "charge_type": to_str(flat.get("billing.chargeType")),
            "billing_bandwidth": to_num(flat.get("billing.bandwidth")),
            "cos": to_str(flat.get("cos")), "billing_cos": to_str(flat.get("billing.cos")),
            "billing_account_number": to_str(flat.get("billingAccountNumber")),
            "endpoint1_uni_service_id": to_str(flat.get("endPoint1.uniServiceId")),
            "endpoint2_uni_service_id": to_str(flat.get("endPoint2.uniServiceId")),
            "customer_bus_org_id": to_str(flat.get("customer.busOrgId")),
            "monthly_rate": to_num(flat.get("billing.monthlyRate")),
            "detail": to_str(flat.get("detail")),
        }, name, number)


FAILURE_FILES = [
    ("ServiceOrderFailure Root Cause Agent.xlsx", "general"),
    ("ServiceOrderFailure Root Cause Agent-Internet.xlsx", "internet"),
    ("VPNOrderFailures-ServiceOrderFailure Root Cause Agent.xlsx", "vpn"),
    ("EOD_Failures.xlsx", "evc"),
]


def rows_service_order_failures():
    for name, family in FAILURE_FILES:
        for number, flat in read_sheet(DATA_DIR / name):
            yield stamp({
                "source_id": to_str(flat.get("_id")),
                "service_family": family,
                "request_id": to_str(flat.get("requestId")),
                "account_id": to_str(flat.get("accountId")),
                "evc_id": to_str(flat.get("evcId")),
                "bandwidth": to_num(flat.get("bandwidth")),
                "status": to_str(flat.get("status")),
                "operation": to_str(flat.get("operation")),
                "message": to_str(flat.get("message") or flat.get("detail")),
            }, name, number)


EDGE_MAP = [
    ("source_id", "_id", to_str), ("request_id", "requestId", to_str), ("resource_id", "resourceId", to_str),
    ("account_id", "accountId", to_str), ("status", "status", to_str), ("operation", "operation", to_str),
    ("message", "message", to_str), ("clli_code", "asset.requestData.clliCode", to_str),
    ("service_id", "asset.requestData.serviceId", to_str), ("vrf_name", "asset.requestData.vrf.name", to_str),
    ("ip_block", "asset.requestData.service.ipv4AddressBlock", to_str),
    ("bandwidth", "asset.requestData.service.bandwidth", to_num),
    ("customer_name", "asset.requestData.customer.name", to_str),
    ("timeout_seconds", "timeoutInSeconds", to_num),
    ("build_start_time", "buildStartTime", to_ts), ("build_finish_time", "buildFinishTime", to_ts),
    ("modify_start_time", "modifyStartTime", to_ts), ("modify_finish_time", "modifyFinishTime", to_ts),
    ("delete_start_time", "deleteStartTime", to_ts), ("delete_finish_time", "deleteFinishTime", to_ts),
]

DYCON_MAP = [
    ("resource_id", "productInstanceId", to_str), ("friendly_name", "customerFriendlyName", to_str),
    ("account_id", "customer.ban", to_str), ("customer_name", "customer.name", to_str),
    ("status", "status", to_str), ("operation", "operation", to_str), ("state", "state", to_str),
    ("product_type", "productType", to_str), ("bandwidth", "billing.bandwidth", to_num),
    ("monthly_rate", "billing.monthlyRate", to_num),
    ("source_created_at", "createDate", to_ts), ("source_deleted_at", "deleteDate", to_ts),
    ("build_start_time", "buildReceiveTime", to_ts), ("build_finish_time", "buildFinishTime", to_ts),
    ("modify_start_time", "modifyReceiveTime", to_ts), ("modify_finish_time", "modifyFinishTime", to_ts),
    ("delete_start_time", "deleteReceiveTime", to_ts), ("delete_finish_time", "deleteFinishTime", to_ts),
]

PROVISIONING_COLUMNS = [
    "source_id", "request_id", "resource_id", "account_id", "customer_name", "friendly_name", "status", "operation",
    "state", "product_type", "message", "clli_code", "service_id", "vrf_name", "ip_block", "bandwidth",
    "monthly_rate", "timeout_seconds", "build_start_time", "build_finish_time", "modify_start_time",
    "modify_finish_time", "delete_start_time", "delete_finish_time", "source_created_at", "source_deleted_at",
]

PROVISIONING_FILES = [
    ("EdgeIPVPN.xlsx", "edge_ipvpn", EDGE_MAP),
    ("EdgeInternet.xlsx", "edge_internet", EDGE_MAP),
    ("DyconIPVPN 3.xlsx", "dycon_ipvpn", DYCON_MAP),
]


def rows_provisioning_requests():
    for name, family, mapping in PROVISIONING_FILES:
        for number, flat in read_sheet(DATA_DIR / name):
            mapped, used = pick(flat, mapping)
            row = {column: mapped.get(column) for column in PROVISIONING_COLUMNS}
            row["details"] = details_of(flat, used)
            yield stamp(row, name, number, product_family=family)


def rows_inventory_dq_issues():
    name = "InventoryDataQualityAgent.xlsx"
    for number, flat in read_sheet(DATA_DIR / name):
        nested = unflatten(flat)
        transactions = nested.get("transactions") or {}
        items = transactions.items() if isinstance(transactions, dict) else enumerate(transactions)
        issues = []
        for index, tx in items:
            exceptions = tx.get("exceptions") if isinstance(tx, dict) else None
            if exceptions:
                issues.append({"transaction": int(index), "exceptions": exceptions})
        issues.sort(key=lambda item: item["transaction"])
        yield stamp({
            "uni_service_id": to_str(flat.get("uniServiceId")),
            "customer_ban": to_str(flat.get("customer.ban")),
            "issue_count": len(issues),
            "issues": issues,
            "details": {k: v for k, v in nested.items() if k not in ("uniServiceId", "customer")},
        }, name, number)


# table -> (row generator, conflict columns used for upsert), in dependency order
TABLES = {
    "product_catalog": (rows_product_catalog, "product_id"),
    "locations": (rows_locations, "site_id"),
    "past_projects": (rows_past_projects, "project_id"),
    "mcgw_pricing": (rows_mcgw_pricing, "source_file,source_row"),
    "customer_ports": (rows_customer_ports, "source_file,source_row"),
    "whitelisted_ports": (rows_whitelisted_ports, "source_file,source_row"),
    "evcs": (rows_evcs, "source_file,source_row"),
    "service_order_failures": (rows_service_order_failures, "source_file,source_row"),
    "inventory_dq_issues": (rows_inventory_dq_issues, "source_file,source_row"),
    "uni_sites": (rows_uni_sites, "source_file,source_row"),
    "provisioning_requests": (rows_provisioning_requests, "source_file,source_row"),
}


# --------------------------------------------------------------------------- #
# Dry-run statistics
# --------------------------------------------------------------------------- #

def print_stats(selected):
    sys.stdout.reconfigure(encoding="utf-8")
    for table in selected:
        generator, _ = TABLES[table]
        count, filled, size, biggest = 0, {}, 0, 0
        for row in generator():
            count += 1
            for column, value in row.items():
                filled.setdefault(column, 0)
                if value not in (None, "", [], {}):
                    filled[column] += 1
            payload = len(json.dumps(row, default=str))
            size += payload
            biggest = max(biggest, payload)
        print(f"\n== {table}: {count} rows, {size / 1e6:.1f} MB JSON, largest row {biggest / 1e3:.1f} KB")
        empty = [c for c in filled if filled[c] == 0]
        sparse = {c: f"{filled[c]}/{count}" for c in filled if 0 < filled[c] < count}
        print("   always-empty columns:", empty or "none")
        print("   partially filled:", sparse or "none")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats", action="store_true", help="dry run: report row counts and payload sizes")
    parser.add_argument("--only", nargs="*", choices=list(TABLES), help="limit to these tables")
    args = parser.parse_args()
    if args.stats:
        print_stats(args.only or list(TABLES))
    else:
        parser.print_help()
