import pandas as pd
import logging
from typing import Tuple

from config import DB_FILE_PATH
from core.schema_loader import SchemaLoader
from core.sql_generator import SQLGenerator
from core.sql_validator import SQLValidator
from core.sql_executor import SQLExecutor

logger = logging.getLogger(__name__)

class QueryService:
    """
    Orchestrates the entire NL-to-SQL pipeline.
    
    User Query -> Schema Load -> LLM Generation -> Validation -> Execution -> DataFrame
    """

    def __init__(self):
        self.schema_loader = SchemaLoader(DB_FILE_PATH)
        self.sql_generator = SQLGenerator()
        self.sql_validator = SQLValidator()
        self.sql_executor = SQLExecutor(DB_FILE_PATH)

    def process_query(self, user_query: str) -> Tuple[pd.DataFrame, str]:
        """
        Processes a natural language query and returns the executed DataFrame and the generated SQL.
        
        Returns:
            Tuple containing:
            - pandas DataFrame of the raw filtered data matching the pipeline requirements.
            - The validated SQL string that was executed.
        """
        logger.info(f"QueryService processing NL query: '{user_query}'")

        # 1. Load schema
        schema_context = self.schema_loader.get_schema_context()

        # 2. Generate SQL
        raw_sql = self.sql_generator.generate_sql(user_query, schema_context)
        
        # 3. Validate SQL
        try:
            valid_sql = self.sql_validator.validate(raw_sql)
        except ValueError as e:
            logger.error(f"SQL Validation failed. Rejected SQL:\n{raw_sql}")
            raise ValueError(f"Generated SQL was rejected: {e}")

        # 4. Execute SQL
        df = self.sql_executor.execute(valid_sql)

        return df, valid_sql
