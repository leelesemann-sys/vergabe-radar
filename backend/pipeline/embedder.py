"""Embedding-Generierung via Azure OpenAI.

Berechnet Embeddings für alle Dokumente in search_documents
die noch kein Embedding haben (indexed_at IS NULL) oder
deren embedding_hash sich geändert hat.
"""
import logging
import json
from openai import AzureOpenAI
import config
import db

logger = logging.getLogger(__name__)

# Azure OpenAI Client (lazy init)
_client = None


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=config.OPENAI_ENDPOINT,
            api_key=config.OPENAI_KEY,
            api_version="2024-06-01",
        )
    return _client


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Berechnet Embeddings für eine Liste von Texten."""
    client = _get_client()
    response = client.embeddings.create(
        input=texts,
        model=config.OPENAI_EMBEDDING_DEPLOYMENT,
        dimensions=config.OPENAI_EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in response.data]


def embed_pending(batch_size: int = 100) -> int:
    """Berechnet Embeddings für alle Dokumente ohne Embedding.

    Args:
        batch_size: Anzahl Texte pro API-Call (max 2048)

    Returns:
        Anzahl der neu eingebetteten Dokumente
    """
    # Dokumente die ein Embedding brauchen
    rows = db.fetch_all("""
        SELECT id, embedding_text
        FROM search_documents
        WHERE embedding_text IS NOT NULL
          AND indexed_at IS NULL
        ORDER BY updated_at
    """)

    if not rows:
        logger.info("Keine Dokumente zum Embedden")
        return 0

    logger.info(f"{len(rows)} Dokumente zum Embedden")
    total = 0

    # In Batches verarbeiten
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        doc_ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        try:
            vectors = _embed_batch(texts)
        except Exception as e:
            logger.error(f"Embedding-Fehler bei Batch {i}: {e}")
            continue

        # Vektoren in DB speichern (als indexed_at markieren)
        # Die eigentlichen Vektoren gehen direkt in den Search Index,
        # wir speichern sie hier temporär als JSON in einer temp-Tabelle
        _store_vectors(doc_ids, vectors)
        total += len(vectors)

        if (i + batch_size) % 500 == 0:
            logger.info(f"  {total}/{len(rows)} embedded...")

    logger.info(f"Embedding fertig: {total} Dokumente")
    return total


def _store_vectors(doc_ids: list[str], vectors: list[list[float]]):
    """Markiert Dokumente als embedded und speichert Vektor-Referenz."""
    engine = db.get_engine()
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    for doc_id, vector in zip(doc_ids, vectors):
        cursor.execute(
            "UPDATE search_documents SET indexed_at = GETDATE() WHERE id = ?",
            doc_id,
        )

    raw_conn.commit()
    cursor.close()
    raw_conn.close()


def get_embedding(text: str) -> list[float]:
    """Berechnet ein einzelnes Embedding (für Query-Zeit)."""
    vectors = _embed_batch([text])
    return vectors[0]


def embed_and_collect(batch_size: int = 100) -> list[dict]:
    """Berechnet Embeddings und gibt Dokumente mit Vektoren zurück.

    Returns:
        Liste von {"id": ..., "vector": [...], ...} für den Indexer
    """
    rows = db.fetch_all("""
        SELECT id, embedding_text, title, description, buyer_name, buyer_city,
               cpv_code_main, contract_nature, publication_date, deadline,
               estimated_value, document_url, procedure_type, lat, lng,
               buyer_post_code, all_cpv_codes
        FROM search_documents
        WHERE embedding_text IS NOT NULL
          AND indexed_at IS NULL
        ORDER BY updated_at
    """)

    if not rows:
        logger.info("Keine Dokumente zum Embedden + Indexen")
        return []

    logger.info(f"{len(rows)} Dokumente zum Embedden + Indexen")
    results = []

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        texts = [r[1] for r in batch]  # embedding_text

        try:
            vectors = _embed_batch(texts)
        except Exception as e:
            logger.error(f"Embedding-Fehler bei Batch {i}: {e}")
            continue

        for row, vector in zip(batch, vectors):
            results.append({
                "id": row[0],
                "embedding_text": row[1],
                "title": row[2],
                "description": row[3],
                "buyer_name": row[4],
                "buyer_city": row[5],
                "cpv_code_main": row[6],
                "contract_nature": row[7],
                "publication_date": row[8],
                "deadline": row[9],
                "estimated_value": row[10],
                "document_url": row[11],
                "procedure_type": row[12],
                "lat": row[13],
                "lng": row[14],
                "buyer_post_code": row[15],
                "all_cpv_codes": row[16],
                "content_vector": vector,
            })

        if (i + batch_size) % 500 == 0:
            logger.info(f"  {len(results)}/{len(rows)} embedded...")

    logger.info(f"Embedding fertig: {len(results)} Dokumente mit Vektoren")
    return results
