"""Quote-to-Provision Assistant API, backed by Supabase.

    uvicorn main:app --reload --port 8000

Uses the secret key server-side, so the endpoints below deliberately expose only
catalog/design data and aggregates, not the customer columns of the operational tables.
"""
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from supabase_client import supabase

app = FastAPI(title="Quote-to-Provision Assistant API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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


def run(query):
    try:
        return query.execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {str(exc)[:300]}")


def one(table: str, key: str, value: str):
    rows = run(supabase.table(table).select("*").eq(key, value).limit(1)).data
    if not rows:
        raise HTTPException(status_code=404, detail=f"{table} '{value}' not found")
    return rows[0]


@app.get("/health")
def health():
    run(supabase.table("product_catalog").select("product_id").limit(1))
    return {"status": "ok"}


@app.get("/api/stats")
def stats():
    return {t: run(supabase.table(t).select("*", count="exact").limit(1)).count for t in STAT_TABLES}


@app.get("/api/products")
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


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    return one("product_catalog", "product_id", product_id)


@app.get("/api/locations")
def list_locations(region: Optional[str] = None, source: Optional[str] = None,
                   aws: Optional[bool] = None, azure: Optional[bool] = None, gcp: Optional[bool] = None,
                   limit: int = Query(100, ge=1, le=500)):
    query = supabase.table("locations").select("*")
    for column, value in (("region", region), ("source", source), ("aws_direct_connect", aws),
                          ("azure_expressroute", azure), ("gcp_interconnect", gcp)):
        if value is not None:
            query = query.eq(column, value)
    return run(query.order("site_id").limit(limit)).data


@app.get("/api/locations/{site_id}")
def get_location(site_id: str):
    return one("locations", "site_id", site_id)


@app.get("/api/locations/{site_id}/capacity")
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


@app.get("/api/projects")
def list_projects(region: Optional[str] = None, source: Optional[str] = None,
                  min_bandwidth: Optional[float] = None, limit: int = Query(50, ge=1, le=200)):
    query = supabase.table("past_projects").select("*")
    if region:
        query = query.eq("region", region)
    if source:
        query = query.eq("source", source)
    if min_bandwidth is not None:
        query = query.gte("primary_bandwidth", min_bandwidth)
    return run(query.order("project_id").limit(limit)).data


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    return one("past_projects", "project_id", project_id)


@app.get("/api/failures")
def list_failures(service_family: Optional[str] = None, operation: Optional[str] = None,
                  limit: int = Query(50, ge=1, le=500)):
    query = supabase.table("service_order_failures").select("service_family,operation,status,message,request_id")
    if service_family:
        query = query.eq("service_family", service_family)
    if operation:
        query = query.eq("operation", operation)
    return run(query.limit(limit)).data


@app.get("/api/ports")
def lookup_ports(uni_service_id: str, limit: int = Query(20, ge=1, le=100)):
    return run(supabase.table("whitelisted_ports").select(PORT_COLUMNS)
               .eq("uni_service_id", uni_service_id).limit(limit)).data


@app.post("/api/orders")
def upsert_order(order: dict = Body(...)):
    if not order.get("provisioning_id"):
        raise HTTPException(status_code=422, detail="provisioning_id is required")
    return run(supabase.table("provisioning_orders").upsert(order, on_conflict="provisioning_id")).data


@app.get("/api/orders/{provisioning_id}")
def get_order(provisioning_id: str):
    order = one("provisioning_orders", "provisioning_id", provisioning_id)
    order["bom_items"] = run(supabase.table("bom_items").select("*").eq("provisioning_id", provisioning_id)).data
    return order
