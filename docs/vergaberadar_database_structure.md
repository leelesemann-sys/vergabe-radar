# VergabeRadar - Datenbankstruktur

## 📊 Entity-Relationship Diagramm (Relationales Schema)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KERN-TABELLEN                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│      NOTICES             │  ◄─── Haupttabelle (Master)
├──────────────────────────┤
│ PK notice_identifier     │
│ PK notice_version        │
│    procedure_identifier  │
│    procedure_legal_basis │
│    form_type             │
│    notice_type           │  ← 'competition' oder 'result'
│    publication_date      │
└──────────────────────────┘
            │
            │ 1:1
            ├──────────────────────┐
            │                      │
            ▼                      ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│    PROCEDURES            │   │       LOTS               │
├──────────────────────────┤   ├──────────────────────────┤
│ FK notice_identifier     │   │ FK notice_identifier     │
│ FK notice_version        │   │ FK notice_version        │
│    procedure_type        │   │ PK lot_identifier        │
│    procedure_features    │   └──────────────────────────┘
│    lots_max_allowed      │              │
└──────────────────────────┘              │ 1:N
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DETAIL-TABELLEN (1:N zu NOTICES)                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐  ┌──────────────────────────────┐
│    CLASSIFICATIONS           │  │      ORGANISATIONS           │
├──────────────────────────────┤  ├──────────────────────────────┤
│ PK id                        │  │ PK id                        │
│ FK notice_identifier         │  │ FK notice_identifier         │
│ FK notice_version            │  │ FK notice_version            │
│    lot_identifier (nullable) │  │    organisation_name         │
│    main_classification_code  │  │    organisation_city         │
│    additional_codes          │  │    organisation_role         │  ← 'buyer'/'tenderer'
│                              │  │    country_subdivision       │  ← NUTS-Code
└──────────────────────────────┘  │    buyer_legal_type          │
         │                        └──────────────────────────────┘
         │ CPV-Codes                         │
         │ (30, 48, 72, 79)                  │ Auftraggeber
         │                                   │
         ▼                                   ▼

┌──────────────────────────────┐  ┌──────────────────────────────┐
│   PLACES_OF_PERFORMANCE      │  │    SUBMISSION_TERMS          │
├──────────────────────────────┤  ├──────────────────────────────┤
│ PK id                        │  │ PK id                        │
│ FK notice_identifier         │  │ FK notice_identifier         │
│ FK notice_version            │  │ FK notice_version            │
│    lot_identifier            │  │    lot_identifier            │
│    town                      │  │    public_opening_date       │  ← Deadline!
│    post_code                 │  │    tender_validity_deadline  │
│    country_subdivision       │  │    guarantee_required        │
└──────────────────────────────┘  └──────────────────────────────┘
         │ Region                            │ Fristen
         │                                   │
         ▼                                   ▼

┌──────────────────────────────┐
│         TENDERS              │  ← Nur bei notice_type='result'
├──────────────────────────────┤
│ PK id                        │
│ FK notice_identifier         │
│ FK notice_version            │
│    tender_identifier         │
│    lot_identifier            │
│    tender_value              │  ← Budget/Wert
│    tender_value_currency     │
│    country_origin            │
└──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    DENORMALISIERTE SUCH-TABELLE                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   SEARCHABLE_TENDERS                           │
│                (Materialized View für Performance)             │
├────────────────────────────────────────────────────────────────┤
│  notice_identifier, notice_version                             │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ cpv_codes              ← Aggregiert aus CLASSIFICATIONS   │
│  │ buyer_name, buyer_city ← Join mit ORGANISATIONS           │
│  │ buyer_region           ← NUTS-Code                         │
│  │ performance_region     ← Join mit PLACES_OF_PERFORMANCE    │
│  │ deadline               ← Join mit SUBMISSION_TERMS         │
│  │ total_value            ← Sum aus TENDERS                   │
│  │ procedure_type         ← Join mit PROCEDURES               │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  Indizes:                                                      │
│    ✓ cpv_codes (für Kategorie-Filter)                         │
│    ✓ buyer_region (für Regions-Filter)                        │
│    ✓ deadline (für Fristen-Filter)                            │
│    ✓ publication_date (für Sortierung)                        │
│    ✓ buyer_name (FULLTEXT für Suche)                          │
└────────────────────────────────────────────────────────────────┘
```

---

## 📋 Tabellenübersicht

### ✅ Kern-Tabellen (Master Data)
| Tabelle | Zweck | Primärschlüssel | Zeilen (Beispiel) |
|---------|-------|-----------------|-------------------|
| **notices** | Haupttabelle aller Bekanntmachungen | notice_id + version | 300 |
| **procedures** | Verfahrensdetails | notice_id + version | 300 |
| **lots** | Einzelne Lose/Auftragsteile | notice_id + version + lot_id | 400 |

### ✅ Detail-Tabellen (1:N Beziehungen)
| Tabelle | Zweck | Foreign Key | Zeilen (Beispiel) |
|---------|-------|-------------|-------------------|
| **classifications** | CPV-Codes (Kategorien) | notice_id + version | 700 |
| **organisations** | Auftraggeber, Bieter, Prüfer | notice_id + version | 800 |
| **places_of_performance** | Ausführungsorte | notice_id + version | 700 |
| **submission_terms** | Fristen, Deadlines | notice_id + version | 350 |
| **tenders** | Angebote & Budgets | notice_id + version | 350 |

### ✅ Such-Optimierung
| Tabelle | Zweck | Update-Frequenz |
|---------|-------|-----------------|
| **searchable_tenders** | Denormalisierte Such-Tabelle | Nach jedem Import |

---

## ⚠️ KRITISCHES PROBLEM: Titel & Beschreibung fehlen!

### ❌ Was fehlt in den CSV-Dateien:
- **Titel** der Ausschreibung (BT-21 in eForms)
- **Beschreibung** (BT-24 in eForms)
- **Leistungsbeschreibung**
- **Weitere Textfelder**

### ✅ Wo sind diese Daten?

Die CSV-Dateien enthalten **nur strukturierte Metadaten**!

**Titel & Beschreibung sind in:**
1. **eForms XML** (Original-Format)
2. **OCDS JSON** (Open Contracting Data Standard)

---

## 💡 LÖSUNG: Hybrid-Ansatz

### Strategie 1: CSV + eForms XML (Empfohlen)

```python
# 1. Import CSV für schnelle Filterung
import_csv_to_database()  # Struktur wie oben

# 2. Parse eForms XML für Titel/Beschreibung
for xml_file in eforms_zip:
    notice_id = extract_notice_id(xml_file)
    title = extract_bt_21(xml_file)  # BT-21 = Title
    description = extract_bt_24(xml_file)  # BT-24 = Description
    
    # Update Database
    db.execute("""
        UPDATE notices 
        SET title = ?, description = ?
        WHERE notice_identifier = ?
    """, [title, description, notice_id])
```

### Strategie 2: Nur OCDS JSON

```python
# OCDS ist vollständig und strukturiert (JSON)
# Aber: Mehr Speicher, langsamere Filterung

for json_file in ocds_zip:
    tender = parse_ocds(json_file)
    
    save_to_db({
        'id': tender['id'],
        'title': tender['tender']['title'],  # ← Hier ist der Titel!
        'description': tender['tender']['description'],
        'cpv': tender['tender']['classification']['id'],
        'buyer': tender['parties'][0]['name'],
        'value': tender['tender']['value']['amount']
    })
```

---

## 🎯 Empfohlene Datenbankstruktur (erweitert)

```sql
-- Erweitere notices-Tabelle um Textfelder
ALTER TABLE notices ADD COLUMN title TEXT;
ALTER TABLE notices ADD COLUMN description TEXT;

-- Erweitere lots-Tabelle
ALTER TABLE lots ADD COLUMN lot_title TEXT;
ALTER TABLE lots ADD COLUMN lot_description TEXT;
ALTER TABLE lots ADD COLUMN lot_value DECIMAL(15,2);

-- Fulltext-Index für Suche
CREATE FULLTEXT INDEX idx_notice_title ON notices(title);
CREATE FULLTEXT INDEX idx_notice_description ON notices(description);
```

---

## 📊 Datenvolumen (Hochrechnung)

**Pro Tag:** ~300 Notices
**Pro Monat:** ~9,000 Notices
**Seit 2022-12:** ~30 Monate × 9,000 = **~270,000 Notices**

### Speicherbedarf (geschätzt):

| Komponente | Größe |
|------------|-------|
| CSV-Metadaten (270k Notices) | ~500 MB |
| eForms XML (Volltext) | ~5 GB |
| OCDS JSON | ~3 GB |
| **Datenbank (optimiert)** | ~1-2 GB |

---

## 🚀 Nächste Schritte

1. **Download eForms oder OCDS Format**
   ```bash
   # Statt format=csv.zip
   format=eforms.zip  # oder
   format=ocds.zip
   ```

2. **Parse XML/JSON für Titel**
   - Tool: python-eforms oder OCDS-Parser
   - Extraktion: BT-21 (Title), BT-24 (Description)

3. **Import in Datenbank**
   - CSV: Strukturierte Daten
   - XML/JSON: Textfelder nachladen

4. **VergabeRadar API bauen**
   - FastAPI oder Django REST
   - Suche über `searchable_tenders`
   - Filter: CPV, Region, Budget, Deadline

---

## ✅ Zusammenfassung

| Feature | CSV | eForms XML | OCDS JSON |
|---------|-----|------------|-----------|
| CPV-Codes | ✅ | ✅ | ✅ |
| Auftraggeber | ✅ | ✅ | ✅ |
| Budget | ✅ | ✅ | ✅ |
| Region | ✅ | ✅ | ✅ |
| Deadline | ⚠️ Teilweise | ✅ | ✅ |
| **Titel** | ❌ | ✅ | ✅ |
| **Beschreibung** | ❌ | ✅ | ✅ |
| Geschwindigkeit | 🚀 Schnell | 🐌 Langsam | 🏃 Mittel |
| Größe | 📦 Klein | 📦📦📦 Groß | 📦📦 Mittel |

**Empfehlung:** CSV für Metadaten + eForms/OCDS für Titel/Beschreibung
