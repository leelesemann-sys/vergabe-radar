import pandas as pd
from sqlalchemy import create_engine, text
import urllib
import json
import config

def get_sql_engine():
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config.SQL_SERVER};DATABASE={config.SQL_DATABASE};UID={config.SQL_USER};PWD={config.SQL_PASSWORD}'
    params = urllib.parse.quote_plus(conn_str)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

def save_search_profile(name, filters_dict):
    """Speichert alle Filter-Einstellungen sicher als JSON."""
    try:
        engine = get_sql_engine()
        json_data = json.dumps(filters_dict)
        query = text("INSERT INTO dbo.user_search_profiles (profile_name, filter_data) VALUES (:name, :data)")
        with engine.begin() as conn:
            conn.execute(query, {"name": name, "data": json_data})
        return True
    except Exception as e:
        return str(e)

def load_saved_profiles():
    """Lädt Profile ohne Caching, damit neue sofort erscheinen."""
    try:
        engine = get_sql_engine()
        return pd.read_sql("SELECT profile_name, filter_data FROM dbo.user_search_profiles ORDER BY created_at DESC", engine)
    except:
        return pd.DataFrame()

def load_cpv_levels(level, parent_code=None):
    """Lädt dynamisch nur Branchen, die auch Treffer in der DB haben."""
    try:
        engine = get_sql_engine()
        if level == 1:
            query = "SELECT DISTINCT h.cpv_2, h.beschreibung_de FROM dbo.vw_cpv_hierarchy h WHERE h.cpv_full LIKE '__000000' AND EXISTS (SELECT 1 FROM dbo.vw_search_index_source src WHERE src.cpv_code LIKE h.cpv_2 + '%') ORDER BY h.cpv_2"
        elif level == 2:
            query = f"SELECT DISTINCT h.cpv_3, h.beschreibung_de FROM dbo.vw_cpv_hierarchy h WHERE h.cpv_2 = '{parent_code}' AND h.cpv_full LIKE '___00000' AND h.cpv_full NOT LIKE '__000000' AND EXISTS (SELECT 1 FROM dbo.vw_search_index_source src WHERE src.cpv_code LIKE h.cpv_3 + '%') ORDER BY h.cpv_3"
        else:
            query = f"SELECT DISTINCT h.cpv_4, h.beschreibung_de FROM dbo.vw_cpv_hierarchy h WHERE h.cpv_3 = '{parent_code}' AND h.cpv_full LIKE '____0000' AND h.cpv_full NOT LIKE '___00000' AND EXISTS (SELECT 1 FROM dbo.vw_search_index_source src WHERE src.cpv_code LIKE h.cpv_4 + '%') ORDER BY h.cpv_4"
        return pd.read_sql(query, engine)
    except:
        return pd.DataFrame()