"""
Data Loader for the OEE Manufacturing Analytics Assistant.

Routes structured QueryFilter objects to the appropriate repository
method. Never loads the full dataset — always requires at least one
filter criterion.
"""

import pandas as pd
import logging
from typing import Optional

from core.query_parser import QueryFilter
from database.repositories import ProductionRepository

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Routes filtered queries to the appropriate repository method.

    Every query must include at least a Machine ID. The loader
    selects the most specific repository method based on which
    filters are present in the QueryFilter.
    """

    def __init__(self, repo: ProductionRepository) -> None:
        """
        Initializes the DataLoader.

        Args:
            repo: The production data repository instance.
        """
        self.repo = repo

    def fetch_filtered_data(self, query_filter: QueryFilter) -> pd.DataFrame:
        """
        Loads filtered production data from the repository.

        Routes to the most specific repository method based on the
        combination of filters in the QueryFilter.

        Args:
            query_filter: Parsed query filter with at least one criterion.

        Returns:
            DataFrame of matching production records.

        Raises:
            ValueError: If the QueryFilter is empty (no criteria).
        """
        if query_filter.is_empty:
            raise ValueError(
                "DataLoader requires at least one filter criterion. "
                "Provide a Machine ID, Shift, or Date."
            )

        machine_id = query_filter.machine_id
        shift = query_filter.shift
        date = query_filter.date

        # Route to the most specific repository method
        if machine_id and shift and date:
            logger.info(
                f"Loading data: Machine={machine_id}, Shift={shift}, Date={date}"
            )
            df = self.repo.get_by_machine_shift_date(machine_id, shift, date)

        elif machine_id and shift:
            logger.info(f"Loading data: Machine={machine_id}, Shift={shift}")
            df = self.repo.get_by_machine_and_shift(machine_id, shift)

        elif machine_id and date:
            logger.info(f"Loading data: Machine={machine_id}, Date={date}")
            df = self.repo.get_by_machine_and_date(machine_id, date)

        elif machine_id:
            logger.info(f"Loading data: Machine={machine_id}")
            df = self.repo.get_by_machine(machine_id)

        else:
            # Shift-only or Date-only queries without Machine ID
            # Fall back to the most general filtered approach
            raise ValueError(
                "DataLoader requires at least a Machine ID filter. "
                "Please specify a machine (e.g., 'Show Press_Line_5')."
            )

        logger.info(f"Loaded {len(df)} records matching filter: {query_filter.describe()}")
        return df
