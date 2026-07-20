"""
OEE Manufacturing Analytics Assistant — Main Entry Point.

Provides an interactive query loop where users can filter production
data by Machine ID, Date, and/or Shift. Only filtered records flow
through the pipeline; no full-dataset processing is performed.

Pipeline per query:
    User Query → Parse → SQL Filter → Validate → OEE Calculate
    → Error Code Resolve → AI Analysis → Runtime CSVs → Console Summary
"""

import os
import sys
import logging
from typing import Optional

import pandas as pd

from config import DB_FILE_PATH, DEBUG_DIR
from database.init_db import initialize_database
from database.database import Database
from database.repositories import ProductionRepository
from core.validator import DataValidator
from core.oee_calculator import OEECalculator
from analysis.error_code_resolver import ErrorCodeResolver
from analysis.loss_analyzer import LossAnalyzer
from analysis.business_impact import BusinessImpactEngine
from reports.report_generator import ReportGenerator
from core.query_service import QueryService

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", "oee_agent.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# CSV column specifications (no duplicates)
OEE_METRICS_COLUMNS = [
    "Machine ID",
    "Availability",
    "Performance",
    "Quality",
    "OEE",
    "Availability Loss",
    "Performance Loss",
    "Quality Loss",
    "Dominant Loss",
    "Description",
    "Typical Downtime",
]

AI_ANALYSIS_COLUMNS = [
    "Machine ID",
    "Date",
    "Shift",
    "Error Code",
    "OEE",
    "Dominant Loss",
    "AI Validation",
    "Validation Reason",
    "Likely Root Cause",
    "Manufacturing Insight",
]

BUSINESS_IMPACT_COLUMNS = [
    "Machine ID",
    "Date",
    "Shift",
    "OEE",
    "Production Loss (units)",
    "Throughput Loss (units)",
    "Downtime Cost",
    "Scrap Cost",
    "Production Loss Cost",
    "Estimated Business Loss",
    "Primary Business Driver",
    "Business Loss Breakdown",
    "Priority Score",
    "Priority",
    "Top Loss Driver Rank",
]


def _ensure_database() -> None:
    """Initializes the SQLite database if it does not exist."""
    if not os.path.exists(DB_FILE_PATH):
        logger.info(f"Database not found at {DB_FILE_PATH}. Initializing...")
        initialize_database()
    else:
        logger.info(f"Database found at {DB_FILE_PATH}.")


def _display_welcome(available_machines: list[str]) -> None:
    """Displays the welcome banner with available machines."""
    separator = "═" * 56

    print(f"\n  {separator}")
    print(f"    OEE Manufacturing Analytics Assistant")
    print(f"  {separator}")
    print(f"\n  Available Machines:")
    for machine in available_machines:
        print(f"    • {machine}")
    print(f"\n  Query Examples:")
    print(f"    • Show Press_Line_5")
    print(f"    • Show Press_Line_5 Morning Shift")
    print(f"    • Show Press_Line_5 on 2026-06-18")
    print(f"    • Show CNC_Milling_3 Night Shift")
    print(f"\n  Type 'exit' or 'quit' to close.\n")


def _generate_runtime_csvs(
    raw_df: pd.DataFrame,
    validated_df: pd.DataFrame,
    oee_df: pd.DataFrame,
    analysis_df: pd.DataFrame,
) -> None:
    """
    Generates runtime CSVs for the filtered dataset ONLY.

    Files:
        01_raw_data.csv       — Raw filtered production records
        02_validated_data.csv  — Validated filtered records
        03_oee_metrics.csv     — OEE metrics + losses + error resolution
        04_ai_analysis.csv     — AI validation + root cause + observation
        05_business_impact.csv — Estimated business loss and priority rankings
    """
    os.makedirs(DEBUG_DIR, exist_ok=True)

    # 01 — Raw filtered data
    raw_df.to_csv(
        os.path.join(DEBUG_DIR, "01_raw_data.csv"), index=False
    )

    # 02 — Validated data
    validated_df.to_csv(
        os.path.join(DEBUG_DIR, "02_validated_data.csv"), index=False
    )

    # 03 — OEE metrics (selected columns only, no duplicates)
    oee_cols = [c for c in OEE_METRICS_COLUMNS if c in analysis_df.columns]
    analysis_df[oee_cols].to_csv(
        os.path.join(DEBUG_DIR, "03_oee_metrics.csv"), index=False
    )

    # 04 — AI analysis (selected columns only, no duplicates)
    ai_cols = [c for c in AI_ANALYSIS_COLUMNS if c in analysis_df.columns]
    analysis_df[ai_cols].to_csv(
        os.path.join(DEBUG_DIR, "04_ai_analysis.csv"), index=False
    )

    # 05 — Business impact
    biz_cols = [c for c in BUSINESS_IMPACT_COLUMNS if c in analysis_df.columns]
    analysis_df[biz_cols].to_csv(
        os.path.join(DEBUG_DIR, "05_business_impact.csv"), index=False
    )

    logger.info(f"Runtime CSVs generated in {DEBUG_DIR}/")


def _process_query(
    user_query: str,
    query_service: QueryService,
    validator: DataValidator,
    calculator: OEECalculator,
    resolver: ErrorCodeResolver,
    analyzer: LossAnalyzer,
    business_engine: BusinessImpactEngine,
    reporter: ReportGenerator,
) -> None:
    """
    Executes the full analysis pipeline for a single filtered query.

    Pipeline:
        SQL Filter → Validate → OEE Calculate → Error Code Resolve
        → AI Analysis → Business Impact → Runtime CSVs → Console Summary
    """
    logger.info(f"Processing query: {user_query}")

    # 1. NL-to-SQL (Query Service)
    try:
        raw_df, valid_sql = query_service.process_query(user_query)
    except Exception as e:
        print(f"\n  SQL Generation Failed: {e}")
        print("  Please try rephrasing your question.\n")
        return

    if raw_df.empty:
        print(f"\n  No records found for your query.")
        print(f"  SQL Executed:\n  {valid_sql}\n")
        return

    logger.info(f"Fetched {len(raw_df)} filtered records.")
    print(f"\n  Generated SQL:\n  {valid_sql}\n")

    # 2. Validate
    logger.info("Validating filtered data...")
    validated_df = validator.validate(raw_df)

    # 3. Deterministic OEE calculation (includes losses + dominant loss)
    logger.info("Calculating OEE metrics...")
    oee_df = calculator.calculate(validated_df)

    # 4. Error Code Resolution (deterministic knowledge lookup)
    logger.info("Resolving error codes...")
    resolved_df = resolver.resolve(oee_df)

    # 5. AI Manufacturing Intelligence Analysis
    logger.info("Running AI Manufacturing Intelligence analysis...")
    ai_df = analyzer.analyze(resolved_df)

    # 6. Business Impact Engine
    logger.info("Calculating Business Impact...")
    analysis_df = business_engine.calculate(ai_df)

    # 7. Generate runtime CSVs (filtered data only)
    _generate_runtime_csvs(raw_df, validated_df, oee_df, analysis_df)

    # 8. Display console summary (pass user_query instead of query_filter)
    reporter.display_summary(
        df=analysis_df,
        query_filter=None,  # We replaced QueryFilter
        ai_processed=analyzer.ai_processed_count,
        ai_skipped=analyzer.ai_skipped_count,
        groq_response_time=analyzer.groq_response_time,
    )


def main() -> None:
    """
    Main entry point for the OEE Manufacturing Analytics Assistant.

    Runs an interactive query loop where users specify filters
    (Machine ID, Date, Shift). Only filtered records are processed
    through the pipeline.
    """
    logger.info("Starting OEE Manufacturing Analytics Assistant.")

    # Ensure output directories exist
    os.makedirs(DEBUG_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Database initialization
    _ensure_database()

    try:
        # Infrastructure setup
        db = Database()
        repo = ProductionRepository(db)
        available_machines = repo.get_available_machines()

        # Initialize pipeline components
        query_service = QueryService()
        validator = DataValidator()
        calculator = OEECalculator()
        resolver = ErrorCodeResolver()
        analyzer = LossAnalyzer()
        business_engine = BusinessImpactEngine()
        reporter = ReportGenerator(debug_mode=True)

        # Display welcome banner
        _display_welcome(available_machines)

        # Interactive query loop
        while True:
            try:
                user_input = input("  Enter query (or 'exit' to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Goodbye!\n")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\n  Goodbye!\n")
                break

            # Process the query through the full pipeline
            _process_query(
                user_query=user_input,
                query_service=query_service,
                validator=validator,
                calculator=calculator,
                resolver=resolver,
                analyzer=analyzer,
                business_engine=business_engine,
                reporter=reporter,
            )

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
