"""Abstrakte Basisklasse für Tender-Datenquellen.

Neue Quellen (TED, Bund.de, etc.) implementieren diese Klasse.
"""
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
import pandas as pd


class TenderSource(ABC):
    """Interface für eine Ausschreibungs-Datenquelle."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Eindeutiger Name der Quelle (z.B. 'oeffentlichevergabe')."""

    @abstractmethod
    def fetch(self, target_date: date) -> dict[str, pd.DataFrame]:
        """Lädt Daten für einen Tag herunter.

        Returns:
            Dict mit Tabellennamen → DataFrame, z.B.:
            {'notice': df_notices, 'purpose': df_purposes, ...}
            Leeres Dict wenn keine Daten verfügbar (Wochenende etc.)
        """

    @abstractmethod
    def get_import_order(self) -> list[str]:
        """Reihenfolge der Tabellen für den Import (FK-Abhängigkeiten)."""
