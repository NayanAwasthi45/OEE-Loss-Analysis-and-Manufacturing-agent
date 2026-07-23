import sqlite3
import logging

logger = logging.getLogger(__name__)

class SchemaLoader:
    """
    Loads and formats the database schema for the LLM prompt.
    Extracts tables, columns, types, and primary/foreign keys dynamically from SQLite.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_schema_context(self) -> str:
        """
        Connects to the SQLite database and returns a formatted string
        describing the schema (tables and columns) for LLM consumption.
        """
        logger.info(f"Loading database schema from {self.db_path}")
        schema_text = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Get all tables
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                for table_name, table_sql in tables:
                    # Skip internal sqlite tables
                    if table_name.startswith("sqlite_"):
                        continue
                    
                    schema_text.append(f"Table: {table_name}")
                    
                    # Optional: We can just use the raw CREATE TABLE sql which is great for LLMs
                    # because it contains PK/FK constraints explicitly.
                    if table_sql:
                        # Clean up formatting slightly
                        clean_sql = "  " + table_sql.replace("\n", "\n  ")
                        schema_text.append(clean_sql)
                    schema_text.append("")

                # Fetch unique values for key mapping
                schema_text.append("==========================================================")
                schema_text.append("UNIQUE VALUES FOR ENTITY RESOLUTION")
                schema_text.append("Use these exact string values when applying WHERE filters.")
                
                try:
                    cursor.execute("SELECT DISTINCT plant_name FROM dim_plant")
                    plants = [row[0] for row in cursor.fetchall() if row[0]]
                    schema_text.append(f"dim_plant.plant_name values: {plants}")
                except Exception:
                    pass
                
                try:
                    cursor.execute("SELECT DISTINCT machine_code FROM dim_machine")
                    machines = [row[0] for row in cursor.fetchall() if row[0]]
                    schema_text.append(f"dim_machine.machine_code values: {machines}")
                except Exception:
                    pass
                
                try:
                    cursor.execute("SELECT DISTINCT shift_name FROM dim_shift")
                    shifts = [row[0] for row in cursor.fetchall() if row[0]]
                    schema_text.append(f"dim_shift.shift_name values: {shifts}")
                except Exception:
                    pass

            return "\n".join(schema_text)

        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise
