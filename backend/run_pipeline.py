"""Vergabe-Radar Ingest Pipeline: Orchestrierung.

Führt die gesamte Pipeline aus:
  1. Download: CSV-Export von oeffentlichevergabe.de
  2. Import: CSV → Azure SQL (9 normalisierte Tabellen)
  3. Enrichment: Geocoding (PLZ → Koordinaten)
  4. Denormalisierung: SQL → search_documents
  5. Embedding: Azure OpenAI text-embedding-3-small
  6. Indexing: Push nach Azure AI Search (vergabe-radar-v2)

Usage:
  python run_pipeline.py                        # Gestern
  python run_pipeline.py --date 2025-12-30      # Bestimmter Tag
  python run_pipeline.py --create-index         # Nur Index erstellen
  python run_pipeline.py --backfill 2025-01-01 2025-01-31  # Datumsbereich
"""
import argparse
import logging
import sys
from datetime import date, datetime, timedelta

# Pipeline-Module
from pipeline.oeffentlichevergabe import OeffentlicheVergabeSource
from pipeline import importer, enricher, denormalizer, embedder, indexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_daily(target_date: date) -> dict:
    """Führt die Pipeline für einen Tag aus.

    Returns:
        Dict mit Statistiken
    """
    logger.info(f"=== Pipeline Start: {target_date} ===")
    stats = {"date": target_date.isoformat()}

    # 1. Download
    logger.info("--- Schritt 1: Download ---")
    source = OeffentlicheVergabeSource()
    data = source.fetch(target_date)

    if not data:
        logger.info(f"Keine Daten für {target_date} (Wochenende/Feiertag?)")
        stats["status"] = "no_data"
        return stats

    stats["download"] = {name: len(df) for name, df in data.items()}

    # 2. Import nach SQL
    logger.info("--- Schritt 2: Import nach SQL ---")
    import_stats = importer.import_all(data, source.get_import_order())
    stats["import"] = import_stats

    # 3. Denormalisierung → search_documents
    logger.info("--- Schritt 3: Denormalisierung ---")
    new_docs = denormalizer.refresh()
    stats["denormalized"] = new_docs

    # 4. Geocoding
    logger.info("--- Schritt 4: Geocoding ---")
    geocoded = enricher.geocode_new_records()
    stats["geocoded"] = geocoded

    # 5. Embedding + Indexing
    logger.info("--- Schritt 5: Embedding + Indexing ---")
    docs_with_vectors = embedder.embed_and_collect()
    stats["embedded"] = len(docs_with_vectors)

    if docs_with_vectors:
        # 6. Push to Azure AI Search
        logger.info("--- Schritt 6: Push to Search ---")
        indexed = indexer.upload_documents(docs_with_vectors)
        stats["indexed"] = indexed

        # Dokumente als indexiert markieren
        indexed_ids = [d["id"] for d in docs_with_vectors]
        indexer.mark_indexed(indexed_ids)
    else:
        stats["indexed"] = 0

    stats["status"] = "ok"
    logger.info(f"=== Pipeline fertig: {target_date} ===")
    _print_summary(stats)
    return stats


def run_backfill(start_date: date, end_date: date):
    """Führt die Pipeline für einen Datumsbereich aus."""
    logger.info(f"=== Backfill: {start_date} bis {end_date} ===")
    current = start_date
    results = []

    while current <= end_date:
        try:
            stats = run_daily(current)
            results.append(stats)
        except Exception as e:
            logger.error(f"Fehler bei {current}: {e}")
            results.append({"date": current.isoformat(), "status": "error", "error": str(e)})

        current += timedelta(days=1)

    # Zusammenfassung
    ok = sum(1 for r in results if r.get("status") == "ok")
    no_data = sum(1 for r in results if r.get("status") == "no_data")
    errors = sum(1 for r in results if r.get("status") == "error")
    logger.info(f"=== Backfill fertig: {ok} OK, {no_data} keine Daten, {errors} Fehler ===")


def _print_summary(stats: dict):
    """Gibt eine kompakte Zusammenfassung aus."""
    if stats.get("status") == "no_data":
        return

    dl = stats.get("download", {})
    total_rows = sum(dl.values())
    imp = stats.get("import", {})
    total_imported = sum(v.get("imported", 0) for v in imp.values() if isinstance(v, dict))

    logger.info(f"  Download:   {total_rows} Zeilen in {len(dl)} Tabellen")
    logger.info(f"  Importiert: {total_imported} Zeilen nach SQL")
    logger.info(f"  Denormalisiert: {stats.get('denormalized', 0)} neue Dokumente")
    logger.info(f"  Geocoded:   {stats.get('geocoded', 0)}")
    logger.info(f"  Embedded:   {stats.get('embedded', 0)}")
    logger.info(f"  Indexiert:  {stats.get('indexed', 0)}")


def main():
    parser = argparse.ArgumentParser(description="Vergabe-Radar Ingest Pipeline")
    parser.add_argument("--date", type=str, help="Datum im Format YYYY-MM-DD (Default: gestern)")
    parser.add_argument("--create-index", action="store_true", help="Nur Search Index erstellen")
    parser.add_argument("--backfill", nargs=2, metavar=("START", "END"),
                        help="Backfill für Datumsbereich START END (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.create_index:
        logger.info("Erstelle Azure AI Search Index...")
        indexer.create_index()
        logger.info("Index erstellt!")
        return

    if args.backfill:
        start = datetime.strptime(args.backfill[0], "%Y-%m-%d").date()
        end = datetime.strptime(args.backfill[1], "%Y-%m-%d").date()
        run_backfill(start, end)
        return

    # Einzelner Tag
    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target = date.today() - timedelta(days=1)

    run_daily(target)


if __name__ == "__main__":
    main()
