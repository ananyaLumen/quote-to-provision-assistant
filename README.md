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

Rows carry a `source` / `data_quality_label` so mock, synthetic and real data can be told apart.
Wide Excel exports keep their key fields as columns and the rest as compact JSONB (`details`).
Every table has Row Level Security enabled with no policies: the publishable key can read nothing,
and only the backend (secret key) can access the data, because it includes real customer names, BANs and addresses.

## Setup

```powershell
cd backend
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # then fill in the values
```

1. Create the tables: paste `backend/sql/schema.sql` into the Supabase SQL Editor, or run `python apply_schema.py`
   (needs `DATABASE_URL`; URL-encode special characters in the password, e.g. `@` becomes `%40`).
2. Load the data: `python load_data.py` (re-runnable; use `--dry-run` to transform without writing, `--only evcs` for one table).
3. Start the API: `uvicorn main:app --reload --port 8000`, then open http://localhost:8000/docs.

`python etl.py --stats` reports row counts, column fill rates and payload sizes without touching the database.

## Schemas

`schemas/` holds the proposal, network and provisioning schemas; see `schemas/SCHEMA_DOCUMENTATION.md`.
