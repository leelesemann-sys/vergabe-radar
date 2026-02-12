-- Zeitraum und Anzahl Notices
SELECT 
    COUNT(*) as total_notices,
    COUNT(DISTINCT notice_identifier) as eindeutige_notices,
    MIN(publication_date) as von_datum,
    MAX(publication_date) as bis_datum,
    COUNT(DISTINCT CAST(publication_date AS DATE)) as anzahl_tage
FROM notices;