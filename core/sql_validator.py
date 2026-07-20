import re
import logging

logger = logging.getLogger(__name__)

class SQLValidator:
    """
    Strictly validates generated SQL to prevent SQL injection or destructive operations.
    Only allows SELECT statements and rejects multiple statements or dangerous keywords.
    """

    # Keywords that are strictly forbidden anywhere in the query
    FORBIDDEN_KEYWORDS = {
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "PRAGMA", "ATTACH", "DETACH", "CREATE", "REPLACE"
    }

    def validate(self, sql_query: str) -> str:
        """
        Validates the SQL query. 
        Returns the query if valid. Raises ValueError if invalid.
        """
        if not sql_query or not sql_query.strip():
            raise ValueError("Generated SQL is empty.")

        query = sql_query.strip()
        query_upper = query.upper()

        # 1. Must start with SELECT
        if not query_upper.startswith("SELECT"):
            raise ValueError(f"Only SELECT queries are allowed. Query started with: {query.split()[0] if query.split() else 'Unknown'}")

        # 2. Prevent multiple statements (no semicolons allowed except optionally at the very end)
        # Remove a trailing semicolon if present for checking
        query_no_trailing = query.rstrip(';')
        if ';' in query_no_trailing:
            raise ValueError("Multiple SQL statements are not allowed.")

        # 3. Check for forbidden keywords (word boundaries to prevent false positives like 'DROP' in 'BACKDROP')
        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", query_upper):
                raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

        logger.info("SQL Validation passed.")
        return query
