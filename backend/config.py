"""Zentrale Konfiguration für Vergabe-Radar Backend.

Alle Secrets werden aus Environment-Variablen gelesen.
Siehe .env.example für die benötigten Variablen.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# --- Azure SQL ---
SQL_SERVER = os.environ["VERGABE_SQL_SERVER"]
SQL_DATABASE = os.environ["VERGABE_SQL_DATABASE"]
SQL_USER = os.environ["VERGABE_SQL_USER"]
SQL_PASSWORD = os.environ["VERGABE_SQL_PASSWORD"]

# --- Azure AI Search ---
SEARCH_ENDPOINT = os.environ["VERGABE_SEARCH_ENDPOINT"]
SEARCH_KEY = os.environ["VERGABE_SEARCH_KEY"]
INDEX_NAME = "vergabe-radar-v2"
SEMANTIC_CONFIG = "vergabe-semantic-config"

# --- Azure OpenAI ---
OPENAI_ENDPOINT = os.environ["VERGABE_OPENAI_ENDPOINT"]
OPENAI_KEY = os.environ["VERGABE_OPENAI_KEY"]
OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 256  # Reduziert für Free Tier (50 MB Limit). 1536 bei Upgrade.

# --- Datenquelle ---
API_BASE_URL = "https://oeffentlichevergabe.de/api/notice-exports"
