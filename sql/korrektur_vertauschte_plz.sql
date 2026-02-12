-- VergabeRadar: Korrektur vertauschter PLZ/Stadt-Einträge
-- Kein ID-Feld nötig - WHERE-Bedingung reicht!

-- 1. Dresden/01099 korrigieren
UPDATE organisations
SET 
    organisation_post_code = '01099',
    organisation_city = 'Dresden'
WHERE organisation_post_code = 'Dresden'
  AND organisation_city = '01099';

-- 2. Bautzen/02625 korrigieren  
UPDATE organisations
SET 
    organisation_post_code = '02625',
    organisation_city = 'Bautzen'
WHERE organisation_post_code = 'Bautzen'
  AND organisation_city = '02625';

-- 3. Ungültige "." Einträge bereinigen
UPDATE organisations
SET 
    organisation_post_code = NULL,
    organisation_city = NULL
WHERE organisation_post_code = '.'
  OR organisation_city = '.';

-- Prüfe Ergebnis
SELECT 
    organisation_post_code as plz,
    organisation_city as stadt,
    COUNT(*) as anzahl
FROM organisations
WHERE organisation_role = 'buyer'
  AND (
      organisation_post_code IN ('01099', '02625')
      OR organisation_post_code = '.'
  )
GROUP BY organisation_post_code, organisation_city
ORDER BY organisation_post_code;
