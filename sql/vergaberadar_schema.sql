-- ============================================================================
-- VergabeRadar Datenbank Schema
-- Relationales Schema basierend auf öffentlichevergabe.de CSV-Export
-- ============================================================================

-- ============================================================================
-- KERN-TABELLEN (Master Data)
-- ============================================================================

-- Haupttabelle: Bekanntmachungen/Notices
CREATE TABLE notices (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    procedure_identifier VARCHAR(100),
    procedure_legal_basis VARCHAR(50),
    form_type VARCHAR(50),
    notice_type VARCHAR(50),  -- 'competition' oder 'result'
    publication_date TIMESTAMP,
    
    PRIMARY KEY (notice_identifier, notice_version),
    INDEX idx_publication_date (publication_date),
    INDEX idx_notice_type (notice_type)
);

-- Verfahren/Procedures
CREATE TABLE procedures (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    cross_border_law VARCHAR(100),
    procedure_type VARCHAR(50),  -- 'open', 'neg-w-call', etc.
    procedure_features TEXT,
    procedure_accelerated BOOLEAN,
    lots_max_allowed INT,
    lots_all_required BOOLEAN,
    lots_max_awarded INT,
    
    PRIMARY KEY (notice_identifier, notice_version),
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);

-- Lose/Lots (einzelne Auftragsteile)
CREATE TABLE lots (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50) NOT NULL,
    
    PRIMARY KEY (notice_identifier, notice_version, lot_identifier),
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);

-- ============================================================================
-- KLASSIFIZIERUNG & KATEGORISIERUNG
-- ============================================================================

-- CPV-Klassifikation (Common Procurement Vocabulary)
CREATE TABLE classifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),  -- NULL = Notice-Level, sonst Lot-Level
    classification_type VARCHAR(20),  -- 'cpv'
    main_classification_code VARCHAR(20),  -- Hauptkategorie (z.B. '72000000' für IT)
    additional_classification_codes TEXT,  -- Comma-separated
    options TEXT,
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_main_cpv (main_classification_code),
    INDEX idx_lot (notice_identifier, notice_version, lot_identifier)
);

-- ============================================================================
-- ORGANISATIONEN
-- ============================================================================

-- Organisationen (Auftraggeber, Bieter, Reviewer)
CREATE TABLE organisations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    organisation_name VARCHAR(500),
    organisation_identifier VARCHAR(200),
    organisation_city VARCHAR(200),
    organisation_post_code VARCHAR(20),
    organisation_country_subdivision VARCHAR(10),  -- NUTS-Code (z.B. DE212)
    organisation_country_code VARCHAR(3),  -- ISO (z.B. DEU)
    organisation_internet_address VARCHAR(500),
    organisation_natural_person BOOLEAN,
    organisation_role VARCHAR(50),  -- 'buyer', 'tenderer', 'reviewer'
    buyer_profile_url VARCHAR(500),
    buyer_legal_type VARCHAR(50),
    buyer_contracting_entity BOOLEAN,
    winner_size VARCHAR(20),  -- 'small', 'medium', 'micro'
    winner_owner_nationality VARCHAR(3),
    winner_listed BOOLEAN,
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_role (organisation_role),
    INDEX idx_region (organisation_country_subdivision),
    INDEX idx_name (organisation_name(255))
);

-- ============================================================================
-- AUSFÜHRUNGSORT & GEOGRAFISCHE DATEN
-- ============================================================================

-- Ausführungsort
CREATE TABLE places_of_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    street VARCHAR(500),
    town VARCHAR(200),
    post_code VARCHAR(20),
    country_subdivision VARCHAR(10),  -- NUTS-Code
    country_code VARCHAR(3),
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_region (country_subdivision),
    INDEX idx_town (town)
);

-- ============================================================================
-- FRISTEN & TERMINE
-- ============================================================================

-- Einreichungsfristen und Termine
CREATE TABLE submission_terms (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    tender_validity_deadline DECIMAL(10,1),
    tender_validity_deadline_unit VARCHAR(20),  -- 'DAY', 'MONTH'
    guarantee_required BOOLEAN,
    public_opening_date TIMESTAMP,
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_opening_date (public_opening_date),
    INDEX idx_lot (notice_identifier, notice_version, lot_identifier)
);

-- ============================================================================
-- ANGEBOTE & VERTRÄGE
-- ============================================================================

-- Angebote/Tenders (nur bei 'result'-Notices)
CREATE TABLE tenders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    tender_identifier VARCHAR(50),
    lot_identifier VARCHAR(50),
    tender_value DECIMAL(15,2),
    tender_value_currency VARCHAR(3),
    tender_payment_value DECIMAL(15,2),
    tender_payment_value_currency VARCHAR(3),
    tender_penalties DECIMAL(15,2),
    tender_penalties_currency VARCHAR(3),
    tender_rank INT,
    concession_revenue_user DECIMAL(15,2),
    concession_revenue_user_currency VARCHAR(3),
    concession_revenue_buyer DECIMAL(15,2),
    concession_revenue_buyer_currency VARCHAR(3),
    country_origin VARCHAR(3),
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_value (tender_value),
    INDEX idx_lot (notice_identifier, notice_version, lot_identifier)
);

-- ============================================================================
-- MATERIALISED VIEWS FÜR VERGABERADAR
-- ============================================================================

-- Suchbare Ausschreibungen (denormalisiert für Performance)
CREATE TABLE searchable_tenders AS
SELECT 
    n.notice_identifier,
    n.notice_version,
    n.notice_type,
    n.publication_date,
    
    -- CPV Codes
    GROUP_CONCAT(DISTINCT c.main_classification_code) as cpv_codes,
    
    -- Auftraggeber
    (SELECT organisation_name 
     FROM organisations 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
       AND organisation_role = 'buyer' 
     LIMIT 1) as buyer_name,
    
    (SELECT organisation_city 
     FROM organisations 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
       AND organisation_role = 'buyer' 
     LIMIT 1) as buyer_city,
     
    (SELECT organisation_country_subdivision 
     FROM organisations 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
       AND organisation_role = 'buyer' 
     LIMIT 1) as buyer_region,
    
    -- Ausführungsort
    (SELECT country_subdivision 
     FROM places_of_performance 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
     LIMIT 1) as performance_region,
    
    -- Deadline
    (SELECT public_opening_date 
     FROM submission_terms 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
     LIMIT 1) as deadline,
    
    -- Budget
    (SELECT SUM(tender_value) 
     FROM tenders 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version) as total_value,
    
    -- Verfahrenstyp
    p.procedure_type

FROM notices n
LEFT JOIN classifications c ON n.notice_identifier = c.notice_identifier 
    AND n.notice_version = c.notice_version
LEFT JOIN procedures p ON n.notice_identifier = p.notice_identifier 
    AND n.notice_version = p.notice_version

WHERE n.notice_type = 'competition'  -- Nur aktive Ausschreibungen
GROUP BY n.notice_identifier, n.notice_version;

-- Indizes für schnelle Suche
CREATE INDEX idx_search_cpv ON searchable_tenders(cpv_codes(100));
CREATE INDEX idx_search_region ON searchable_tenders(buyer_region);
CREATE INDEX idx_search_deadline ON searchable_tenders(deadline);
CREATE INDEX idx_search_publication ON searchable_tenders(publication_date);
CREATE FULLTEXT INDEX idx_search_buyer ON searchable_tenders(buyer_name);

-- ============================================================================
-- WICHTIGE NOTIZEN
-- ============================================================================

/*
FEHLENDE DATEN IN CSV-FORMAT:
- Titel der Ausschreibung (BT-21)
- Beschreibung (BT-24)
- Weitere Textfelder

LÖSUNG: Diese Daten sind in eForms XML oder OCDS JSON verfügbar!

CSV-Format: Strukturierte Daten, gut für Filterung
eForms/OCDS: Vollständige Daten inkl. Texte

EMPFEHLUNG:
1. CSV für Metadaten & Filterung (schnell)
2. eForms/OCDS für Volltext & Details (bei Bedarf)
3. Hybrid-Ansatz: CSV importieren + XML/JSON für Details nachladen
*/

-- ============================================================================
-- BEISPIEL-QUERIES FÜR VERGABERADAR
-- ============================================================================

-- Suche IT-Ausschreibungen (CPV 30, 48, 72, 79) in Berlin
SELECT * FROM searchable_tenders
WHERE cpv_codes REGEXP '(^|,)(30|48|72|79)'
  AND (buyer_region LIKE 'DE3%' OR performance_region LIKE 'DE3%')
  AND deadline > NOW()
ORDER BY publication_date DESC;

-- Top 10 Auftraggeber nach Anzahl Ausschreibungen
SELECT buyer_name, buyer_city, COUNT(*) as tender_count
FROM searchable_tenders
GROUP BY buyer_name, buyer_city
ORDER BY tender_count DESC
LIMIT 10;

-- Durchschnittlicher Auftragswert pro CPV-Kategorie
SELECT 
    SUBSTRING(cpv_codes, 1, 2) as cpv_division,
    COUNT(*) as count,
    AVG(total_value) as avg_value,
    SUM(total_value) as total_value
FROM searchable_tenders
WHERE total_value IS NOT NULL
GROUP BY cpv_division
ORDER BY total_value DESC;
