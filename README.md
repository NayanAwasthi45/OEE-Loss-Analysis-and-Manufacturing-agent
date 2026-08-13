# OEE Loss Analysis & Improvement Agent

An enterprise-grade OEE (Overall Equipment Effectiveness) Analytics Agent that deterministically calculates OEE metrics from raw operator data and utilizes LLM-based semantic understanding to classify manufacturing losses according to the Six Big Loss Taxonomy.

## Features

### Phase A: Core Intelligence
- **Data Ingestion**: Dynamic NLP query parsing mapped directly to the local SQLite star schema (`data/oee_star_enterprise_corrected.db`).
- **Data Validation**: Strict constraint checks on chronological and physical parameters.
- **Deterministic OEE Calculation**: Pure algorithmic evaluation of Availability, Performance, and Quality metrics.
- **Manufacturing Knowledge Injection**: Pulls domain expertise (Machine Profiles, TPM Playbooks) directly into context.
- **LLM Loss Analysis Engine**: Leverages Groq API to provide AI validation, root causes, and manufacturing insights for problematic records.

### Phase B: Business Impact Engine
- **Configurable Economics**: Uses `business_config.json` for downtime, scrap, and production loss cost assumptions.
- **Financial Mapping**: Translates time and unit losses into explicit currency-based business loss metrics.
- **Priority Scoring Model**: Ranks machines and losses using a weighted severity algorithm (OEE, Business Loss, Downtime, Error Category).

### Phase C: Enterprise Dashboard (Modernized)
- **FastAPI Backend**: A thin REST wrapper exposing the existing pipeline.
- **React/Vite Frontend**: A premium, industrial-styled dashboard (Siemens MindSphere / Power BI aesthetic).
- **Rich Visualizations**: Recharts-powered interactive graphs (OEE Gauges, Pillar Trendlines, Loss Distribution Donuts, and Breakdown Bars).
- **Export Capabilities**: 1-click Export to PDF for preserving the current state of the dashboard without losing context.
- **AI Loading Sequence**: Transparent 5-step progress indication when running complex LLM chains.

### Phase D: Advanced Scenarios & RAG Simulation
- **Deterministic ROI Projections**: Calculates exact recovered units and cost savings directly from record-level data.
- **Top-2 Contributor Ranking**: Dynamically targets the worst-performing machines for a specific KPI (Availability, Performance, Quality).
- **Domain RAG Integration**: Injects actual Standard Operating Procedures (SOPs) based on dominant machine and error codes to provide highly targeted improvement plans.

### Phase E: Ticketing System & Autonomous Agent
- **Automated Threshold Ticketing**: The backend proactively scans OEE records during analysis and automatically files database tickets for severe anomalies (OEE < 50%, AI Validation = Mismatch, or Business Loss > ₹80,000).
- **Idempotency Safeguards**: Enforces UNIQUE constraints (`date`, `shift`, `machine_id`) to prevent duplicate automated tickets.
- **Integrated Maintenance Ticketing**: Directly raise maintenance tickets for records manually from the UI when needed.
- **Database Persistence**: Tickets are saved to the `ticket` table with metadata (Date, Shift, Machine ID, Status).
- **Optimistic UI Updates**: Instant feedback upon raising a ticket, changing the action button to a confirmed status.

## Project Structure
```text
project_root/
├── api/
│   └── server.py             # FastAPI REST layer with Endpoints & Tickets
├── analysis/
│   ├── business_impact.py    # Phase B: Financial cost and Priority Scoring
│   ├── error_code_resolver.py # Maps standard error codes
│   └── loss_analyzer.py      # LLM Groq AI Analysis Orchestrator
├── copilot/
│   ├── scenarios/            # Phase D: Deterministic simulation logic
│   ├── chat_service.py       # Orchestrates chat modes and simulation
│   └── scenario_context_builder.py 
├── core/
│   ├── schema_loader.py      # Dynamically maps natural language to DB entities
│   ├── sql_generator.py      # Translates natural language queries to SQL
│   ├── oee_calculator.py     # Deterministic metric calculator
│   └── validator.py          # Enforces data compliance
├── dashboard_upgraded/       # Phase C: Premium React + Vite Frontend App
│   ├── src/
│   │   ├── components/       # UI Cards, Charts, Layouts, Tables
│   │   ├── pages/            # Dashboard Views
│   │   └── services/         # API integrations
│   └── package.json
├── database/
│   ├── database.py           # SQLite connections
│   └── init_db.py            # SQLite schema initialization
├── knowledge/                # Domain Knowledge base JSONs and PDFs
├── rag/                      # RAG components (DocumentLoader, Chunker, Retriever)
├── .env                      # API keys (Create this file!)
├── business_config.json      # Phase B configurable costs
├── main.py                   # CLI Application Entrypoint
├── requirements.txt          # Python dependencies
└── README.md
```

## Authentication Details

The dashboard is secured using Role-Based JWT Authentication. You must log in using one of the following provisioned accounts (all use the same demonstration password):

| Role | Username | Password |
|------|----------|----------|
| Plant Manager | `plant_user` | `password123` |
| Production Admin | `production_user` | `password123` |
| CLI Operator | `cli_user` | `password123` |
| Operational Excellence | `op_ex_user` | `password123` |

## Setup Instructions

1. **Install Dependencies**
   Make sure you are in your active virtual environment, then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   The application requires a Groq API Key to perform semantic classifications.
   Open the `.env` file at the root of the project and replace the placeholder with your actual Groq API Key:
   ```env
   GROQ_API_KEY=gsk_your_actual_key_here
   ```
   > **Note**: If the API key is missing or invalid, the app will not crash. It will deterministically fallback the classification status to "Pending Review" and output "Unknown".

3. **Install Dashboard Frontend Dependencies**
   ```bash
   cd dashboard_upgraded
   npm install
   cd ..
   ```

## How to Run

### Enterprise Dashboard UI (Recommended)
To run the premium React UI, you need two terminal windows:

**Terminal 1 (Backend API):**
```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend UI):**
```bash
cd dashboard_upgraded
npm run dev
```
Then navigate to **http://localhost:5173** in your web browser. Type a query in the search bar (e.g. `Show yesterday's OEE`) and click Analyze! You can expand production rows to view AI insights and raise tickets for anomalies.

## Unit Testing
```bash
pytest tests/ -v
```
