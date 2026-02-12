"""Database connection helper für Azure SQL."""
import urllib
from sqlalchemy import create_engine, text
import config

_engine = None


def get_engine():
    """Erstellt oder gibt gecachte SQLAlchemy Engine zurück."""
    global _engine
    if _engine is None:
        odbc_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={config.SQL_SERVER};"
            f"DATABASE={config.SQL_DATABASE};"
            f"UID={config.SQL_USER};"
            f"PWD={config.SQL_PASSWORD};"
            f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30"
        )
        params = urllib.parse.quote_plus(odbc_str)
        _engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={params}",
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine


def execute(query, params=None):
    """Führt ein DML/DDL Statement aus (INSERT, UPDATE, CREATE, etc.)."""
    engine = get_engine()
    with engine.begin() as conn:
        return conn.execute(text(query), params or {})


def fetch_all(query, params=None):
    """Führt SELECT aus und gibt Liste von Rows zurück."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchall()


def fetch_df(query, params=None):
    """Führt SELECT aus und gibt pandas DataFrame zurück."""
    import pandas as pd
    engine = get_engine()
    return pd.read_sql(text(query), engine, params=params)
