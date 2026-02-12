-- ============================================================================
-- VergabeRadar Datenbank Schema - VOLLSTÄNDIG MIT PURPOSE
-- ============================================================================

-- ============================================================================
-- 🎉 BREAKING NEWS: purpose.csv enthält TITEL & BESCHREIBUNG!
-- Wir brauchen KEIN OCDS oder eForms mehr - alles ist in CSV!
-- ============================================================================

-- ============================================================================
-- KERN-TABELLEN
-- ============================================================================

CREATE TABLE notices (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    procedure_identifier VARCHAR(100),
    procedure_legal_basis VARCHAR(50),
    form_type VARCHAR(50),
    notice_type VARCHAR(50),
    publication_date TIMESTAMP,
    
    PRIMARY KEY (notice_identifier, notice_version),
    INDEX idx_publication_date (publication_date),
    INDEX idx_notice_type (notice_type)
);

CREATE TABLE procedures (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    cross_border_law VARCHAR(100),
    procedure_type VARCHAR(50),
    procedure_features TEXT,
    procedure_accelerated BOOLEAN,
    lots_max_allowed INT,
    lots_all_required BOOLEAN,
    lots_max_awarded INT,
    
    PRIMARY KEY (notice_identifier, notice_version),
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);

CREATE TABLE lots (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50) NOT NULL,
    
    PRIMARY KEY (notice_identifier, notice_version, lot_identifier),
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);

-- ============================================================================
-- ⭐ NEUE TABELLE: PURPOSE - ENTHÄLT TITEL & BESCHREIBUNG! ⭐
-- ============================================================================

CREATE TABLE purposes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),  -- NULL = Notice-Level, sonst Lot-Level
    internal_identifier VARCHAR(100),
    main_nature VARCHAR(20),  -- 'services', 'works', 'supplies'
    additional_nature VARCHAR(50),
    title TEXT,  -- ⭐ TITEL!
    estimated_value DECIMAL(15,2),
    estimated_value_currency VARCHAR(3),
    description TEXT,  -- ⭐ BESCHREIBUNG!
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_nature (main_nature),
    INDEX idx_lot (notice_identifier, notice_version, lot_identifier),
    FULLTEXT INDEX idx_title (title),
    FULLTEXT INDEX idx_description (description)
);

-- ============================================================================
-- DETAIL-TABELLEN
-- ============================================================================

CREATE TABLE classifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    classification_type VARCHAR(20),
    main_classification_code VARCHAR(20),
    additional_classification_codes TEXT,
    options TEXT,
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_main_cpv (main_classification_code)
);

CREATE TABLE organisations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    organisation_name VARCHAR(500),
    organisation_identifier VARCHAR(200),
    organisation_city VARCHAR(200),
    organisation_post_code VARCHAR(20),
    organisation_country_subdivision VARCHAR(10),
    organisation_country_code VARCHAR(3),
    organisation_internet_address VARCHAR(500),
    organisation_natural_person BOOLEAN,
    organisation_role VARCHAR(50),
    buyer_profile_url VARCHAR(500),
    buyer_legal_type VARCHAR(50),
    buyer_contracting_entity BOOLEAN,
    winner_size VARCHAR(20),
    winner_owner_nationality VARCHAR(3),
    winner_listed BOOLEAN,
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_role (organisation_role),
    INDEX idx_region (organisation_country_subdivision),
    FULLTEXT INDEX idx_name (organisation_name)
);

CREATE TABLE places_of_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    street VARCHAR(500),
    town VARCHAR(200),
    post_code VARCHAR(20),
    country_subdivision VARCHAR(10),
    country_code VARCHAR(3),
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_region (country_subdivision)
);

CREATE TABLE submission_terms (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    tender_validity_deadline DECIMAL(10,1),
    tender_validity_deadline_unit VARCHAR(20),
    guarantee_required BOOLEAN,
    public_opening_date TIMESTAMP,
    
    FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version),
    INDEX idx_opening_date (public_opening_date)
);

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
    INDEX idx_value (tender_value)
);

-- ============================================================================
-- SUCHBARE AUSSCHREIBUNGEN (Denormalisiert)
-- ============================================================================

CREATE TABLE searchable_tenders AS
SELECT 
    n.notice_identifier,
    n.notice_version,
    n.notice_type,
    n.publication_date,
    
    -- ⭐ TITEL & BESCHREIBUNG (aus PURPOSE!)
    (SELECT title 
     FROM purposes 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
       AND lot_identifier IS NULL
     LIMIT 1) as title,
    
    (SELECT description 
     FROM purposes 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
       AND lot_identifier IS NULL
     LIMIT 1) as description,
    
    -- Art des Auftrags
    (SELECT main_nature 
     FROM purposes 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
     LIMIT 1) as contract_nature,
    
    -- Geschätzter Wert (aus PURPOSE!)
    (SELECT estimated_value 
     FROM purposes 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version 
       AND lot_identifier IS NULL
     LIMIT 1) as estimated_value,
    
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
    
    -- Tatsächlicher Auftragswert (bei Results)
    (SELECT SUM(tender_value) 
     FROM tenders 
     WHERE notice_identifier = n.notice_identifier 
       AND notice_version = n.notice_version) as actual_value,
    
    -- Verfahrenstyp
    p.procedure_type

FROM notices n
LEFT JOIN classifications c ON n.notice_identifier = c.notice_identifier 
    AND n.notice_version = c.notice_version
LEFT JOIN procedures p ON n.notice_identifier = p.notice_identifier 
    AND n.notice_version = p.notice_version

WHERE n.notice_type = 'competition'
GROUP BY n.notice_identifier, n.notice_version;

-- ============================================================================
-- INDIZES FÜR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_search_cpv ON searchable_tenders(cpv_codes(100));
CREATE INDEX idx_search_region ON searchable_tenders(buyer_region);
CREATE INDEX idx_search_deadline ON searchable_tenders(deadline);
CREATE INDEX idx_search_publication ON searchable_tenders(publication_date);
CREATE INDEX idx_search_nature ON searchable_tenders(contract_nature);
CREATE INDEX idx_search_value ON searchable_tenders(estimated_value);
CREATE FULLTEXT INDEX idx_search_title ON searchable_tenders(title);
CREATE FULLTEXT INDEX idx_search_description ON searchable_tenders(description);
CREATE FULLTEXT INDEX idx_search_buyer ON searchable_tenders(buyer_name);

-- ============================================================================
-- BEISPIEL-QUERIES
-- ============================================================================

-- Suche IT-Dienstleistungen (CPV 72) in Bayern mit Budget > 50k
SELECT 
    title,
    buyer_name,
    buyer_city,
    estimated_value,
    deadline,
    cpv_codes
FROM searchable_tenders
WHERE cpv_codes REGEXP '(^|,)72'
  AND contract_nature = 'services'
  AND buyer_region LIKE 'DE2%'
  AND estimated_value > 50000
  AND deadline > NOW()
ORDER BY publication_date DESC;

-- Volltext-Suche: "Software" im Titel oder Beschreibung
SELECT 
    title,
    description,
    buyer_name,
    estimated_value
FROM searchable_tenders
WHERE MATCH(title, description) AGAINST('Software' IN NATURAL LANGUAGE MODE)
  AND deadline > NOW()
ORDER BY publication_date DESC;

-- Top 10 Auftraggeber nach Anzahl Ausschreibungen
SELECT 
    buyer_name,
    buyer_city,
    COUNT(*) as tender_count,
    SUM(estimated_value) as total_value
FROM searchable_tenders
WHERE estimated_value IS NOT NULL
GROUP BY buyer_name, buyer_city
ORDER BY tender_count DESC
LIMIT 10;

-- Durchschnittswert pro Auftragsart
SELECT 
    contract_nature,
    COUNT(*) as count,
    AVG(estimated_value) as avg_value,
    SUM(estimated_value) as total_value
FROM searchable_tenders
WHERE estimated_value IS NOT NULL
GROUP BY contract_nature
ORDER BY total_value DESC;
