# Vergabe-Radar

Automatisierte Erfassung, Aufbereitung und semantische Suche deutscher oeffentlicher Ausschreibungen.

Vergabe-Radar aggregiert taeglich Bekanntmachungen von oeffentlichevergabe.de, normalisiert die Daten in einer relationalen Datenbank, reichert sie mit Geokoordinaten an und macht sie ueber Hybrid Search (Vektor + Keyword + Semantic Ranking) praezise durchsuchbar.

## Was dieses Projekt leistet

**Datenerfassung** -- Vollautomatischer Download der taeglichen CSV-Exporte (~300 Ausschreibungen/Tag, 19 Tabellen) ueber die offizielle API. Erweiterbare Architektur fuer zusaetzliche Quellen (TED/EU, Bund.de).

**Normalisierung** -- Import in 9 sauber normalisierte SQL-Tabellen (Notices, Procedures, Lots, Purposes, Classifications, Organisations, Places, Submission Terms, Tenders) mit Duplikat- und FK-Handling.

**Denormalisierung** -- Aufbau einer optimierten Suchtabelle aus den normalisierten Daten. Jede Ausschreibung wird zu einem flachen Dokument mit allen relevanten Feldern zusammengefuehrt.

**Geocoding** -- 3-stufiger Fallback (exakte PLZ, PLZ-Prefix, Regex-Extraktion aus Beschreibungstext) gegen 8.300+ deutsche Postleitzahlen. Ermoeglicht Umkreissuche.

**Embedding** -- Generierung semantischer Vektoren (text-embedding-3-small, 256 Dimensionen) fuer jede Ausschreibung. Der Embedding-Text kombiniert Titel, Beschreibung, Auftraggeber, Ort, CPV-Code und Vertragsart.

**Hybrid Search** -- Azure AI Search Index mit drei Suchebenen:
- **Vektor-Suche** (HNSW, Cosine Similarity) -- findet semantisch aehnliche Ausschreibungen auch ohne exakte Keyword-Treffer
- **Keyword-Suche** (BM25, de.microsoft Analyzer) -- praezise Volltextsuche mit deutscher Sprachanalyse
- **Semantic Ranking** -- KI-basiertes Re-Ranking der Ergebnisse fuer optimale Relevanz

## Architektur

```
oeffentlichevergabe.de API
         |
    [Download CSV.zip]
         |
    [Import -> Azure SQL]        9 normalisierte Tabellen
         |
    [Denormalisierung]           -> search_documents
         |
    [Geocoding]                  PLZ -> lat/lng
         |
    [Embedding]                  Azure OpenAI text-embedding-3-small
         |
    [Indexing]                   -> Azure AI Search (vergabe-radar-v2)
         |
    [Hybrid Search API]          Vector + BM25 + Semantic
```

## Quickstart

```bash
cd backend

# 1. Environment einrichten
cp .env.example .env
# .env mit Azure-Credentials ausfuellen

# 2. Dependencies installieren
pip install python-dotenv sqlalchemy pyodbc pandas requests openai azure-search-documents

# 3. Search Index erstellen (einmalig)
python run_pipeline.py --create-index

# 4. Pipeline fuer einen Tag ausfuehren
python run_pipeline.py --date 2025-12-30

# 5. Backfill fuer einen Zeitraum
python run_pipeline.py --backfill 2025-01-01 2025-12-31

# 6. Taeglicher Lauf (Default: gestern)
python run_pipeline.py
```

## Projektstruktur

```
backend/
  config.py                  Zentrale Konfiguration (env-vars)
  db.py                      SQLAlchemy Connection Helper
  run_pipeline.py            Pipeline-Orchestrierung
  app.py                     Streamlit Frontend (Prototyp)
  pipeline/
    base_source.py           Abstrakte Datenquelle (erweiterbar)
    oeffentlichevergabe.py   Konkrete Quelle: oeffentlichevergabe.de
    importer.py              CSV -> 9 SQL-Tabellen
    denormalizer.py          SQL -> search_documents
    enricher.py              PLZ-Geocoding
    embedder.py              Azure OpenAI Embeddings
    indexer.py               Azure AI Search Push
sql/                         Datenbank-Schema
frontend/                    HTML/React Prototypen
docs/                        Dokumentation
```

## Azure-Ressourcen

| Dienst | Zweck | Tier |
|--------|-------|------|
| Azure SQL Database | Normalisierte Datenhaltung | Serverless Gen5 |
| Azure AI Search | Hybrid Search Index | Free |
| Azure OpenAI | Embedding-Generierung | text-embedding-3-small |

## Erweiterbarkeit

Neue Datenquellen werden als Subklasse von `TenderSource` implementiert:

```python
class MeineQuelle(TenderSource):
    @property
    def name(self) -> str:
        return "meine-quelle"

    def fetch(self, target_date: date) -> dict[str, pd.DataFrame]:
        # Daten holen und als DataFrames zurueckgeben
        ...

    def get_import_order(self) -> list[str]:
        return ["notice", "procedure", "lot", ...]
```

## Lizenz

MIT
