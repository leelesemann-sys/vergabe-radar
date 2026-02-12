"""Datenquelle: oeffentlichevergabe.de API.

Lädt tägliche CSV-Exporte mit 9 Tabellen pro Tag.
"""
import io
import zipfile
import logging
from datetime import date
import requests
import pandas as pd
import config
from pipeline.base_source import TenderSource

logger = logging.getLogger(__name__)

# CSV-Dateiname → SQL-Tabellenname
TABLE_MAP = {
    "notice": "notices",
    "procedure": "procedures",
    "lot": "lots",
    "purpose": "purposes",
    "classification": "classifications",
    "organisation": "organisations",
    "placeOfPerformance": "places_of_performance",
    "submissionTerms": "submission_terms",
    "tender": "tenders",
}

# Reihenfolge für FK-Abhängigkeiten
IMPORT_ORDER = [
    "notice", "procedure", "lot", "purpose",
    "classification", "organisation", "placeOfPerformance",
    "submissionTerms", "tender",
]


class OeffentlicheVergabeSource(TenderSource):
    """Datenquelle: oeffentlichevergabe.de CSV-Export API."""

    @property
    def name(self) -> str:
        return "oeffentlichevergabe"

    def fetch(self, target_date: date) -> dict[str, pd.DataFrame]:
        """Lädt CSV-Export für einen Tag und gibt DataFrames zurück."""
        date_str = target_date.isoformat()
        url = config.API_BASE_URL
        params = {"pubDay": date_str, "format": "csv.zip"}

        logger.info(f"Download {date_str} von {url}")
        try:
            resp = requests.get(url, params=params, timeout=120)
        except requests.RequestException as e:
            logger.error(f"Download fehlgeschlagen: {e}")
            return {}

        if resp.status_code == 400:
            logger.info(f"Keine Daten für {date_str} (Wochenende/Feiertag)")
            return {}
        if resp.status_code != 200:
            logger.error(f"HTTP {resp.status_code} für {date_str}")
            return {}

        size_mb = len(resp.content) / (1024 * 1024)
        logger.info(f"  {size_mb:.2f} MB heruntergeladen")

        # ZIP entpacken → DataFrames
        result = {}
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            csv_files = {f.replace(".csv", ""): f for f in zf.namelist() if f.endswith(".csv")}
            for csv_name, filename in csv_files.items():
                with zf.open(filename) as f:
                    df = pd.read_csv(f)
                    result[csv_name] = df
                    logger.info(f"  {csv_name}: {len(df)} Zeilen")

        return result

    def get_import_order(self) -> list[str]:
        return IMPORT_ORDER

    def get_table_name(self, csv_name: str) -> str:
        return TABLE_MAP.get(csv_name, csv_name)
