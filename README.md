# Quote-to-Provision Assistant

AI assistant that turns a customer requirement into a validated solution, delivery roadmap and software plan.
This repo currently contains the data layer (Supabase/PostgreSQL), a small FastAPI backend and a frontend shell.

## Data layer

Source files in `data/` are loaded into Supabase by `backend/load_data.py`.

| Table | Source | Rows |
|---|---|---|
| `product_catalog` | `catalog/product_catalog*.json` (mock + real) | 23 |
| `locations` | `inventory/inventory*.json` (mock + real) | 109 |
| `past_projects` | `projects/past_projects*.json` (synthetic + real) | 16 |
| `mcgw_pricing` | MultiCloudGateway Advisor-MCGW-GroupedPricing.xlsx | 212 |
| `uni_sites` | Location_Site.xlsx | 10,495 |
| `customer_ports` | CustomerPorts.xlsx | 2,909 |
| `whitelisted_ports` | WhitelistedPorts.xlsx | 10,488 |
| `evcs` | EVCs 1.xlsx | 9,646 |
| `provisioning_requests` | EdgeIPVPN, EdgeInternet, DyconIPVPN 3 | 11,006 |
| `service_order_failures` | ServiceOrderFailure Root Cause Agent (x3), EOD_Failures | 3,077 |
| `inventory_dq_issues` | InventoryDataQualityAgent.xlsx | 2,956 |
| `provisioning_orders`, `bom_items`, `site_allocations` | produced by the assistant | 0 |
| `embeddings` | pgvector embeddings of the text sources below, written by `backend/embed_all.py` | 5,977 |

Embedded sources: `past_projects` (16), `product_catalog` (23), `locations` (109), `mcgw_pricing` (212),
`service_order_failures` (2,695 rows that have a message), `inventory_dq_issues` (2,922 rows with issues).
The structured operational tables (ports, EVCs, UNI sites, provisioning requests) are deliberately not embedded:
they are identifiers and numbers that SQL filters handle better. Search with the `match_embeddings(query_embedding, source_name, match_count)` SQL function.

Rows carry a `source` / `data_quality_label` so mock, synthetic and real data can be told apart.
Wide Excel exports keep their key fields as columns and the rest as compact JSONB (`details`).
Every table has Row Level Security enabled with no policies: the publishable key can read nothing,
and only the backend (secret key) can access the data, because it includes real customer names, BANs and addresses.

## Setup

```powershell
python -m venv backend\venv; .\backend\venv\Scripts\Activate.ps1
pip install -r requirements.txt -r backend\requirements.txt
copy backend\.env.example backend\.env        # then fill in the values (incl. OPENAI_API_KEY)
```

1. Create the tables: paste `backend/sql/schema.sql` into the Supabase SQL Editor (safe to re-run), or run
   `python backend\apply_schema.py` (needs `DATABASE_URL`; URL-encode special characters in the password,
   e.g. `@` becomes `%40`). This also enables the `vector` extension used for similar-project search.
2. Load the data: `python backend\load_data.py` (re-runnable; `--dry-run` transforms without writing, `--only evcs` for one table).
3. Embed the text sources: `python -m backend.embed_all` (run from the repo root; incremental, so re-run whenever the data changes;
   `--dry-run` shows what would be embedded, `--only product_catalog` limits it to one source).
Then start the backend and the frontend (see [Run the app](#run-the-app)).

`python backend\etl.py --stats` reports row counts, column fill rates and payload sizes without touching the database.

## Run the app

Connect to the corporate network/VPN first: the backend calls the internal LLM gateway. Use two terminals.

**Terminal 1: backend** (run from the repo root, not from `backend/`)

```powershell
cd "<path-to>\quote-to-provision-assistant"
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs. Health check: http://localhost:8000/health.
Start it with `python -m uvicorn` rather than the `uvicorn` command: on managed machines the `uvicorn.exe`
launcher can be blocked by the Approved Products List, while `python.exe` is not.

**Terminal 2: frontend**

```powershell
cd "<path-to>\quote-to-provision-assistant\frontend"
npm install        # first time only
npm run dev
```

Open http://localhost:5173. The UI calls `POST /quote` on `http://localhost:8000`; set `VITE_API_URL` to use another backend.
A quote takes about 20-60 seconds because the backend makes several LLM calls.

| Problem | Fix |
|---|---|
| `No module named 'backend'` | Run uvicorn from the repo root. |
| `address already in use` (port 8000) | `Get-NetTCPConnection -LocalPort 8000 -State Listen \| ForEach-Object { Stop-Process -Id $_.OwningProcess }` |
| UI says "Can't reach the API" | The backend isn't running, or you are off the VPN. |
| `OPTIONS /quote ... 400` in the backend log | The UI is opened from an origin the API doesn't allow. The log names it; add it to `CORS_ORIGINS` (comma-separated) and restart. `localhost`, private IPs and this machine's hostname are allowed by default. |
| `vite` blocked | `node node_modules\vite\bin\vite.js --host 0.0.0.0` |

## Quote pipeline

`POST /quote` runs the pipeline in `backend/pipeline.py` over a shared `QuoteState` (see `docs/module-contract.md`).

| Step | Module | Status |
|---|---|---|
| Requirement extraction | `agents/extractor.py` (OpenAI structured output, `schemas/requirement.py`) | implemented |
| Similar-project retrieval | `agents/retriever.py` (OpenAI embeddings + pgvector `match_past_projects`) | implemented |
| Validation | `agents/validator.py` (catalog, locations, inventory presence and order history via SQL; no LLM) | implemented |
| Network solution | `agents/network.py` (catalog + MCGW rate card; BOM, cost range, schema-valid draft provisioning JSON; no LLM) | implemented |
| Software solution | `agents/software.py` (GPT-4o plan; effort and cost totals computed in code) | implemented |
| Proposal | `agents/proposal.py` (deterministic assembly, roadmap and costs; LLM writes only the summary, guarded against invented figures) | implemented |

Design rules shared by the validator and the network agent live in `backend/design.py`. Planning assumptions you may want to change:
`DEFAULT_SLA_PCT` (design.py), the contingency percentages (network.py) and `SOFTWARE_DAY_RATE_USD` (env).

The data endpoints (`/api/products`, `/api/locations`, `/api/projects`, ...) live in `backend/api/data_routes.py`.

## Schemas

`schemas/` holds the proposal, network and provisioning schemas; see `schemas/SCHEMA_DOCUMENTATION.md`.
