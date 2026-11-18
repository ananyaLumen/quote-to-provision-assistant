"""Load the source data into Supabase.

    python load_data.py                  # load every table
    python load_data.py --only evcs      # load selected tables
    python load_data.py --dry-run        # transform only, write nothing

Idempotent: rows are upserted on their natural key (or source_file + source_row),
so re-running refreshes the data instead of duplicating it.
"""
import argparse
import json
import logging
import sys
import time

from etl import TABLES

log = logging.getLogger("load_data")

# PostgREST rejects very large bodies, and the wide Excel exports produce big JSONB rows,
# so batches are capped by both row count and serialized size.
MAX_ROWS = 500
MAX_BYTES = 1_500_000
RETRIES = 3


def batches(rows):
    batch, size = [], 0
    for row in rows:
        row_size = len(json.dumps(row, default=str))
        if batch and (len(batch) >= MAX_ROWS or size + row_size > MAX_BYTES):
            yield batch
            batch, size = [], 0
        batch.append(row)
        size += row_size
    if batch:
        yield batch


def upsert(client, table, batch, conflict):
    for attempt in range(1, RETRIES + 1):
        try:
            client.table(table).upsert(batch, on_conflict=conflict).execute()
            return
        except Exception as exc:  # network blips and statement timeouts are retried
            if attempt == RETRIES:
                raise
            log.warning("%s: batch failed (%s); retry %d/%d", table, str(exc)[:200], attempt, RETRIES - 1)
            time.sleep(2 * attempt)


def load_table(client, table, dry_run):
    generator, conflict = TABLES[table]
    total = 0
    for batch in batches(generator()):
        if not dry_run:
            upsert(client, table, batch, conflict)
        total += len(batch)
        log.info("%s: %d rows", table, total)
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="*", choices=list(TABLES), help="tables to load (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="transform the data but do not write")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = None
    if not args.dry_run:
        from supabase_client import supabase as client

    counts = {}
    for table in args.only or list(TABLES):
        counts[table] = load_table(client, table, args.dry_run)

    print("\nLoaded" if not args.dry_run else "\nDry run (nothing written)")
    for table, count in counts.items():
        print(f"  {table:<24}{count:>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
