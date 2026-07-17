# OEE Loss Analysis & Improvement Agent

An enterprise-grade OEE (Overall Equipment Effectiveness) Analytics Agent that deterministically calculates OEE metrics from raw operator data and utilizes LLM-based semantic understanding to classify manufacturing losses according to the Six Big Loss Taxonomy.

## Current Progress & Features (Phase 1)
- **Data Ingestion**: Loads data from CSV securely and reliably into a local SQLite database (`database/oee.db`).
- **Data Validation**: Strict validation pipeline enforcing chronological correctness, physical constraints (downtime <= planned time), and part counts.
- **Deterministic OEE Calculation**: Pure algorithmic evaluation of Availability, Performance, and Quality metrics without hallucinatory AI errors.
- **Reporting & Persistence**: Separates business logic from UI/Reporting and saves all enriched datasets back into `oee_results`.
- **LLM Loss Analysis Engine**: Batch processes operator notes in a single LLM request (Groq API) to deterministically map them into the *Six Big Loss Taxonomy* (e.g. "Equipment Failure", "Process Defects"). Performs a cross-validation consistency check against the mathematically dominant loss to prevent hallucinations.
- **Unit Testing**: Contains full coverage for standard bounds, divide-by-zero checks, and logic validation.

## Project Structure
```text
project_root/
├── analysis/
│   └── loss_analyzer.py      # Combines deterministic losses & LLM categorization
├── core/
│   ├── data_loader.py        # Loads data safely
│   ├── oee_calculator.py     # Deterministic metric calculator
│   ├── reporting.py          # Separated UI/Reporting module
│   └── validator.py          # Ensures data compliance
├── database/
│   ├── database.py           # SQLite interactions via Pandas/parameterized SQL
│   └── init_db.py            # SQLite database initialization
├── data/
│   └── test.csv              # Initial loading dataset
├── llm/
│   ├── groq_client.py        # Groq API interaction logic & retries
│   └── prompts.py            # Prompts and few-shot examples
├── tests/
│   ├── test_calculator.py    # Tests for calculation logic
│   └── test_validator.py     # Tests for validation logic
├── .env                      # API keys (Create this file!)
├── config.py                 # Configuration Paths
├── main.py                   # Application Entrypoint
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

3. **Run the Application**
   ```bash
   python main.py
   ```
   This will run the entire ingestion, validation, calculation, AI classification, and reporting workflow.

4. **Run Unit Tests**
   ```bash
   python -m unittest discover tests/
   ```
