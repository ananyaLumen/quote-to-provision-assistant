"""Embed every text source into the shared `embeddings` table.

    python -m backend.embed_all                      # all sources (run from the repository root)
    python -m backend.embed_all --only product_catalog locations
    python -m backend.embed_all --dry-run            # build the texts and count what would be embedded
    python -m backend.embed_all --force              # re-embed even unchanged rows

Incremental: a row is only re-embedded when its text (or the embedding model) changed, and embeddings of
rows that no longer exist in the source table are removed. Needs OPENAI_API_KEY / OPENAI_BASE_URL in backend/.env.
"""
import argparse
import asyncio
import hashlib

from backend.embedding_sources import SOURCES, Source
from backend.embeddings import embed_texts
from backend.llm import EMBEDDING_MODEL
from backend.supabase_client import supabase

PAGE = 1000
BATCH = 50  # inputs per embeddings request (also keeps each upsert body around 1 MB)
RETRIES = 3


def fetch_all(table: str, columns: str, order_by: str) -> list[dict]:
    rows, start = [], 0
    while True:
        page = supabase.table(table).select(columns).order(order_by).range(start, start + PAGE - 1).execute().data
        rows += page
        if len(page) < PAGE:
            return rows
        start += PAGE


def fingerprint(content: str) -> str:
    return hashlib.sha256(f"{EMBEDDING_MODEL}|{content}".encode()).hexdigest()


async def embed_with_retry(texts: list[str]) -> list[list[float]]:
    for attempt in range(1, RETRIES + 1):
        try:
            return await embed_texts(texts)
        except Exception as exc:  # gateway hiccups and rate limits are retried
            if attempt == RETRIES:
                raise
            print(f"  embedding request failed ({type(exc).__name__}); retry {attempt}/{RETRIES - 1}")
            await asyncio.sleep(3 * attempt)


async def embed_source(name: str, source: Source, dry_run: bool, force: bool) -> None:
    rows = fetch_all(source.table, source.columns, source.key)
    wanted = {}
    for row in rows:
        content = source.build(row)
        if content:
            wanted[str(row[source.key])] = content

    # Only this source's stored fingerprints: filter server-side rather than scanning the whole table.
    stored = {}
    page_start = 0
    while True:
        page = (supabase.table("embeddings").select("source_key,content_hash").eq("source_table", name)
                .order("source_key").range(page_start, page_start + PAGE - 1).execute().data)
        stored.update({r["source_key"]: r["content_hash"] for r in page})
        if len(page) < PAGE:
            break
        page_start += PAGE

    todo = [(key, text) for key, text in wanted.items() if force or stored.get(key) != fingerprint(text)]
    stale = [key for key in stored if key not in wanted]
    print(f"{name}: {len(rows)} rows, {len(wanted)} with text, {len(todo)} to embed, {len(stale)} stale")
    if dry_run:
        return

    for start in range(0, len(todo), BATCH):
        chunk = todo[start:start + BATCH]
        vectors = await embed_with_retry([text for _, text in chunk])
        supabase.table("embeddings").upsert(
            [{"source_table": name, "source_key": key, "content": text, "content_hash": fingerprint(text),
              "model": EMBEDDING_MODEL, "embedding": vector}
             for (key, text), vector in zip(chunk, vectors)],
            on_conflict="source_table,source_key",
        ).execute()
        print(f"  {name}: embedded {min(start + BATCH, len(todo))}/{len(todo)}")
    for start in range(0, len(stale), PAGE):
        supabase.table("embeddings").delete().eq("source_table", name).in_("source_key", stale[start:start + PAGE]).execute()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="*", choices=list(SOURCES), help="sources to embed (default: all)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for name in args.only or list(SOURCES):
        await embed_source(name, SOURCES[name], args.dry_run, args.force)
    if not args.dry_run:
        total = supabase.table("embeddings").select("*", count="exact").limit(1).execute().count
        print(f"Done. embeddings table now holds {total} rows.")


if __name__ == "__main__":
    asyncio.run(main())
