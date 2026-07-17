import sqlite3
import logging
from config import DB_FILE_PATH

logger = logging.getLogger(__name__)

class Database:
    """
    Database class acts as a lightweight connection manager to SQLite.
    """
    
    def __init__(self, db_path: str = DB_FILE_PATH):
        """
        Initializes the Database instance.
        
        Args:
            db_path (str): The path to the SQLite database file.
        """
        self.db_path = db_path
        
    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a connection to the SQLite database.
        
        Returns:
            sqlite3.Connection: The database connection object.
        """
        return sqlite3.connect(self.db_path)
