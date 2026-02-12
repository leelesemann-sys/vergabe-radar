SELECT 
    COUNT(*) as anzahl_purposes,
    SUM(DATALENGTH(title) + DATALENGTH(description)) / 1024.0 / 1024.0 as text_mb,
    SUM(DATALENGTH(title) + DATALENGTH(description)) / 1024.0 / 1024.0 * 1.7 as index_mb
FROM purposes;
