import asyncio

from backend.embeddings import embed_texts, requirement_text
from backend.supabase_client import supabase
from schemas.quote_state import QuoteState

TOP_K = 5


async def run(state: QuoteState) -> QuoteState:
    """Retriever. Reads requirement; writes similar_projects (best matches first, with a cosine similarity)."""
    if not state.requirement:
        raise ValueError("retriever needs state.requirement; run the extractor first")

    query = requirement_text(state.requirement)
    if not query:
        raise ValueError("requirement has nothing to search with")
    (vector,) = await embed_texts([query])

    response = await asyncio.to_thread(
        lambda: supabase.rpc("match_past_projects", {"query_embedding": vector, "match_count": TOP_K}).execute()
    )

    state.similar_projects = [
        {
            # Keys of the original stub first, so existing consumers keep working.
            "project_id": row["project_id"],
            "summary": row["description"],
            "similarity": round(row["similarity"], 4),
            "technologies": row["cloud_platforms"],
            "name": row["name"],
            "client": row["client"],
            "region": row["region"],
            "primary_bandwidth": row["primary_bandwidth"],
            "bandwidth_unit": row["bandwidth_unit"],
            "sla_uptime_pct": row["sla_uptime_pct"],
            "duration_months": row["duration_months"],
            "total_cost": row["total_cost"],
            "lessons_learned": row["lessons_learned"],
            "source": row["source"],
        }
        for row in response.data
    ]
    return state
