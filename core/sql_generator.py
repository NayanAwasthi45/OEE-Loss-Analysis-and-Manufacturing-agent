import os
import re
import logging
from typing import Optional
from dotenv import load_dotenv

try:
    import groq
except ImportError:
    groq = None

logger = logging.getLogger(__name__)


class SQLGenerator:
    """
    Translates Natural Language into SQLite SQL queries using an LLM (Groq).
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.error("GROQ_API_KEY is missing. SQL generation will fail.")
            self.client = None
        else:
            if groq is None:
                logger.error("groq package is missing.")
                self.client = None
            else:
                self.client = groq.Groq(api_key=api_key)

        self.system_prompt = """
You are an expert SQLite Database Administrator and Data Engineer.
Your task is to translate natural language questions into highly optimized, read-only SQLite SELECT queries based on the provided star schema.

CRITICAL REQUIREMENTS:
1. You MUST generate ONLY the raw SQL code. No markdown formatting, no explanations, no `sql` codeblocks. Just the raw text starting with SELECT.
2. The output of your query MUST return a flat table with EXACTLY these 10 columns (use aliases to match EXACTLY):
   - "Date" (from dim_date.full_date)
   - "Machine ID" (from dim_machine.machine_code)
   - "Shift" (from dim_shift.shift_name)
   - "Planned Time (min)" (from fact_production.planned_time)
   - "Downtime (min)" (SUM of fact_downtime.duration OR 0 if no downtime)
   - "Total Parts Produced" (from fact_production.total_parts)
   - "Defective Parts" (from fact_production.defective_parts)
   - "Ideal Cycle Time (min/unit)" (from fact_production.ideal_cycle_time)
   - "Error Code" (from dim_reason.error_code OR 'DT-00' if no downtime/reason)
   - "Operator ID" (from dim_operator.operator_code)

3. Join rules: 
   - `fact_production` is the central fact table.
   - Join `dim_machine`, `dim_date`, `dim_shift`, `dim_operator` on their respective keys.
   - `fact_downtime` might have multiple rows per production, or none.
   - You MUST ensure the final granularity is 1 row per downtime event per production run, OR 1 row per healthy production run. 
   - If there is NO downtime, emit one row with "Downtime (min)" = 0 and "Error Code" = 'DT-00'.
   - Use LEFT JOINs for downtime to preserve production records that ran perfectly.

4. Apply the user's natural language filters in the WHERE clause:
   - For string matching (e.g. machine codes, shifts, plants), ALWAYS use case-insensitive matching like `LIKE '%word%'` or `LOWER(column) = LOWER('word')`.
   - Examples of shifts in db: 'Morning', 'Afternoon', 'Night'. If user says 'nightshift', map it to 'Night' via `LOWER(dim_shift.shift_name) LIKE '%night%'`.

==========================================================
DATABASE METADATA
Manufacturing OEE Analytics Database
==========================================================

DATABASE TYPE: SQLite
SCHEMA DESIGN: Star Schema

BUSINESS HIERARCHY
Plant -> Production Line -> Machine -> Production Record -> Downtime Event

TABLES
1. dim_plant (plant_id, plant_name, location)
2. dim_line (line_id, line_name, plant_id)
3. dim_machine (machine_id, machine_code, machine_type, line_id)
4. dim_date (date_key, full_date, day, month, year, quarter)
5. dim_shift (shift_id, shift_name)  # e.g., 'Morning', 'Afternoon', 'Night'
6. dim_operator (operator_id, operator_code)
7. dim_reason (reason_id, error_code)
8. fact_production (production_id, date_key, machine_id, shift_id, operator_id, planned_time, run_time, total_parts, defective_parts, ideal_cycle_time)
9. fact_downtime (downtime_id, production_id, date_key, machine_id, reason_id, shift_id, duration)

RELATIONSHIPS
- fact_production.machine_id -> dim_machine.machine_id
- fact_production.shift_id -> dim_shift.shift_id
- fact_production.operator_id -> dim_operator.operator_id
- fact_production.date_key -> dim_date.date_key
- fact_downtime.production_id -> fact_production.production_id
- fact_downtime.reason_id -> dim_reason.reason_id
- dim_machine.line_id -> dim_line.line_id
- dim_line.plant_id -> dim_plant.plant_id

IMPORTANT BUSINESS RULES
1. Plant information is not stored in the fact tables. Retrieve Plant using: fact_production -> dim_machine -> dim_line -> dim_plant
2. Production metrics come only from fact_production.
3. Downtime metrics come only from fact_downtime.
4. One production record may have multiple downtime events.
5. Generate only ONE SQLite SELECT statement. Never DROP/DELETE/UPDATE.
"""

    def generate_sql(self, query: str, schema_context: str) -> str:
        """
        Calls the LLM to generate a SQL query from natural language.
        """
        if not self.client:
            raise RuntimeError("Groq client is not initialized. Check API keys.")

        logger.info(f"Generating SQL for query: '{query}'")

        user_content = f"DATABASE SCHEMA:\n{schema_context}\n\nUSER QUERY:\n{query}\n\nGenerate the SQLite SELECT query:"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0
            )
            raw_output = response.choices[0].message.content.strip()

            # Clean up markdown formatting if the LLM ignores instructions
            cleaned_sql = re.sub(r"^```sql\s*", "", raw_output, flags=re.IGNORECASE)
            cleaned_sql = re.sub(r"\s*```$", "", cleaned_sql).strip()

            logger.debug(f"Generated SQL: \n{cleaned_sql}")
            return cleaned_sql

        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            raise ValueError(f"LLM Generation failed: {e}")
