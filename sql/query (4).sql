-- Durchschnittliche Größe pro Purpose (in Bytes)
SELECT 
    COUNT(*) as anzahl_purposes,
    AVG(DATALENGTH(title)) as avg_title_bytes,
    AVG(DATALENGTH(description)) as avg_description_bytes,
    AVG(DATALENGTH(title) + DATALENGTH(description)) as avg_total_bytes,
    SUM(DATALENGTH(title) + DATALENGTH(description)) / 1024.0 / 1024.0 as total_mb
FROM purposes
WHERE title IS NOT NULL OR description IS NOT NULL;