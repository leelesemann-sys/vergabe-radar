-- Anzahl Datensätze pro Tabelle
SELECT 'notices' as Tabelle, COUNT(*) as Anzahl FROM notices
UNION ALL
SELECT 'procedures', COUNT(*) FROM procedures
UNION ALL
SELECT 'lots', COUNT(*) FROM lots
UNION ALL
SELECT 'purposes', COUNT(*) FROM purposes
UNION ALL
SELECT 'classifications', COUNT(*) FROM classifications
UNION ALL
SELECT 'organisations', COUNT(*) FROM organisations
UNION ALL
SELECT 'places_of_performance', COUNT(*) FROM places_of_performance
UNION ALL
SELECT 'submission_terms', COUNT(*) FROM submission_terms
UNION ALL
SELECT 'tenders', COUNT(*) FROM tenders
ORDER BY Anzahl DESC;