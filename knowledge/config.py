import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CSV_FILE_PATH = os.path.join(DATA_DIR, "OEE_Manufacturing_Dataset_1000Rows.xlsx")

DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")
DB_FILE_PATH = os.path.join(DATABASE_DIR, "oee.db")

KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "knowledge")
ERROR_CODES_PATH = os.path.join(KNOWLEDGE_DIR, "error_codes.json")

DEBUG_DIR = os.path.join(PROJECT_ROOT, "debug")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
