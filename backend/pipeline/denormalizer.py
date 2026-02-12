"""Denormalisierung: 9 normalisierte Tabellen → search_documents.

Baut die flache Suchtabelle aus den normalisierten Tabellen auf.
Nur neue Notices die noch nicht in search_documents sind werden verarbeitet.
"""
import hashlib
import logging
import db

logger = logging.getLogger(__name__)


def _build_embedding_text(title, description, buyer_name, buyer_city, cpv, nature):
    """Baut den Text der embedded wird."""
    parts = []
    if title:
        parts.append(f"Ausschreibung: {title}")
    if description:
        # Beschreibung auf ~2000 Zeichen kürzen für Embedding
        desc = description[:2000]
        parts.append(f"Beschreibung: {desc}")
    if buyer_name:
        parts.append(f"Auftraggeber: {buyer_name}")
    if buyer_city:
        parts.append(f"Ort: {buyer_city}")
    if cpv:
        parts.append(f"CPV: {cpv}")
    if nature:
        parts.append(f"Art: {nature}")
    return "\n".join(parts)


def refresh():
    """Füllt search_documents mit neuen Notices aus den normalisierten Tabellen.

    Nur Notices mit notice_type='competition' und die noch nicht in search_documents sind.
    """
    # Neue Notices finden die noch nicht denormalisiert wurden
    count_before = db.fetch_all("SELECT COUNT(*) FROM search_documents")[0][0]

    db.execute("""
        INSERT INTO search_documents (
            id, notice_identifier, notice_version, title, description,
            buyer_name, buyer_city, buyer_post_code, contract_nature,
            publication_date, deadline, estimated_value, document_url,
            cpv_code_main, all_cpv_codes, procedure_type,
            embedding_text, embedding_hash, updated_at
        )
        SELECT
            CONCAT(n.notice_identifier, '-', n.notice_version) AS id,
            n.notice_identifier,
            n.notice_version,
            p.title,
            p.description,
            o.organisation_name AS buyer_name,
            o.organisation_city AS buyer_city,
            o.organisation_post_code AS buyer_post_code,
            p.main_nature AS contract_nature,
            n.publication_date,
            st.public_opening_date AS deadline,
            p.estimated_value,
            CONCAT('https://oeffentlichevergabe.de/ui/de/tender/', n.notice_identifier) AS document_url,
            c.main_classification_code AS cpv_code_main,
            c.additional_classification_codes AS all_cpv_codes,
            pr.procedure_type,
            -- Embedding text: wird in Python nachbearbeitet
            NULL AS embedding_text,
            NULL AS embedding_hash,
            GETDATE() AS updated_at
        FROM notices n
        -- Purpose: Notice-Level (lot_identifier IS NULL) bevorzugt
        OUTER APPLY (
            SELECT TOP 1 title, description, main_nature, estimated_value
            FROM purposes
            WHERE notice_identifier = n.notice_identifier
              AND notice_version = n.notice_version
            ORDER BY CASE WHEN lot_identifier IS NULL THEN 0 ELSE 1 END
        ) p
        -- Buyer Organisation
        OUTER APPLY (
            SELECT TOP 1 organisation_name, organisation_city, organisation_post_code
            FROM organisations
            WHERE notice_identifier = n.notice_identifier
              AND notice_version = n.notice_version
              AND organisation_role = 'buyer'
        ) o
        -- Haupt-CPV Code
        OUTER APPLY (
            SELECT TOP 1 main_classification_code, additional_classification_codes
            FROM classifications
            WHERE notice_identifier = n.notice_identifier
              AND notice_version = n.notice_version
            ORDER BY CASE WHEN lot_identifier IS NULL THEN 0 ELSE 1 END
        ) c
        -- Deadline
        OUTER APPLY (
            SELECT TOP 1 public_opening_date
            FROM submission_terms
            WHERE notice_identifier = n.notice_identifier
              AND notice_version = n.notice_version
        ) st
        -- Procedure Type
        LEFT JOIN procedures pr
            ON pr.notice_identifier = n.notice_identifier
            AND pr.notice_version = n.notice_version
        WHERE n.notice_type LIKE 'cn-%'
          AND NOT EXISTS (
              SELECT 1 FROM search_documents sd
              WHERE sd.id = CONCAT(n.notice_identifier, '-', n.notice_version)
          )
    """)

    count_after = db.fetch_all("SELECT COUNT(*) FROM search_documents")[0][0]
    new_docs = count_after - count_before
    logger.info(f"Denormalisierung: {new_docs} neue Dokumente (gesamt: {count_after})")

    # Embedding-Text in Python aufbauen (flexibler als in SQL)
    if new_docs > 0:
        _update_embedding_texts()

    return new_docs


def _update_embedding_texts():
    """Baut embedding_text + embedding_hash für Dokumente wo es noch fehlt."""
    rows = db.fetch_all("""
        SELECT id, title, description, buyer_name, buyer_city, cpv_code_main, contract_nature
        FROM search_documents
        WHERE embedding_text IS NULL
    """)

    if not rows:
        return

    engine = db.get_engine()
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()

    for doc_id, title, desc, buyer, city, cpv, nature in rows:
        emb_text = _build_embedding_text(title, desc, buyer, city, cpv, nature)
        emb_hash = hashlib.sha256(emb_text.encode("utf-8")).hexdigest()
        cursor.execute(
            "UPDATE search_documents SET embedding_text=?, embedding_hash=? WHERE id=?",
            emb_text, emb_hash, doc_id,
        )

    raw_conn.commit()
    cursor.close()
    raw_conn.close()
    logger.info(f"Embedding-Text für {len(rows)} Dokumente aufgebaut")
