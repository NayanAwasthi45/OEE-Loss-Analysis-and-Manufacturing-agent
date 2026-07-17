import sqlite3
import pandas as pd
import logging
from config import CSV_FILE_PATH, DB_FILE_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_database() -> None:
    """
    Initializes the SQLite database using data from the source file.

    Supports both CSV (.csv) and Excel (.xlsx / .xls) formats.
    Reads the file, connects to SQLite, and creates / replaces
    the 'production_data' table with the file contents.
    """
    conn = None
    try:
        logger.info(f"Reading source file from: {CSV_FILE_PATH}")

        if CSV_FILE_PATH.endswith((".xlsx", ".xls")):
            df = pd.read_excel(CSV_FILE_PATH)
        else:
            df = pd.read_csv(CSV_FILE_PATH)

        logger.info(f"Loaded {len(df)} records from source file.")

        logger.info(f"Connecting to SQLite database at: {DB_FILE_PATH}")
        conn = sqlite3.connect(DB_FILE_PATH)

        logger.info("Inserting records into the 'production_data' table...")
        df.to_sql("production_data", conn, if_exists="replace", index=False)

        logger.info("Database initialization completed successfully.")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_database()
