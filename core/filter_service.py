import sqlite3
import pandas as pd
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class FilterService:
    """
    Constructs and executes parameterized SQL queries based on explicit filters.
    Bypasses the LLM entirely for deterministic, fast querying while preserving
    the exact same 10-column schema expected by the analytics pipeline.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def process_filters(self, 
                        plant: Optional[str] = None,
                        line: Optional[str] = None,
                        machine: Optional[str] = None,
                        shift: Optional[str] = None,
                        from_date: Optional[str] = None,
                        to_date: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
        """
        Builds and executes a parameterized SQL query based on provided filters.

        Returns:
            Tuple containing:
            - pandas DataFrame of the raw filtered data
            - The executed parameterized SQL string (for UI transparency)
        """
        logger.info(f"FilterService processing filters: plant={plant}, line={line}, machine={machine}, shift={shift}, from={from_date}, to={to_date}")

        base_query = """
            SELECT 
                dim_date.full_date AS "Date", 
                dim_machine.machine_code AS "Machine ID", 
                dim_shift.shift_name AS "Shift", 
                fact_production.planned_time AS "Planned Time (min)", 
                COALESCE(SUM(fact_downtime.duration), 0) AS "Downtime (min)", 
                fact_production.total_parts AS "Total Parts Produced", 
                fact_production.defective_parts AS "Defective Parts", 
                fact_production.ideal_cycle_time AS "Ideal Cycle Time (min/unit)", 
                COALESCE(dim_reason.error_code, 'DT-00') AS "Error Code", 
                dim_operator.operator_code AS "Operator ID"
            FROM fact_production
            LEFT JOIN fact_downtime ON fact_production.production_id = fact_downtime.production_id
            LEFT JOIN dim_reason ON fact_downtime.reason_id = dim_reason.reason_id
            JOIN dim_machine ON fact_production.machine_id = dim_machine.machine_id
            JOIN dim_line ON dim_machine.line_id = dim_line.line_id
            JOIN dim_plant ON dim_line.plant_id = dim_plant.plant_id
            JOIN dim_date ON fact_production.date_key = dim_date.date_key
            JOIN dim_shift ON fact_production.shift_id = dim_shift.shift_id
            JOIN dim_operator ON fact_production.operator_id = dim_operator.operator_id
            WHERE 1=1
        """

        conditions = []
        params = []

        if plant:
            conditions.append("dim_plant.plant_name = ?")
            params.append(plant)
        
        if line:
            conditions.append("dim_line.line_name = ?")
            params.append(line)
            
        if machine:
            conditions.append("dim_machine.machine_code = ?")
            params.append(machine)
            
        if shift:
            conditions.append("dim_shift.shift_name = ?")
            params.append(shift)
            
        if from_date:
            conditions.append("dim_date.full_date >= ?")
            params.append(from_date)
            
        if to_date:
            conditions.append("dim_date.full_date <= ?")
            params.append(to_date)

        # Append conditions
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Group by all non-aggregated columns to ensure correct granularity (1 row per downtime event per production run, or 1 row per healthy production run)
        base_query += """
            GROUP BY 
                dim_date.full_date,
                dim_machine.machine_code,
                dim_shift.shift_name,
                fact_production.planned_time,
                fact_production.total_parts,
                fact_production.defective_parts,
                fact_production.ideal_cycle_time,
                COALESCE(dim_reason.error_code, 'DT-00'),
                dim_operator.operator_code
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(base_query, conn, params=params)
                logger.info(f"FilterService returned {len(df)} rows.")
                
                # Reconstruct query for UI transparency (replacing ? with values)
                ui_query = base_query
                for p in params:
                    # Very basic substitution for UI display only (not for execution)
                    if isinstance(p, str):
                        ui_query = ui_query.replace("?", f"'{p}'", 1)
                    else:
                        ui_query = ui_query.replace("?", str(p), 1)
                        
                return df, ui_query.strip()
        except Exception as e:
            logger.error(f"SQL execution failed in FilterService: {e}")
            raise ValueError(f"Database execution error: {e}")
