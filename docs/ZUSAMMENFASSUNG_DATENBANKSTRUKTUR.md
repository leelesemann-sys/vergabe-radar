# VergabeRadar - Datenbankstruktur Übersicht

## 🎯 Zusammenfassung

**Ja, wir können eine vollständige Datenbank bauen!**

✅ **CSV-Daten:** Strukturierte Metadaten (CPV, Auftraggeber, Budget, Region)  
⚠️ **Problem:** Titel & Beschreibung fehlen in CSV  
✅ **Lösung:** OCDS JSON oder eForms XML für Textfelder nutzen

---

## 📊 Relationales Schema (8 Haupttabellen)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATENBANK: vergaberadar                      │
└─────────────────────────────────────────────────────────────────┘

┌───────────────┐         ┌────────────────┐         ┌──────────────┐
│   NOTICES     │────1:1──│   PROCEDURES   │         │     LOTS     │
│ (Hauptdaten)  │         │  (Verfahren)   │    ┌───│ (Lose/Teile) │
├───────────────┤         ├────────────────┤    │    ├──────────────┤
│ PK id+version │         │ FK id+version  │    │    │ FK id+version│
│    type       │         │    type        │    │    │ PK lot_id    │
│    pub_date   │         │    features    │    │    └──────────────┘
│  ⚠️ title     │         └────────────────┘    │            │
│  ⚠️ description│                               │            │
└───────────────┘                               │            │
        │                                       │            │
        │ 1:N                                   │            │
        ├───────┬───────────┬─────────┬─────────┴────────────┘
        │       │           │         │
        ▼       ▼           ▼         ▼
┌──────────┐ ┌──────┐ ┌──────────┐ ┌────────┐
│CLASSIFI- │ │ORGAN-│ │PLACES_OF_│ │SUBMIS- │
│CATIONS   │ │ISATIONS│ │PERFORM. │ │SION_   │
│          │ │      │ │          │ │TERMS   │
│🎯 CPV    │ │👥 Buyer│ │📍 Region │ │⏰ Deadline│
└──────────┘ └──────┘ └──────────┘ └────────┘

                ┌──────────┐
                │ TENDERS  │
                │          │
                │💰 Budget │
                └──────────┘

        ┌─────────────────────────────┐
        │   SEARCHABLE_TENDERS        │
        │   (Denormalisiert)          │
        │                             │
        │ ✓ cpv_codes                 │
        │ ✓ buyer_name, buyer_region  │
        │ ✓ performance_region        │
        │ ✓ deadline                  │
        │ ✓ total_value               │
        │ ⚠️ title (aus OCDS!)        │
        │ ⚠️ description (aus OCDS!)  │
        └─────────────────────────────┘
```

**Legende:**
- ✅ = Vorhanden in CSV
- ⚠️ = Fehlt in CSV, muss aus OCDS/eForms geladen werden

---

## 📋 Vollständige Tabellenliste

| # | Tabelle | Zweck | Primärschlüssel | Zeilen/Tag |
|---|---------|-------|-----------------|------------|
| 1 | **notices** | Haupt-Bekanntmachungen | notice_id + version | ~300 |
| 2 | **procedures** | Verfahrensdetails | notice_id + version | ~300 |
| 3 | **lots** | Lose/Auftragsabschnitte | notice_id + version + lot_id | ~400 |
| 4 | **classifications** | CPV-Codes | auto_id | ~700 |
| 5 | **organisations** | Auftraggeber/Bieter | auto_id | ~800 |
| 6 | **places_of_performance** | Ausführungsorte | auto_id | ~700 |
| 7 | **submission_terms** | Fristen/Deadlines | auto_id | ~350 |
| 8 | **tenders** | Angebote/Budgets | auto_id | ~350 |
| 9 | **searchable_tenders** | Such-Optimierung | notice_id + version | ~300 |

**Gesamt pro Tag:** ~4,200 Datensätze
**Gesamt seit 2022-12:** ~3,8 Millionen Datensätze

---

## 🔑 Wichtige Felder für VergabeRadar

### ✅ Was wir haben (CSV):

| Feld | Tabelle | Verwendung |
|------|---------|------------|
| **CPV-Code** | classifications | Kategorie-Filter (IT = 30/48/72/79) |
| **Auftraggeber** | organisations | Anzeige, Filter |
| **Region (NUTS)** | organisations, places_of_performance | Regions-Filter |
| **Budget** | tenders | Budget-Filter, Sortierung |
| **Deadline** | submission_terms | Fristen-Filter |
| **Publikationsdatum** | notices | Sortierung, "Neu heute" |
| **Verfahrenstyp** | procedures | Offenes Verfahren, etc. |

### ⚠️ Was fehlt (OCDS/eForms):

| Feld | Quelle | Kritisch? |
|------|--------|-----------|
| **Titel** | OCDS: tender.title | ⭐⭐⭐ JA |
| **Beschreibung** | OCDS: tender.description | ⭐⭐⭐ JA |
| Los-Titel | OCDS: tender.lots[].title | ⭐⭐ Wichtig |
| Los-Beschreibung | OCDS: tender.lots[].description | ⭐ Nice-to-have |

---

## 💡 Empfohlene Implementierung

### Phase 1: MVP mit CSV (JETZT)

```python
# Import nur CSV-Daten
# ✅ Funktioniert OHNE Titel
# ⚠️ User sieht nur: "Ausschreibung #db6a23a1..."

pipeline = [
    download_csv_daily(),
    import_to_database(),
    create_searchable_tenders(),
    # Filter funktionieren:
    filter_by_cpv(['72', '30']),  # ✅ IT-Ausschreibungen
    filter_by_region('DE3'),       # ✅ Berlin
    filter_by_budget(10000, 100000) # ✅ Budget
]
```

**Problem:** Keine Titel = User weiß nicht, worum es geht!

---

### Phase 2: MVP + OCDS für Titel (BESSER)

```python
# 1. Import CSV (schnell)
import_csv_to_database()

# 2. Download OCDS JSON
download_ocds_daily()

# 3. Parse OCDS für Titel
for tender in parse_ocds_json():
    db.execute("""
        UPDATE notices 
        SET title = ?, description = ?
        WHERE notice_identifier = ?
    """, [tender['title'], tender['description'], tender['id']])

# Jetzt funktioniert ALLES:
# ✅ Filter (CPV, Region, Budget)
# ✅ Titel anzeigen
# ✅ Beschreibung anzeigen
# ✅ Volltext-Suche möglich
```

---

## 🚀 Konkrete Umsetzung

### Script 1: CSV Import (5 Minuten)

```bash
# Täglich ausführen
python import_csv_to_database.py --date 2024-12-30

# Erstellt:
# ✅ notices (300 Zeilen)
# ✅ classifications (700 Zeilen)
# ✅ organisations (800 Zeilen)
# ✅ ... (alle Tabellen)
```

### Script 2: OCDS Import (10 Minuten)

```bash
# Täglich nach CSV-Import
python import_ocds_titles.py --date 2024-12-30

# Updated:
# ✅ notices.title
# ✅ notices.description
# ✅ lots.lot_title
```

### Script 3: Suchindex aufbauen (2 Minuten)

```bash
# Nach Import
python rebuild_search_index.py

# Erstellt:
# ✅ searchable_tenders (denormalisiert)
# ✅ FULLTEXT Indizes
```

---

## 📈 Performance-Überlegungen

### Suchgeschwindigkeit:

**Option A: Direkte Joins (langsam)**
```sql
-- 8 Table Joins für jede Suche!
SELECT n.*, c.cpv, o.buyer_name, s.deadline
FROM notices n
JOIN classifications c ON ...
JOIN organisations o ON ...
JOIN submission_terms s ON ...
WHERE ...
```
⏱️ **~500ms** pro Suche bei 270k Notices

**Option B: searchable_tenders (schnell)**
```sql
-- Denormalisierte Tabelle, keine Joins!
SELECT * FROM searchable_tenders
WHERE cpv_codes LIKE '%72%'
  AND buyer_region = 'DE212'
  AND deadline > NOW()
```
⏱️ **~50ms** pro Suche

**Empfehlung:** `searchable_tenders` täglich nach Import neu berechnen

---

## 📦 Dateien zur Umsetzung

Ich habe erstellt:

1. **vergaberadar_schema.sql**
   - Komplette CREATE TABLE Statements
   - Indizes für Performance
   - Beispiel-Queries

2. **vergaberadar_database_structure.md**
   - ER-Diagramm
   - Tabellenübersicht
   - Detaillierte Dokumentation

3. **extract_titles_from_ocds.py**
   - OCDS JSON Download
   - Titel/Beschreibung Extraktion
   - Vollständiges Beispiel

4. **analyze_vergabe_data.py**
   - CSV-Analyse
   - Statistiken
   - Datenqualitäts-Check

---

## ✅ Fazit

**JA, wir können eine vollständige Datenbank bauen!**

**Empfohlener Ansatz:**
```
CSV-Daten (täglich)
    ↓
Datenbank Import
    ↓
OCDS-Daten (täglich)
    ↓
Titel/Beschreibung nachladen
    ↓
searchable_tenders berechnen
    ↓
VergabeRadar API
    ↓
React Frontend
```

**Zeitaufwand:**
- CSV Import: ~5 Min/Tag
- OCDS Import: ~10 Min/Tag
- Suchindex: ~2 Min/Tag
- **Gesamt: ~17 Min/Tag automatisiert**

**Speicherbedarf:**
- PostgreSQL/MySQL: ~2 GB
- Mit Volltext: ~3 GB
- Backups: +2 GB

**Kosten (Azure):**
- Azure SQL: ~€50-100/Monat
- Storage: ~€5/Monat
- **Gesamt: ~€55-105/Monat**

---

## 🎯 Nächster Schritt

Sollen wir:
1. ✅ Ein vollständiges Import-Script schreiben?
2. ✅ OCDS-Parsing testen?
3. ✅ Datenbank auf Azure SQL aufsetzen?
4. ✅ VergabeRadar MVP bauen?

**Du entscheidest!** 🚀
