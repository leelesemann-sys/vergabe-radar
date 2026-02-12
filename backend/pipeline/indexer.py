"""Azure AI Search Index: Erstellen und Befüllen.

Erstellt den vergabe-radar-v2 Index mit Vector + Keyword + Semantic Config
und pusht Dokumente mit Embeddings hinein.
"""
import json
import logging
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)
import config
import db

logger = logging.getLogger(__name__)


def create_index():
    """Erstellt den vergabe-radar-v2 Index (idempotent)."""
    client = SearchIndexClient(
        endpoint=config.SEARCH_ENDPOINT,
        credential=AzureKeyCredential(config.SEARCH_KEY),
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="de.microsoft"),
        SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="de.microsoft"),
        SearchableField(name="buyer_name", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="buyer_city", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="cpv_code_main", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="contract_nature", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="publication_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SimpleField(name="deadline", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SimpleField(name="estimated_value", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="document_url", type=SearchFieldDataType.String),
        SimpleField(name="procedure_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="geo_location", type=SearchFieldDataType.GeographyPoint, filterable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=config.OPENAI_EMBEDDING_DIMENSIONS,
            vector_search_profile_name="vergabe-vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="vergabe-hnsw"),
        ],
        profiles=[
            VectorSearchProfile(
                name="vergabe-vector-profile",
                algorithm_configuration_name="vergabe-hnsw",
            ),
        ],
    )

    semantic_config = SemanticConfiguration(
        name=config.SEMANTIC_CONFIG,
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="description")],
            keywords_fields=[
                SemanticField(field_name="cpv_code_main"),
                SemanticField(field_name="buyer_name"),
            ],
        ),
    )

    index = SearchIndex(
        name=config.INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=SemanticSearch(configurations=[semantic_config]),
    )

    result = client.create_or_update_index(index)
    logger.info(f"Index '{result.name}' erstellt/aktualisiert")
    return result


def _format_doc(doc: dict) -> dict:
    """Formatiert ein Dokument für den Azure Search Upload."""
    search_doc = {
        "id": doc["id"],
        "title": doc.get("title"),
        "description": doc.get("description"),
        "buyer_name": doc.get("buyer_name"),
        "buyer_city": doc.get("buyer_city"),
        "cpv_code_main": doc.get("cpv_code_main"),
        "contract_nature": doc.get("contract_nature"),
        "document_url": doc.get("document_url"),
        "procedure_type": doc.get("procedure_type"),
        "content_vector": doc.get("content_vector"),
    }

    # Datum formatieren (ISO 8601)
    for date_field in ("publication_date", "deadline"):
        val = doc.get(date_field)
        if val is not None:
            if isinstance(val, datetime):
                search_doc[date_field] = val.isoformat() + "Z"
            elif isinstance(val, str) and val:
                search_doc[date_field] = val
            else:
                search_doc[date_field] = None
        else:
            search_doc[date_field] = None

    # Estimated Value
    ev = doc.get("estimated_value")
    search_doc["estimated_value"] = float(ev) if ev is not None else None

    # Geo Location (GeoJSON Point)
    lat = doc.get("lat")
    lng = doc.get("lng")
    if lat is not None and lng is not None:
        try:
            lat_f, lng_f = float(lat), float(lng)
            if -90 <= lat_f <= 90 and -180 <= lng_f <= 180:
                search_doc["geo_location"] = {
                    "type": "Point",
                    "coordinates": [lng_f, lat_f],
                }
        except (ValueError, TypeError):
            pass

    return search_doc


def upload_documents(docs: list[dict], batch_size: int = 500) -> int:
    """Pusht Dokumente nach Azure AI Search.

    Args:
        docs: Liste von Dokumenten (aus embedder.embed_and_collect)
        batch_size: Dokumente pro Upload-Batch

    Returns:
        Anzahl erfolgreich hochgeladener Dokumente
    """
    client = SearchClient(
        endpoint=config.SEARCH_ENDPOINT,
        index_name=config.INDEX_NAME,
        credential=AzureKeyCredential(config.SEARCH_KEY),
    )

    total = 0
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        formatted = [_format_doc(d) for d in batch]

        try:
            result = client.upload_documents(documents=formatted)
            succeeded = sum(1 for r in result if r.succeeded)
            failed = sum(1 for r in result if not r.succeeded)
            total += succeeded
            if failed > 0:
                logger.warning(f"Batch {i}: {failed} fehlgeschlagen")
                for r in result:
                    if not r.succeeded:
                        logger.warning(f"  Doc {r.key}: {r.error_message}")
                        break  # Nur ersten Fehler loggen
        except Exception as e:
            logger.error(f"Upload-Fehler bei Batch {i}: {e}")

    logger.info(f"Search Index: {total}/{len(docs)} Dokumente hochgeladen")
    return total


def mark_indexed(doc_ids: list[str]):
    """Markiert Dokumente als erfolgreich indexiert."""
    engine = db.get_engine()
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    for doc_id in doc_ids:
        cursor.execute(
            "UPDATE search_documents SET indexed_at = GETDATE() WHERE id = ?",
            doc_id,
        )

    raw_conn.commit()
    cursor.close()
    raw_conn.close()
