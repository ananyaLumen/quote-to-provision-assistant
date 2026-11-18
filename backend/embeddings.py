"""Text builders and OpenAI embedding helpers for similar-project search.

Projects and requirements are rendered in the same style so their embeddings are comparable.
"""
import re

from backend.llm import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, get_client

_TAG = re.compile(r"\[[^\]]*\]\s*")  # data-quality tags like [MOCK] / [REAL] are noise for similarity


def _clean(text) -> str:
    return _TAG.sub("", str(text)).strip()


def _join(items) -> str:
    return ", ".join(_clean(i) for i in items if i)


def project_text(row: dict) -> str:
    parts = [f"{_clean(row['name'])}."]
    if row.get("description"):
        description = _clean(row["description"])
        parts.append(description if description.endswith((".", "!", "?")) else description + ".")
    if row.get("client"):
        parts.append(f"Client: {_clean(row['client'])}.")
    place = _join([row.get("location"), row.get("region")])
    if place:
        parts.append(f"Location: {place}.")
    if row.get("primary_bandwidth") is not None:
        unit = row.get("bandwidth_unit") or ""
        parts.append(f"Bandwidth: {row['primary_bandwidth']} {unit} primary"
                     + (f", {row['secondary_bandwidth']} {unit} secondary." if row.get("secondary_bandwidth") else "."))
    if row.get("cloud_platforms"):
        parts.append(f"Cloud platforms: {_join(row['cloud_platforms'])}.")
    if row.get("sla_uptime_pct") is not None:
        parts.append(f"SLA: {row['sla_uptime_pct']}% uptime"
                     + (f", {row['sla_support_level']} support." if row.get("sla_support_level") else "."))
    if row.get("duration_months") is not None:
        parts.append(f"Duration: {row['duration_months']} months.")
    if row.get("lessons_learned"):
        parts.append(f"Lessons learned: {'; '.join(_clean(x) for x in row['lessons_learned'])}.")
    return " ".join(parts)


def requirement_text(req: dict) -> str:
    parts = []
    if req.get("summary"):
        parts.append(f"{req['summary']}")
    if req.get("sites"):
        parts.append(f"Sites: {_join(req['sites'])}.")
    if req.get("regions"):
        parts.append(f"Location: {_join(req['regions'])}.")
    if req.get("topology"):
        parts.append(f"Topology: {req['topology']}.")
    if req.get("bandwidth"):
        parts.append(f"Bandwidth: {req['bandwidth']} per link.")
    if req.get("clouds"):
        parts.append(f"Cloud platforms: {_join(req['clouds'])}.")
    if req.get("sla"):
        parts.append(f"SLA: {req['sla']} uptime.")
    if req.get("security"):
        parts.append(f"Security: {_join(req['security'])}.")
    if req.get("integrations"):
        parts.append(f"Integrations: {_join(req['integrations'])}.")
    if req.get("software_components"):
        parts.append(f"Software: {_join(req['software_components'])}.")
    if req.get("timeline"):
        parts.append(f"Duration: {req['timeline']}.")
    return " ".join(parts)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await get_client().embeddings.create(
        model=EMBEDDING_MODEL, input=texts, dimensions=EMBEDDING_DIMENSIONS
    )
    vectors = [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
    if len(vectors) != len(texts) or any(len(v) != EMBEDDING_DIMENSIONS for v in vectors):
        raise RuntimeError(f"Embedding model returned unexpected shapes; expected {EMBEDDING_DIMENSIONS} dimensions")
    return vectors
