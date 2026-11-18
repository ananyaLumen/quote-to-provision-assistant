"""Read/write endpoints over the Supabase data (catalog, locations, projects, failures, ports, orders).

Mounted at /api by backend.main. Uses the secret key server-side, so these endpoints deliberately
expose only catalog/design data and aggregates, not the customer columns of the operational tables.
"""
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query

from backend.supabase_client import supabase

router = APIRouter(prefix="/api", tags=["data"])

STAT_TABLES = [
    "product_catalog", "locations", "past_projects", "mcgw_pricing", "uni_sites", "customer_ports",
    "whitelisted_ports", "evcs", "provisioning_requests", "service_order_failures", "inventory_dq_issues",
    "provisioning_orders",
]
# Port lookups return network facts only; customer names/BANs stay out of the API.
PORT_COLUMNS = (
    "uni_service_id,status,network_type,ring_type,site_id,device_name,device_port,device_port_speed,"
    "device_model,device_vendor,pe_device_name,pe_device_port,pe_device_model,pe_device_vendor"
)
# Explicit list so the 1536-float embedding column never ends up in API responses.
PROJECT_COLUMNS = (
    "project_id,name,description,client,location,region,primary_bandwidth,secondary_bandwidth,bandwidth_unit,"
    "cloud_platforms,cloud_distribution,sla_uptime_pct,sla_response_time_ms,sla_support_level,start_date,"
    "completion_date,duration_months,total_cost,setup_cost,monthly_operational,currency,lessons_learned,extra,"
    "source,data_quality_label,created_date"
)


def run(query):
    try:
        return query.execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {str(exc)[:300]}")


def one(table: str, key: str, value: str, columns: str = "*"):
    rows = run(supabase.table(table).select(columns).eq(key, value).limit(1)).data
    if not rows:
        raise HTTPException(status_code=404, detail=f"{table} '{value}' not found")
    return rows[0]


@router.get("/stats")
def stats():
    return {t: run(supabase.table(t).select("*", count="exact").limit(1)).count for t in STAT_TABLES}


@router.get("/products")
def list_products(product_type: Optional[str] = None, source: Optional[str] = None,
                  max_monthly_cost: Optional[float] = None, limit: int = Query(100, ge=1, le=500)):
    query = supabase.table("product_catalog").select("*")
    if product_type:
        query = query.eq("product_type", product_type)
    if source:
        query = query.eq("source", source)
    if max_monthly_cost is not None:
        query = query.lte("monthly_cost", max_monthly_cost)
    return run(query.order("product_id").limit(limit)).data


@router.get("/products/{product_id}")
def get_product(product_id: str):
    return one("product_catalog", "product_id", product_id)


@router.get("/locations")
def list_locations(region: Optional[str] = None, source: Optional[str] = None,
                   aws: Optional[bool] = None, azure: Optional[bool] = None, gcp: Optional[bool] = None,
                   limit: int = Query(100, ge=1, le=500)):
    query = supabase.table("locations").select("*")
    for column, value in (("region", region), ("source", source), ("aws_direct_connect", aws),
                          ("azure_expressroute", azure), ("gcp_interconnect", gcp)):
        if value is not None:
            query = query.eq(column, value)
    return run(query.order("site_id").limit(limit)).data


@router.get("/locations/{site_id}")
def get_location(site_id: str):
    return one("locations", "site_id", site_id)


@router.get("/locations/{site_id}/capacity")
def location_capacity(site_id: str):
    loc = one("locations", "site_id", site_id)

    def usage(total, free):
        return None if not total or free is None else round((total - free) / total * 100, 1)

    return {
        "site_id": site_id,
        "rack_units": {"total": loc["rack_units"], "available": loc["available_rack_units"],
                       "utilization_pct": usage(loc["rack_units"], loc["available_rack_units"])},
        "power_kw": {"total": loc["power_capacity_kw"], "available": loc["available_power_kw"],
                     "utilization_pct": usage(loc["power_capacity_kw"], loc["available_power_kw"])},
        "cooling_kw": {"total": loc["cooling_capacity_kw"], "available": loc["available_cooling_kw"],
                       "utilization_pct": usage(loc["cooling_capacity_kw"], loc["available_cooling_kw"])},
        "source": loc["source"],
    }


@router.get("/projects")
def list_projects(region: Optional[str] = None, source: Optional[str] = None,
                  min_bandwidth: Optional[float] = None, limit: int = Query(50, ge=1, le=200)):
    query = supabase.table("past_projects").select(PROJECT_COLUMNS)
    if region:
        query = query.eq("region", region)
    if source:
        query = query.eq("source", source)
    if min_bandwidth is not None:
        query = query.gte("primary_bandwidth", min_bandwidth)
    return run(query.order("project_id").limit(limit)).data


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    return one("past_projects", "project_id", project_id, PROJECT_COLUMNS)


@router.get("/failures")
def list_failures(service_family: Optional[str] = None, operation: Optional[str] = None,
                  limit: int = Query(50, ge=1, le=500)):
    query = supabase.table("service_order_failures").select("service_family,operation,status,message,request_id")
    if service_family:
        query = query.eq("service_family", service_family)
    if operation:
        query = query.eq("operation", operation)
    return run(query.limit(limit)).data


@router.get("/ports")
def lookup_ports(uni_service_id: str, limit: int = Query(20, ge=1, le=100)):
    return run(supabase.table("whitelisted_ports").select(PORT_COLUMNS)
               .eq("uni_service_id", uni_service_id).limit(limit)).data


@router.post("/orders")
def upsert_order(order: dict = Body(...)):
    if not order.get("provisioning_id"):
        raise HTTPException(status_code=422, detail="provisioning_id is required")
    return run(supabase.table("provisioning_orders").upsert(order, on_conflict="provisioning_id")).data


@router.get("/orders/{provisioning_id}")
def get_order(provisioning_id: str):
    order = one("provisioning_orders", "provisioning_id", provisioning_id)
    order["bom_items"] = run(supabase.table("bom_items").select("*").eq("provisioning_id", provisioning_id)).data
    return order
