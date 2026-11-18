"""Database reads used by the agents. All calls are blocking supabase-py calls wrapped for async code."""
import asyncio

import httpx

from backend.supabase_client import supabase

RETRIES = 3


async def _run(query):
    # The client keeps one HTTP/2 connection open; the server occasionally drops it between requests.
    for attempt in range(1, RETRIES + 1):
        try:
            return (await asyncio.to_thread(query.execute)).data
        except (httpx.TransportError, httpx.RemoteProtocolError):
            if attempt == RETRIES:
                raise
            await asyncio.sleep(0.5 * attempt)


async def _rpc(name: str, params: dict):
    return await _run(supabase.rpc(name, params))


async def connectivity_products() -> list[dict]:
    return await _run(supabase.table("product_catalog").select("*").in_("product_type", ["connectivity", "dycon_ipvpn"]))


async def cloud_locations() -> list[dict]:
    """Locations with on-ramp data (the 'real' sites have none: their capacity is unverified)."""
    return await _run(supabase.table("locations").select(
        "site_id,name,region,aws_direct_connect,aws_available_ports,azure_expressroute,azure_available_circuits,"
        "gcp_interconnect,available_rack_units,available_power_kw,source").not_.is_("aws_available_ports", "null"))


async def mcgw_components() -> list[dict]:
    return await _run(supabase.table("mcgw_pricing").select(
        "component_id,component_type,category,class_of_service,description,hourly_rate,monthly_rate"
    ).in_("component_type", ["gatewayTier", "connectionBandwidth", "interface"]))


async def site_presence(sites: list[str]) -> list[dict]:
    return await _rpc("site_presence", {"site_names": sites}) if sites else []


async def provisioning_outcomes() -> list[dict]:
    return await _rpc("provisioning_outcomes", {})


async def common_failure_reasons(families: list[str], operation: str, top_n: int = 3) -> list[dict]:
    return await _rpc("common_failure_reasons", {"families": families, "op": operation, "top_n": top_n})
