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
