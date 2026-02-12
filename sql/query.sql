-- ============================================================================
-- VergabeRadar Schema - KORRIGIERT (ohne Fulltext vorerst)
-- ============================================================================

-- Lösche alte Tabellen falls vorhanden
DROP VIEW IF EXISTS searchable_tenders_view;
DROP TABLE IF EXISTS tenders;
DROP TABLE IF EXISTS submission_terms;
DROP TABLE IF EXISTS places_of_performance;
DROP TABLE IF EXISTS organisations;
DROP TABLE IF EXISTS classifications;
DROP TABLE IF EXISTS purposes;
DROP TABLE IF EXISTS lots;
DROP TABLE IF EXISTS procedures;
DROP TABLE IF EXISTS notices;
GO

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
    publication_date DATETIME2,
    
    CONSTRAINT PK_notices PRIMARY KEY (notice_identifier, notice_version)
);
GO

CREATE INDEX idx_notices_publication_date ON notices(publication_date);
CREATE INDEX idx_notices_notice_type ON notices(notice_type);
GO

-- Verfahren
CREATE TABLE procedures (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    cross_border_law VARCHAR(100),
    procedure_type VARCHAR(50),
    procedure_features NVARCHAR(MAX),
    procedure_accelerated BIT,
    lots_max_allowed INT,
    lots_all_required BIT,
    lots_max_awarded INT,
    
    CONSTRAINT PK_procedures PRIMARY KEY (notice_identifier, notice_version),
    CONSTRAINT FK_procedures_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

-- Lose
CREATE TABLE lots (
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50) NOT NULL,
    
    CONSTRAINT PK_lots PRIMARY KEY (notice_identifier, notice_version, lot_identifier),
    CONSTRAINT FK_lots_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

-- ============================================================================
-- PURPOSE - TITEL & BESCHREIBUNG
-- ============================================================================

CREATE TABLE purposes (
    id BIGINT IDENTITY(1,1),
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    internal_identifier VARCHAR(100),
    main_nature VARCHAR(20),
    additional_nature VARCHAR(50),
    title NVARCHAR(MAX),
    estimated_value DECIMAL(15,2),
    estimated_value_currency VARCHAR(3),
    description NVARCHAR(MAX),
    
    CONSTRAINT PK_purposes PRIMARY KEY (id),
    CONSTRAINT FK_purposes_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

CREATE INDEX idx_purposes_notice ON purposes(notice_identifier, notice_version);
CREATE INDEX idx_purposes_lot ON purposes(lot_identifier);
CREATE INDEX idx_purposes_nature ON purposes(main_nature);
GO

-- ============================================================================
-- KLASSIFIZIERUNG
-- ============================================================================

CREATE TABLE classifications (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    classification_type VARCHAR(20),
    main_classification_code VARCHAR(20),
    additional_classification_codes NVARCHAR(MAX),
    options NVARCHAR(MAX),
    
    CONSTRAINT FK_classifications_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

CREATE INDEX idx_classifications_cpv ON classifications(main_classification_code);
CREATE INDEX idx_classifications_notice ON classifications(notice_identifier, notice_version);
GO

-- ============================================================================
-- ORGANISATIONEN
-- ============================================================================

CREATE TABLE organisations (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    organisation_name NVARCHAR(500),
    organisation_identifier VARCHAR(200),
    organisation_city NVARCHAR(200),
    organisation_post_code VARCHAR(20),
    organisation_country_subdivision VARCHAR(10),
    organisation_country_code VARCHAR(3),
    organisation_internet_address NVARCHAR(500),
    organisation_natural_person BIT,
    organisation_role VARCHAR(50),
    buyer_profile_url NVARCHAR(500),
    buyer_legal_type VARCHAR(50),
    buyer_contracting_entity BIT,
    winner_size VARCHAR(20),
    winner_owner_nationality VARCHAR(3),
    winner_listed BIT,
    
    CONSTRAINT FK_organisations_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

CREATE INDEX idx_organisations_role ON organisations(organisation_role);
CREATE INDEX idx_organisations_region ON organisations(organisation_country_subdivision);
CREATE INDEX idx_organisations_notice ON organisations(notice_identifier, notice_version);
GO

-- ============================================================================
-- AUSFÜHRUNGSORT
-- ============================================================================

CREATE TABLE places_of_performance (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    street NVARCHAR(500),
    town NVARCHAR(200),
    post_code VARCHAR(20),
    country_subdivision VARCHAR(10),
    country_code VARCHAR(3),
    
    CONSTRAINT FK_places_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

CREATE INDEX idx_places_region ON places_of_performance(country_subdivision);
CREATE INDEX idx_places_notice ON places_of_performance(notice_identifier, notice_version);
GO

-- ============================================================================
-- FRISTEN
-- ============================================================================

CREATE TABLE submission_terms (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    notice_identifier VARCHAR(100) NOT NULL,
    notice_version VARCHAR(10) NOT NULL,
    lot_identifier VARCHAR(50),
    tender_validity_deadline DECIMAL(10,1),
    tender_validity_deadline_unit VARCHAR(20),
    guarantee_required BIT,
    public_opening_date DATETIME2,
    
    CONSTRAINT FK_submission_terms_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

CREATE INDEX idx_submission_opening ON submission_terms(public_opening_date);
CREATE INDEX idx_submission_notice ON submission_terms(notice_identifier, notice_version);
GO

-- ============================================================================
-- ANGEBOTE
-- ============================================================================

CREATE TABLE tenders (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
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
    
    CONSTRAINT FK_tenders_notices FOREIGN KEY (notice_identifier, notice_version) 
        REFERENCES notices(notice_identifier, notice_version)
);
GO

CREATE INDEX idx_tenders_value ON tenders(tender_value);
CREATE INDEX idx_tenders_notice ON tenders(notice_identifier, notice_version);
GO

-- ============================================================================
-- SUCH-VIEW
-- ============================================================================

CREATE VIEW searchable_tenders_view AS
SELECT 
    n.notice_identifier,
    n.notice_version,
    n.notice_type,
    n.publication_date,
    
    -- Titel & Beschreibung (nur Notice-Level, nicht Lot-Level)
    p.title,
    p.description,
    p.main_nature as contract_nature,
    p.estimated_value,
    
    -- CPV Code (erste Klassifikation)
    (SELECT TOP 1 main_classification_code 
     FROM classifications c 
     WHERE c.notice_identifier = n.notice_identifier 
       AND c.notice_version = n.notice_version
       AND c.lot_identifier IS NULL) as cpv_code,
    
    -- Auftraggeber
    (SELECT TOP 1 organisation_name 
     FROM organisations o
     WHERE o.notice_identifier = n.notice_identifier 
       AND o.notice_version = n.notice_version 
       AND o.organisation_role = 'buyer') as buyer_name,
    
    (SELECT TOP 1 organisation_city 
     FROM organisations o
     WHERE o.notice_identifier = n.notice_identifier 
       AND o.notice_version = n.notice_version 
       AND o.organisation_role = 'buyer') as buyer_city,
     
    (SELECT TOP 1 organisation_country_subdivision 
     FROM organisations o
     WHERE o.notice_identifier = n.notice_identifier 
       AND o.notice_version = n.notice_version 
       AND o.organisation_role = 'buyer') as buyer_region,
    
    -- Deadline
    (SELECT TOP 1 public_opening_date 
     FROM submission_terms st
     WHERE st.notice_identifier = n.notice_identifier 
       AND st.notice_version = n.notice_version) as deadline,
    
    -- Verfahrenstyp
    pr.procedure_type

FROM notices n
LEFT JOIN purposes p ON n.notice_identifier = p.notice_identifier 
    AND n.notice_version = p.notice_version
    AND p.lot_identifier IS NULL
LEFT JOIN procedures pr ON n.notice_identifier = pr.notice_identifier 
    AND n.notice_version = pr.notice_version

WHERE n.notice_type = 'competition';
GO

PRINT '✅ Schema erfolgreich erstellt!';
PRINT '';
PRINT 'Tabellen (9):';
PRINT '  - notices';
PRINT '  - procedures';
PRINT '  - lots';
PRINT '  - purposes (Titel & Beschreibung)';
PRINT '  - classifications (CPV-Codes)';
PRINT '  - organisations (Auftraggeber)';
PRINT '  - places_of_performance';
PRINT '  - submission_terms';
PRINT '  - tenders';
PRINT '';
PRINT 'Views (1):';
PRINT '  - searchable_tenders_view';
PRINT '';
PRINT '⚠️  Fulltext Index wird später hinzugefügt (wenn Daten vorhanden)';
GO