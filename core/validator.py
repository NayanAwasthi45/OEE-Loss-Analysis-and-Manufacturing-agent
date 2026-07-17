import pandas as pd
import logging
from analysis.error_code_resolver import ErrorCodeResolver

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates the production data DataFrame against predefined rules
    and ensures every Error Code exists in the knowledge base.
    """

    REQUIRED_COLUMNS = [
        "Date",
        "Machine ID",
        "Shift",
        "Planned Time (min)",
        "Downtime (min)",
        "Total Parts Produced",
        "Defective Parts",
        "Ideal Cycle Time (min/unit)",
        "Error Code",
        "Operator ID",
    ]

    def __init__(self) -> None:
        self._resolver = ErrorCodeResolver()

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates the DataFrame columns, data rules, and error codes.

        Args:
            df: The DataFrame to validate.

        Returns:
            The validated DataFrame (unchanged).

        Raises:
            ValueError: If any validation rule fails.
        """
        logger.info("Starting data validation.")

        if df is None or df.empty:
            raise ValueError("Data validation failed: DataFrame is empty or None.")

        self._validate_columns(df)
        self._validate_rules(df)
        self._validate_error_codes(df)

        logger.info("Data validation completed successfully.")
        return df

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Checks if all required columns are present."""
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Data validation failed: Missing required columns: {missing}"
            )

    def _validate_rules(self, df: pd.DataFrame) -> None:
        """Validates logical business rules for the data values."""

        if not (df["Planned Time (min)"] > 0).all():
            raise ValueError(
                "Data validation failed: 'Planned Time (min)' must be > 0."
            )

        if not (df["Downtime (min)"] >= 0).all():
            raise ValueError(
                "Data validation failed: 'Downtime (min)' must be >= 0."
            )

        if not (df["Downtime (min)"] <= df["Planned Time (min)"]).all():
            raise ValueError(
                "Data validation failed: 'Downtime (min)' cannot be greater "
                "than 'Planned Time (min)'."
            )

        if not (df["Total Parts Produced"] >= df["Defective Parts"]).all():
            raise ValueError(
                "Data validation failed: 'Total Parts Produced' must be >= "
                "'Defective Parts'."
            )

        if not (df["Ideal Cycle Time (min/unit)"] > 0).all():
            raise ValueError(
                "Data validation failed: 'Ideal Cycle Time (min/unit)' must be > 0."
            )

    def _validate_error_codes(self, df: pd.DataFrame) -> None:
        """Ensures every Error Code exists in the knowledge base."""
        valid_codes = self._resolver.valid_codes
        unknown = set(df["Error Code"].unique()) - valid_codes
        if unknown:
            raise ValueError(
                f"Data validation failed: Unknown Error Codes: {sorted(unknown)}"
            )
