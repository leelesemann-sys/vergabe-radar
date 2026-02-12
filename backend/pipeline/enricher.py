"""Enrichment: Geocoding von PLZ → Koordinaten.

Nutzt die plz_coordinates Tabelle in der DB und Nominatim als Fallback.
"""
import re
import logging
import db

logger = logging.getLogger(__name__)

# PLZ-Regex für deutsche Postleitzahlen
PLZ_RE = re.compile(r"\b(\d{5})\b")


def _load_plz_lookup() -> dict:
    """Lädt PLZ → (lat, lng) Mapping aus der DB."""
    rows = db.fetch_all(
        "SELECT plz, lat, lng FROM plz_coordinates WHERE lat IS NOT NULL"
    )
    return {r[0]: (float(r[1]), float(r[2])) for r in rows}


def _normalize_plz(raw: str | None) -> str | None:
    """Bereinigt PLZ-Strings: '01067.0' → '01067', 'D-50667' → '50667'."""
    if not raw:
        return None
    s = str(raw).strip()
    # Float-Artefakte entfernen
    if "." in s:
        s = s.split(".")[0]
    # Nur Ziffern extrahieren
    digits = re.sub(r"[^\d]", "", s)
    # Auf 5 Stellen auffüllen
    if len(digits) == 4:
        digits = "0" + digits
    if len(digits) == 5:
        return digits
    return None


def geocode_new_records():
    """Geocoded alle search_documents ohne Koordinaten.

    Strategie (3-Level-Fallback):
    1. Exakter PLZ-Match aus plz_coordinates
    2. PLZ-Prefix (erste 3 Stellen)
    3. PLZ aus Beschreibungstext extrahieren
    """
    plz_lookup = _load_plz_lookup()
    logger.info(f"PLZ-Lookup geladen: {len(plz_lookup)} Einträge")

    # Alle Docs ohne Koordinaten
    rows = db.fetch_all("""
        SELECT id, buyer_post_code, buyer_city, description
        FROM search_documents
        WHERE lat IS NULL
    """)

    if not rows:
        logger.info("Keine Dokumente zum Geocoden")
        return 0

    logger.info(f"{len(rows)} Dokumente ohne Koordinaten")

    updated = 0
    engine = db.get_engine()
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    for doc_id, post_code, city, description in rows:
        lat, lng = None, None

        # Level 1: Exakter PLZ-Match
        plz = _normalize_plz(post_code)
        if plz and plz in plz_lookup:
            lat, lng = plz_lookup[plz]

        # Level 2: PLZ-Prefix (erste 3 Stellen → nächste bekannte PLZ)
        if lat is None and plz:
            prefix = plz[:3]
            for known_plz, coords in plz_lookup.items():
                if known_plz.startswith(prefix):
                    lat, lng = coords
                    break

        # Level 3: PLZ aus Description extrahieren
        if lat is None and description:
            matches = PLZ_RE.findall(str(description))
            for m in matches:
                if m in plz_lookup:
                    lat, lng = plz_lookup[m]
                    break

        if lat is not None:
            cursor.execute(
                "UPDATE search_documents SET lat=?, lng=? WHERE id=?",
                lat, lng, doc_id,
            )
            updated += 1

    raw_conn.commit()
    cursor.close()
    raw_conn.close()

    logger.info(f"Geocoding: {updated}/{len(rows)} Dokumente mit Koordinaten versehen")
    return updated
