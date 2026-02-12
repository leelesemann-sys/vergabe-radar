"""CSV-Import nach Azure SQL.

Importiert DataFrames in die normalisierten 9 Tabellen.
Basiert auf der bewährten Logik aus etl/import_to_azure.py.
"""
import logging
import pandas as pd
from decimal import Decimal
import db

logger = logging.getLogger(__name__)


# --- Typ-Konvertierungen (aus import_to_azure.py übernommen) ---

def _s(value, max_len=None):
    """Safe string."""
    if pd.isna(value) or value == "" or value == "NaN":
        return None
    v = str(value).strip()
    return v[:max_len] if max_len and len(v) > max_len else v


def _dec(value):
    """Safe decimal."""
    if pd.isna(value) or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _int(value):
    """Safe int."""
    if pd.isna(value) or value == "":
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _bool(value):
    """Safe bool."""
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def _dt(value):
    """Safe datetime."""
    if pd.isna(value) or value == "":
        return None
    try:
        return pd.to_datetime(value)
    except Exception:
        return None


# --- Tabellen-spezifische Insert-Logik ---

_TABLE_DEFS = {
    "notice": {
        "sql": """INSERT INTO notices (notice_identifier, notice_version, procedure_identifier,
                   procedure_legal_basis, form_type, notice_type, publication_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("procedureIdentifier"), 100), _s(r.get("procedureLegalBasis"), 50),
            _s(r.get("formType"), 50), _s(r.get("noticeType"), 50),
            _dt(r.get("publicationDate")),
        ),
    },
    "procedure": {
        "sql": """INSERT INTO procedures (notice_identifier, notice_version, cross_border_law,
                   procedure_type, procedure_features, procedure_accelerated,
                   lots_max_allowed, lots_all_required, lots_max_awarded)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("crossBorderLaw"), 100), _s(r.get("procedureType"), 50),
            _s(r.get("procedureFeatures")), _bool(r.get("procedureAccelerated")),
            _int(r.get("lotsMaxAllowed")), _bool(r.get("lotsAllRequired")),
            _int(r.get("lotsMaxAwarded")),
        ),
    },
    "lot": {
        "sql": """INSERT INTO lots (notice_identifier, notice_version, lot_identifier)
                   VALUES (?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("lotIdentifier"), 50),
        ),
    },
    "purpose": {
        "sql": """INSERT INTO purposes (notice_identifier, notice_version, lot_identifier,
                   internal_identifier, main_nature, additional_nature,
                   title, estimated_value, estimated_value_currency, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("lotIdentifier"), 50), _s(r.get("internalIdentifier"), 100),
            _s(r.get("mainNature"), 20), _s(r.get("additionalNature"), 50),
            _s(r.get("title")), _dec(r.get("estimatedValue")),
            _s(r.get("estimatedValueCurrency"), 3), _s(r.get("description")),
        ),
    },
    "classification": {
        "sql": """INSERT INTO classifications (notice_identifier, notice_version, lot_identifier,
                   classification_type, main_classification_code,
                   additional_classification_codes, options)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("lotIdentifier"), 50), _s(r.get("classificationType"), 20),
            _s(r.get("mainClassificationCode"), 20),
            _s(r.get("additionalClassificationCodes")), _s(r.get("options")),
        ),
    },
    "organisation": {
        "sql": """INSERT INTO organisations (notice_identifier, notice_version, organisation_name,
                   organisation_identifier, organisation_city, organisation_post_code,
                   organisation_country_subdivision, organisation_country_code,
                   organisation_internet_address, organisation_natural_person,
                   organisation_role, buyer_profile_url, buyer_legal_type,
                   buyer_contracting_entity, winner_size, winner_owner_nationality,
                   winner_listed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("organisationName"), 500), _s(r.get("organisationIdentifier"), 200),
            _s(r.get("organisationCity"), 200), _s(r.get("organisationPostCode"), 20),
            _s(r.get("organisationCountrySubdivision"), 10),
            _s(r.get("organisationCountryCode"), 3),
            _s(r.get("organisationInternetAddress"), 500),
            _bool(r.get("organisationNaturalPerson")),
            _s(r.get("organisationRole"), 50), _s(r.get("buyerProfileURL"), 500),
            _s(r.get("buyerLegalType"), 50), _bool(r.get("buyerContractingEntity")),
            _s(r.get("winnerSize"), 20), _s(r.get("winnerOwnerNationality"), 3),
            _bool(r.get("winnerListed")),
        ),
    },
    "placeOfPerformance": {
        "sql": """INSERT INTO places_of_performance (notice_identifier, notice_version,
                   lot_identifier, street, town, post_code, country_subdivision, country_code)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("lotIdentifier"), 50), _s(r.get("street"), 500),
            _s(r.get("town"), 200), _s(r.get("postCode"), 20),
            _s(r.get("countrySubdivision"), 10), _s(r.get("countryCode"), 3),
        ),
    },
    "submissionTerms": {
        "sql": """INSERT INTO submission_terms (notice_identifier, notice_version, lot_identifier,
                   tender_validity_deadline, tender_validity_deadline_unit,
                   guarantee_required, public_opening_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("lotIdentifier"), 50), _dec(r.get("tenderValidityDeadline")),
            _s(r.get("tenderValidityDeadlineUnit"), 20),
            _bool(r.get("guaranteeRequired")), _dt(r.get("publicOpeningDate")),
        ),
    },
    "tender": {
        "sql": """INSERT INTO tenders (notice_identifier, notice_version, tender_identifier,
                   lot_identifier, tender_value, tender_value_currency,
                   tender_payment_value, tender_payment_value_currency,
                   tender_penalties, tender_penalties_currency, tender_rank,
                   concession_revenue_user, concession_revenue_user_currency,
                   concession_revenue_buyer, concession_revenue_buyer_currency,
                   country_origin)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        "cols": lambda r: (
            _s(r.get("noticeIdentifier"), 100), _s(r.get("noticeVersion"), 10),
            _s(r.get("tenderIdentifier"), 50), _s(r.get("lotIdentifier"), 50),
            _dec(r.get("tenderValue")), _s(r.get("tenderValueCurrency"), 3),
            _dec(r.get("tenderPaymentValue")), _s(r.get("tenderPaymentValueCurrency"), 3),
            _dec(r.get("tenderPenalties")), _s(r.get("tenderPenaltiesCurrency"), 3),
            _int(r.get("tenderRank")),
            _dec(r.get("concessionRevenueUser")), _s(r.get("concessionRevenueUserCurrency"), 3),
            _dec(r.get("concessionRevenueBuyer")), _s(r.get("concessionRevenueBuyerCurrency"), 3),
            _s(r.get("countryOrigin"), 3),
        ),
    },
}


def import_table(csv_name: str, df: pd.DataFrame) -> dict:
    """Importiert einen DataFrame in die entsprechende SQL-Tabelle.

    Returns:
        {"imported": int, "errors": int, "skipped_dupes": int}
    """
    table_def = _TABLE_DEFS.get(csv_name)
    if not table_def:
        logger.warning(f"Keine Definition für Tabelle '{csv_name}'")
        return {"imported": 0, "errors": 0, "skipped_dupes": 0}

    import pyodbc
    engine = db.get_engine()
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    imported = 0
    errors = 0
    dupes = 0

    for _, row in df.iterrows():
        try:
            params = table_def["cols"](row)
            cursor.execute(table_def["sql"], params)
            imported += 1
        except pyodbc.IntegrityError as e:
            if "PRIMARY KEY" in str(e) or "UNIQUE" in str(e):
                dupes += 1
            elif "FOREIGN KEY" in str(e):
                dupes += 1  # Parent nicht vorhanden
            else:
                errors += 1
                if errors <= 3:
                    logger.warning(f"  {csv_name} Integrity: {str(e)[:100]}")
        except Exception as e:
            errors += 1
            if errors <= 3:
                logger.warning(f"  {csv_name} Error: {str(e)[:100]}")

    raw_conn.commit()
    cursor.close()
    raw_conn.close()

    logger.info(f"  {csv_name}: {imported} importiert, {dupes} dupes, {errors} fehler")
    return {"imported": imported, "errors": errors, "skipped_dupes": dupes}


def import_all(data: dict[str, pd.DataFrame], import_order: list[str]) -> dict:
    """Importiert alle Tabellen in FK-Reihenfolge.

    Args:
        data: Dict csv_name → DataFrame (von TenderSource.fetch())
        import_order: Reihenfolge der CSV-Namen

    Returns:
        Dict mit Statistiken pro Tabelle
    """
    stats = {}
    for csv_name in import_order:
        if csv_name in data:
            logger.info(f"Importiere {csv_name} ({len(data[csv_name])} Zeilen)...")
            stats[csv_name] = import_table(csv_name, data[csv_name])
        else:
            logger.info(f"  {csv_name}: nicht vorhanden (optional)")
            stats[csv_name] = {"imported": 0, "errors": 0, "skipped_dupes": 0, "missing": True}
    return stats
