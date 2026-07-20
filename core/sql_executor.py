import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SQLExecutor:
    """
    Executes validated SQL queries against the SQLite database and returns DataFrames.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute(self, query: str) -> pd.DataFrame:
        """
        Executes a SQL SELECT query and returns the result as a pandas DataFrame.
        """
        logger.info(f"Executing SQL query against {self.db_path}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn)
                logger.info(f"SQL execution returned {len(df)} rows.")
                return df
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise ValueError(f"Database execution error: {e}")
