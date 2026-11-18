"""Compute and store an embedding for every row of past_projects.

    python -m backend.embed_projects        (run from the repository root)

Re-run after the project data changes. Needs OPENAI_API_KEY in backend/.env and the pgvector
column from sql/schema.sql.
"""
import asyncio

from backend.api.data_routes import PROJECT_COLUMNS
from backend.embeddings import embed_texts, project_text
from backend.supabase_client import supabase


async def main() -> None:
    rows = supabase.table("past_projects").select(PROJECT_COLUMNS).execute().data
    vectors = await embed_texts([project_text(row) for row in rows])
    for row, vector in zip(rows, vectors):
        supabase.table("past_projects").update({"embedding": vector}).eq("project_id", row["project_id"]).execute()
    print(f"Embedded {len(rows)} projects")


if __name__ == "__main__":
    asyncio.run(main())
