"""
Repository pattern implementation for accessing production_data.

Provides explicit SQL-filtered query methods to enforce the principle
that no pipeline stage should ever process the complete dataset.
Discovery methods support the interactive query parser.
"""

import pandas as pd
import logging
from typing import List

from database.database import Database

logger = logging.getLogger(__name__)


class ProductionRepository:
    """
    Repository pattern implementation for accessing production_data.

    Encapsulates all SQL queries and isolates them from business logic.
    Every public method returns a filtered subset — there is no
    'get_all' by design.
    """

    _TABLE = "production_data"

    def __init__(self, db: Database) -> None:
        """
        Initializes the repository with a database connection manager.

        Args:
            db: Database connection manager instance.
        """
        self.db = db

    # ------------------------------------------------------------------
    # Filtered query methods
    # ------------------------------------------------------------------

    def get_by_machine(self, machine_id: str) -> pd.DataFrame:
        """
        Retrieves all production records for a specific machine.

        Args:
            machine_id: The Machine ID to filter by.

        Returns:
            DataFrame of matching production records.
        """
        logger.info(f"Repository: Filtering by Machine ID = '{machine_id}'")
        query = f'SELECT * FROM {self._TABLE} WHERE "Machine ID" = ?'
        return self._execute_query(query, [machine_id])

    def get_by_machine_and_shift(
        self, machine_id: str, shift: str
    ) -> pd.DataFrame:
        """
        Retrieves production records for a specific machine and shift.

        Args:
            machine_id: The Machine ID to filter by.
            shift: The Shift to filter by (e.g., 'Morning', 'Afternoon', 'Night').

        Returns:
            DataFrame of matching production records.
        """
        logger.info(
            f"Repository: Filtering by Machine ID = '{machine_id}', "
            f"Shift = '{shift}'"
        )
        query = (
            f'SELECT * FROM {self._TABLE} '
            f'WHERE "Machine ID" = ? AND "Shift" = ?'
        )
        return self._execute_query(query, [machine_id, shift])

    def get_by_machine_and_date(
        self, machine_id: str, date: str
    ) -> pd.DataFrame:
        """
        Retrieves production records for a specific machine and date.

        Args:
            machine_id: The Machine ID to filter by.
            date: The date string in YYYY-MM-DD format.

        Returns:
            DataFrame of matching production records.
        """
        logger.info(
            f"Repository: Filtering by Machine ID = '{machine_id}', "
            f"Date = '{date}'"
        )
        query = (
            f'SELECT * FROM {self._TABLE} '
            f'WHERE "Machine ID" = ? AND "Date" = ?'
        )
        return self._execute_query(query, [machine_id, date])

    def get_by_machine_shift_date(
        self, machine_id: str, shift: str, date: str
    ) -> pd.DataFrame:
        """
        Retrieves production records for a specific machine, shift, and date.

        Args:
            machine_id: The Machine ID to filter by.
            shift: The Shift to filter by.
            date: The date string in YYYY-MM-DD format.

        Returns:
            DataFrame of matching production records.
        """
        logger.info(
            f"Repository: Filtering by Machine ID = '{machine_id}', "
            f"Shift = '{shift}', Date = '{date}'"
        )
        query = (
            f'SELECT * FROM {self._TABLE} '
            f'WHERE "Machine ID" = ? AND "Shift" = ? AND "Date" = ?'
        )
        return self._execute_query(query, [machine_id, shift, date])

    # ------------------------------------------------------------------
    # Discovery methods (for query parser & user guidance)
    # ------------------------------------------------------------------

    def get_available_machines(self) -> List[str]:
        """
        Returns a sorted list of distinct Machine IDs in the database.
        Used by the query parser for case-insensitive machine name matching.
        """
        query = f'SELECT DISTINCT "Machine ID" FROM {self._TABLE} ORDER BY "Machine ID"'
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                machines = df["Machine ID"].tolist()
                logger.info(f"Discovery: Found {len(machines)} distinct machines.")
                return machines
        except Exception as e:
            logger.error(f"Failed to retrieve available machines: {e}")
            raise

    def get_available_shifts(self) -> List[str]:
        """
        Returns a sorted list of distinct Shift values in the database.
        Used for validating user-provided shift filters.
        """
        query = f'SELECT DISTINCT "Shift" FROM {self._TABLE} ORDER BY "Shift"'
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                shifts = df["Shift"].tolist()
                logger.info(f"Discovery: Found {len(shifts)} distinct shifts.")
                return shifts
        except Exception as e:
            logger.error(f"Failed to retrieve available shifts: {e}")
            raise

    def get_available_dates(self) -> List[str]:
        """
        Returns a sorted list of distinct Date values in the database.
        Used for validating user-provided date filters.
        """
        query = f'SELECT DISTINCT "Date" FROM {self._TABLE} ORDER BY "Date"'
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
                dates = df["Date"].tolist()
                logger.info(f"Discovery: Found {len(dates)} distinct dates.")
                return dates
        except Exception as e:
            logger.error(f"Failed to retrieve available dates: {e}")
            raise

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _execute_query(
        self, query: str, params: list
    ) -> pd.DataFrame:
        """
        Executes a parameterized SQL query and returns a DataFrame.

        Args:
            query: SQL query string with ? placeholders.
            params: List of parameter values.

        Returns:
            DataFrame of query results.
        """
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                logger.info(f"Query returned {len(df)} records.")
                return df
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise
