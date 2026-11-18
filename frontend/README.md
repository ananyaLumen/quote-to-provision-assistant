# Quote-to-Provision Assistant — Frontend starter

A React + Vite frontend prototype for the hackathon project.

## Requirements
- Node.js 18 or newer
- npm

## Run locally
1. Extract this ZIP file.
2. Open the extracted `quote-to-provision-frontend` folder in VS Code.
3. Open the VS Code terminal.
4. Run:

```bash
npm install
npm run dev
```

5. Open the local URL printed by Vite (usually http://localhost:5173).

## Run with the live backend
The UI calls `POST /quote` on the FastAPI backend, so start the backend first. Connect to the corporate network/VPN
(the backend calls the internal LLM gateway) and use two terminals.

**Terminal 1: backend** (from the repo root, not from `backend/`)

```powershell
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs. If `uvicorn.exe` is blocked by the Approved Products List, this `python -m` form still works.

**Terminal 2: frontend** (this folder)

```powershell
npm install   # first time only
npm run dev
```

Then open http://localhost:5173. Set `VITE_API_URL` to point at a different backend (default `http://localhost:8000`).
A quote takes about 20-60 seconds. If the UI says it can't reach the API, the backend isn't running or you are off the VPN.

## Current functionality
- Dark-mode dashboard and customer requirement input
- Sample requirement prefilled
- Simulated AI processing workflow
- Proposal overview with illustrative metrics
- Network design and mock BOM
- Software plan and roadmap
- Synthetic similar-project retrieval examples
- Mock provisioning JSON viewer
- JSON download and browser print-to-PDF

## Important demo limitations
All proposal figures, risk, confidence, project matches, BOM and configuration are illustrative synthetic demo content. The workflow is simulated in the browser. It does not call an LLM, retrieve real project records, calculate a live quote, connect to ServiceNow, or provision network services.

## Backend integration
The frontend is intentionally structured so the demo data can later be replaced by API responses from your team's FastAPI backend. Agree endpoint names and JSON schemas with the backend team before wiring it up.
