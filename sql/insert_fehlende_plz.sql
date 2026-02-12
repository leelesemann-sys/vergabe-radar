-- VergabeRadar: Fehlende 32 PLZs manuell ergänzen
-- Hardcoded mit Google Maps Koordinaten

INSERT INTO plz_coordinates (plz, lat, lng, city, state) VALUES
-- Top-Priorität (>3 Einträge)
('01001', 51.0504, 13.7373, 'Dresden', 'Sachsen'),
('30147', 52.3861, 9.7320, 'Hannover', 'Niedersachsen'),
('39090', 52.1205, 11.6276, 'Magdeburg', 'Sachsen-Anhalt'),
('23538', 53.8755, 10.6865, 'Lübeck', 'Schleswig-Holstein'),
('12591', 52.5421, 13.5945, 'Berlin', 'Berlin'),

-- Mittel-Priorität (2-3 Einträge)
('55503', 49.8420, 7.8614, 'Bad Kreuznach', 'Rheinland-Pfalz'),
('58079', 51.3669, 7.4712, 'Hagen', 'Nordrhein-Westfalen'),
('60547', 50.0503, 8.5717, 'Frankfurt am Main', 'Hessen'),
('72015', 48.5216, 9.0576, 'Tübingen', 'Baden-Württemberg'),
('60590', 50.0978, 8.6442, 'Frankfurt am Main', 'Hessen'),
('66041', 49.2401, 7.0003, 'Saarbrücken', 'Saarland'),
('99437', 50.8969, 11.2847, 'Bad Berka', 'Thüringen'),
('01099', 51.0657, 13.7512, 'Dresden', 'Sachsen'),
('12414', 52.4535, 13.5755, 'Berlin', 'Berlin'),
('04092', 51.3406, 12.3747, 'Leipzig', 'Sachsen'),
('04453', 51.4006, 12.2244, 'Schkeuditz', 'Sachsen'),
('28334', 53.1067, 8.8517, 'Bremen', 'Bremen'),
('50960', 50.9364, 6.9528, 'Köln', 'Nordrhein-Westfalen'),

-- Niedrig-Priorität (1 Eintrag)
('52425', 50.9227, 6.3608, 'Jülich', 'Nordrhein-Westfalen'),
('40837', 51.2969, 6.8492, 'Ratingen', 'Nordrhein-Westfalen'),
('44777', 51.4818, 7.2162, 'Bochum', 'Nordrhein-Westfalen'),
('46473', 51.6588, 6.6189, 'Wesel', 'Nordrhein-Westfalen'),
('08067', 50.7182, 12.4958, 'Zwickau', 'Sachsen'),
('10704', 52.5065, 13.2846, 'Berlin', 'Berlin'),
('10837', 52.4954, 13.3728, 'Berlin', 'Berlin'),
('17042', 53.5578, 13.2611, 'Neubrandenburg', 'Mecklenburg-Vorpommern'),
('19092', 53.6288, 11.4148, 'Schwerin', 'Mecklenburg-Vorpommern'),
('02625', 51.1807, 14.4343, 'Bautzen', 'Sachsen'),
('69045', 49.4093, 8.6764, 'Heidelberg', 'Baden-Württemberg'),
('63037', 50.1025, 8.7649, 'Offenbach am Main', 'Hessen'),
('78457', 47.6779, 9.1732, 'Konstanz', 'Baden-Württemberg'),
('85326', 48.3538, 11.7861, 'München-Flughafen', 'Bayern'),
('85577', 48.0787, 11.6514, 'Neubiberg', 'Bayern');

-- Prüfe Ergebnis
SELECT COUNT(*) as neue_plz_anzahl FROM plz_coordinates 
WHERE plz IN ('01001', '30147', '39090', '23538', '12591', '55503', '58079', '60547', '72015', '60590', '66041', '99437', '01099', '12414', '04092', '04453', '28334', '50960', '52425', '40837', '44777', '46473', '08067', '10704', '10837', '17042', '19092', '02625', '69045', '63037', '78457', '85326', '85577');
