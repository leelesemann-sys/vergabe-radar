-- Detaillierte Statistik
SELECT 
    'Notices gesamt' as Metric, 
    COUNT(*) as Wert 
FROM notices

UNION ALL

SELECT 
    'Purposes mit Titel', 
    COUNT(*) 
FROM purposes 
WHERE title IS NOT NULL

UNION ALL

SELECT 
    'Eindeutige CPV-Codes', 
    COUNT(DISTINCT main_classification_code) 
FROM classifications

UNION ALL

SELECT 
    'Auftraggeber', 
    COUNT(*) 
FROM organisations 
WHERE organisation_role = 'buyer'

UNION ALL

SELECT 
    'Notices mit Budget', 
    COUNT(DISTINCT notice_identifier) 
FROM purposes 
WHERE estimated_value IS NOT NULL

UNION ALL

SELECT 
    'Notices mit Deadline', 
    COUNT(DISTINCT notice_identifier) 
FROM submission_terms 
WHERE public_opening_date IS NOT NULL;