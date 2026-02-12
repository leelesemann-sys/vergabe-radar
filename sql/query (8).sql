-- Test 1: Ausschreibungen mit Titel
SELECT TOP 5
    n.notice_identifier,
    n.publication_date,
    p.title,
    p.main_nature,
    c.main_classification_code as cpv_code,
    o.organisation_name as buyer
FROM notices n
LEFT JOIN purposes p ON n.notice_identifier = p.notice_identifier 
    AND n.notice_version = p.notice_version
LEFT JOIN classifications c ON n.notice_identifier = c.notice_identifier
    AND n.notice_version = c.notice_version
LEFT JOIN organisations o ON n.notice_identifier = o.notice_identifier
    AND n.notice_version = o.notice_version
    AND o.organisation_role = 'buyer'
WHERE p.title IS NOT NULL
ORDER BY n.publication_date DESC;