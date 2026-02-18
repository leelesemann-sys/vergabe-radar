# Vergabe-Radar

> **Language:** English | [Deutsch](README.de.md)

Automated collection, processing, and semantic search of German public procurement notices (Ausschreibungen).

Vergabe-Radar aggregates daily notices from oeffentlichevergabe.de, normalizes the data in a relational database, enriches them with geocoordinates, and makes them precisely searchable via Hybrid Search (Vector + Keyword + Semantic Ranking).

## What This Project Does

**Data Collection** -- Fully automated download of daily CSV exports (~300 notices/day, 19 tables) via the official API. Extensible architecture for additional sources (TED/EU, Bund.de).

**Normalization** -- Import into 9 cleanly normalized SQL tables (Notices, Procedures, Lots, Purposes, Classifications, Organisations, Places, Submission Terms, Tenders) with duplicate and FK handling.

**Denormalization** -- Construction of an optimized search table from the normalized data. Each Ausschreibung (procurement notice) is merged into a flat document with all relevant fields.

**Geocoding** -- 3-level fallback (exact postal code, postal code prefix, regex extraction from description text) against 8,300+ German postal codes. Enables radius search.

**Embedding** -- Generation of semantic vectors (text-embedding-3-small, 256 dimensions) for each Ausschreibung. The embedding text combines title, description, contracting authority, location, CPV code, and contract type.

**Hybrid Search** -- Azure AI Search index with three search layers:
- **Vector Search** (HNSW, Cosine Similarity) -- finds semantically similar Ausschreibungen even without exact keyword matches
- **Keyword Search** (BM25, de.microsoft Analyzer) -- precise full-text search with German language analysis
- **Semantic Ranking** -- AI-based re-ranking of results for optimal relevance

## Architecture

```
oeffentlichevergabe.de API
         |
    [Download CSV.zip]
         |
    [Import -> Azure SQL]        9 normalized tables
         |
    [Denormalization]            -> search_documents
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

# 1. Set up environment
cp .env.example .env
# Fill .env with Azure credentials

# 2. Install dependencies
pip install python-dotenv sqlalchemy pyodbc pandas requests openai azure-search-documents

# 3. Create search index (one-time)
python run_pipeline.py --create-index

# 4. Run pipeline for a single day
python run_pipeline.py --date 2025-12-30

# 5. Backfill for a date range
python run_pipeline.py --backfill 2025-01-01 2025-12-31

# 6. Daily run (default: yesterday)
python run_pipeline.py
```

## Project Structure

```
backend/
  config.py                  Central configuration (env-vars)
  db.py                      SQLAlchemy connection helper
  run_pipeline.py            Pipeline orchestration
  app.py                     Streamlit frontend (prototype)
  pipeline/
    base_source.py           Abstract data source (extensible)
    oeffentlichevergabe.py   Concrete source: oeffentlichevergabe.de
    importer.py              CSV -> 9 SQL tables
    denormalizer.py          SQL -> search_documents
    enricher.py              PLZ geocoding
    embedder.py              Azure OpenAI embeddings
    indexer.py               Azure AI Search push
sql/                         Database schema
frontend/                    HTML/React prototypes
docs/                        Documentation
```

## Azure Resources

| Service | Purpose | Tier |
|---------|---------|------|
| Azure SQL Database | Normalized data storage | Serverless Gen5 |
| Azure AI Search | Hybrid search index | Free |
| Azure OpenAI | Embedding generation | text-embedding-3-small |

## Extensibility

New data sources are implemented as subclasses of `TenderSource`:

```python
class MySource(TenderSource):
    @property
    def name(self) -> str:
        return "my-source"

    def fetch(self, target_date: date) -> dict[str, pd.DataFrame]:
        # Fetch data and return as DataFrames
        ...

    def get_import_order(self) -> list[str]:
        return ["notice", "procedure", "lot", ...]
```

## License

MIT
