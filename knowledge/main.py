import os
import logging
from config import DB_FILE_PATH, DEBUG_DIR
from database.init_db import initialize_database
from database.database import Database
from database.repositories import ProductionRepository
from core.validator import DataValidator
from core.data_loader import DataLoader
from core.oee_calculator import OEECalculator
from analysis.error_code_resolver import ErrorCodeResolver
from analysis.loss_analyzer import LossAnalyzer
from reports.report_generator import ReportGenerator

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main orchestration workflow for the OEE Analytics Agent.

    Pipeline:
        SQLite → Repository → DataLoader → Validator → OEE Calculator
        → Error Code Resolver → Loss Analyzer (Groq) → Report Generator
    """
    logger.info("Starting OEE Analytics Agent workflow.")

    # Ensure output directories exist
    os.makedirs(DEBUG_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Database initialisation (one-time CSV/Excel → SQLite load)
    # ------------------------------------------------------------------
    if not os.path.exists(DB_FILE_PATH):
        logger.info(f"Database not found at {DB_FILE_PATH}. Initializing...")
        initialize_database()
    else:
        logger.info(f"Database found at {DB_FILE_PATH}.")

    try:
        # --------------------------------------------------------------
        # 2. Infrastructure setup
        # --------------------------------------------------------------
        db = Database()
        repo = ProductionRepository(db)
        data_loader = DataLoader(repo)
        validator = DataValidator()
        calculator = OEECalculator()
        resolver = ErrorCodeResolver()
        analyzer = LossAnalyzer()
        reporter = ReportGenerator(debug_mode=True)

        # --------------------------------------------------------------
        # 3. Fetch raw data from SQLite
        # --------------------------------------------------------------
        logger.info("Fetching raw data from repository...")
        raw_df = data_loader.fetch_raw_data()
        raw_df.to_csv(os.path.join(DEBUG_DIR, "01_raw_data.csv"), index=False)

        # --------------------------------------------------------------
        # 4. Validate
        # --------------------------------------------------------------
        logger.info("Validating data...")
        validated_df = validator.validate(raw_df)
        validated_df.to_csv(os.path.join(DEBUG_DIR, "02_validated_data.csv"), index=False)

        # --------------------------------------------------------------
        # 5. Deterministic OEE calculation
        # --------------------------------------------------------------
        logger.info("Calculating OEE metrics...")
        oee_df = calculator.calculate(validated_df)
        oee_df.to_csv(os.path.join(DEBUG_DIR, "03_oee_analysis.csv"), index=False)

        # --------------------------------------------------------------
        # 6. Error Code Resolution (deterministic knowledge lookup)
        # --------------------------------------------------------------
        logger.info("Resolving error codes...")
        resolved_df = resolver.resolve(oee_df)

        # --------------------------------------------------------------
        # 7. AI Loss Analysis (Groq Manufacturing Analyst)
        # --------------------------------------------------------------
        logger.info("Running AI Loss Analysis...")
        analysis_df = analyzer.analyze(resolved_df)
        analysis_df.to_csv(os.path.join(DEBUG_DIR, "04_loss_analysis.csv"), index=False)

        # --------------------------------------------------------------
        # 8. Reporting
        # --------------------------------------------------------------
        reporter.display_summary(analysis_df)

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
