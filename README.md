# OEE Loss Analysis & Improvement Agent

# OEE Loss Analysis & Improvement Agent

An enterprise-grade OEE (Overall Equipment Effectiveness) Analytics Agent that deterministically calculates OEE metrics from raw operator data and utilizes LLM-based semantic understanding to classify manufacturing losses according to the Six Big Loss Taxonomy.

## Features

### Phase A: Core Intelligence
- **Data Ingestion**: Interactive NLP query parsing with local SQLite repository (`database/oee.db`).
- **Data Validation**: Strict constraint checks on chronological and physical parameters.
- **Deterministic OEE Calculation**: Pure algorithmic evaluation of Availability, Performance, and Quality metrics.
- **Manufacturing Knowledge Injection**: Pulls domain expertise (Machine Profiles, TPM Playbooks) directly into context.
- **LLM Loss Analysis Engine**: Leverages Groq API to provide AI validation, root causes, and manufacturing insights for problematic records.

### Phase B: Business Impact Engine
- **Configurable Economics**: Uses `business_config.json` for downtime, scrap, and production loss cost assumptions.
- **Financial Mapping**: Translates time and unit losses into explicit currency-based business loss metrics.
- **Priority Scoring Model**: Ranks machines and losses using a weighted severity algorithm (OEE, Business Loss, Downtime, Error Category).

### Phase C: Enterprise Dashboard
- **FastAPI Backend**: A thin REST wrapper exposing the existing pipeline without altering the core CLI application.
- **React/Vite Frontend**: A premium, industrial-styled dashboard (Tailwind CSS, shadcn/ui).
- **Rich Visualizations**: Recharts-powered interactive graphs (OEE Gauges, Pillar Trendlines, Loss Distribution Donuts, and Breakdown Bars).
- **Manufacturing AI Panel**: Dedicated UI component showcasing Groq-powered validations and root causes.

## Project Structure
```text
project_root/
├── api/
│   └── server.py             # FastAPI REST layer wrapper
├── analysis/
│   ├── business_impact.py    # Phase B: Financial cost and Priority Scoring
│   ├── error_code_resolver.py # Maps standard error codes
│   └── loss_analyzer.py      # LLM Groq AI Analysis Orchestrator
├── core/
│   ├── data_loader.py        # SQLite query handler
│   ├── oee_calculator.py     # Deterministic metric calculator
│   ├── query_parser.py       # Natural language parser
│   └── validator.py          # Enforces data compliance
├── dashboard/                # Phase C: React + Vite Frontend App
│   ├── src/
│   │   ├── components/       # UI Cards, Charts, Layouts, Tables
│   │   ├── pages/            # Dashboard Views
│   │   └── services/         # API integrations
│   ├── index.html
│   └── package.json
├── database/
│   ├── database.py           # SQLite connections
│   ├── init_db.py            # SQLite schema initialization
│   └── repositories.py       # Query abstractions
├── knowledge/                # Domain Knowledge base JSONs
├── llm/
│   └── groq_client.py        # Groq API client
├── reports/
│   └── report_generator.py   # Console reporting formatter
├── tests/                    # Pytest test suite
├── .env                      # API keys (Create this file!)
├── business_config.json      # Phase B configurable costs
├── config.py                 # Configuration Paths
├── main.py                   # CLI Application Entrypoint
├── requirements.txt          # Python dependencies
└── README.md
```

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

4. **Install Dashboard Frontend Dependencies**
   ```bash
   cd dashboard
   npm install
   cd ..
   ```

## How to Run

### Option 1: Interactive CLI (Phase A & B)
You can use the backend terminal application exactly as originally designed.
```bash
python main.py
```
*Enter a query such as `Show Press_Line_5 Morning Shift` in the prompt.*

### Option 2: Enterprise Dashboard UI (Phase C)
To run the premium React UI, you need two terminal windows:

**Terminal 1 (Backend API):**
```bash
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend UI):**
```bash
cd dashboard
npm run dev
```
Then navigate to **http://localhost:5173** in your web browser. Type a query in the search bar and click Analyze!

## Unit Testing
```bash
pytest tests/ -v
```
