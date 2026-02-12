# VergabeRadar - Projekt Status (FINAL)

## ✅ FERTIG

### API & Datenquelle
- ✅ **öffentlichevergabe.de API** identifiziert & validiert
- ✅ **CSV-Format** analysiert (19 Tabellen dokumentiert, 9 verfügbar)
- ✅ **purpose.csv** gefunden → **Titel & Beschreibung vorhanden!**
- ✅ Swagger API validiert → Code ist korrekt
- ✅ Diskrepanzen dokumentiert → Lösung entwickelt

### Datenbank-Design
- ✅ **Relationales Schema** (10 Tabellen)
- ✅ **ER-Diagramm** erstellt
- ✅ **SQL Schema** geschrieben (vergaberadar_complete_schema.sql)
- ✅ **searchable_tenders** View für schnelle Suche
- ✅ **LEFT JOIN Strategie** für optionale Tabellen

### Import-Scripts
- ✅ **CSV Download Script** funktioniert
- ✅ **CSV Parsing** erfolgreich getestet
- ✅ **Robuster Import v2.0** mit Optional-Handling
- ✅ **Error-Handling** implementiert

### Datenanalyse
- ✅ **702 Ausschreibungen** analysiert (30.12.2024)
- ✅ **18.9% IT-relevant** (CPV 30/48/72/79)
- ✅ **300 Auftraggeber** aus 68 Regionen
- ✅ **100% Titel vorhanden, 99.7% Beschreibung**

---

## 📋 OFFENE AUFGABEN

### Phase 1: Datenbank Setup (2-3 Stunden)
- [ ] Azure SQL Database erstellen
- [ ] Schema importieren (SQL ausführen)
- [ ] Import-Script auf Server deployen
- [ ] Täglichen Cron-Job einrichten

### Phase 2: Daten Import (1 Stunde)
- [ ] Historische Daten laden (seit 2022-12)
- [ ] Erste Test-Daten importieren
- [ ] searchable_tenders View testen

### Phase 3: Backend API (1-2 Tage)
- [ ] FastAPI oder Django REST aufsetzen
- [ ] Endpoints implementieren:
  - `/api/search` (Suche + Filter)
  - `/api/tenders/{id}` (Details)
  - `/api/stats` (Statistiken)
- [ ] **AI Relevanz-Scoring implementieren**
- [ ] **Budget-Extraktion aus Beschreibungstext** (siehe unten)

### Phase 4: Frontend (2-3 Tage)
- [ ] React App erstellen
- [ ] Suchmaske mit Filtern
- [ ] Ausschreibungs-Liste
- [ ] Detail-Ansicht
- [ ] User-Profile & Alerts

### Phase 5: Features (optional)
- [ ] Email-Alerts System
- [ ] User Authentication
- [ ] Saved Searches
- [ ] Export-Funktionen

---

## 🎯 MVP SCOPE

**Was definitiv drin ist:**
- ✅ Suche nach Titel/Beschreibung
- ✅ Filter: CPV, Region, Auftraggeber, Auftragsart
- ✅ Sortierung nach Datum
- ✅ Vollständige Ausschreibungsdetails

**Was teilweise drin ist:**
- ⚠️ Budget-Filter (nur ~50% haben Werte)
- ⚠️ Deadline-Filter (nur ~9% haben Daten)

**Was später kommt:**
- ⏰ Email-Alerts
- ⏰ Saved Searches
- ⏰ AI-Matching

---

## 💡 BUDGET-EXTRAKTION (NEUE ANFORDERUNG)

### Problem:
Nur ~3.5% der Ausschreibungen haben `estimatedValue` in purpose.csv.  
Bei IT/Beratungs-Ausschreibungen wird Budget oft NICHT direkt angegeben!

### Lösung: Text-Analyse für Aufwandsangaben

**Suche in `description` nach:**
- **Manntagen** (z.B. "geschätzt 50 Manntage")
- **Personentagen** (z.B. "ca. 100 Personentage")
- **Arbeitsstunden** (z.B. "maximal 800 Stunden")

### Implementierung:

```python
import re

def extract_effort_from_description(description):
    """
    Extrahiert Aufwandsangaben aus Beschreibungstext
    
    Returns:
        dict mit {type, value, unit}
    """
    
    if not description:
        return None
    
    # Pattern für Aufwandsangaben
    patterns = [
        # "50 Manntage", "ca. 100 Manntage", "bis zu 200 Manntage"
        r'(?:ca\.?\s*|etwa\s*|bis\s+zu\s*|maximal\s*|geschätzt\s*)?(\d+(?:[.,]\d+)?)\s*Manntage?',
        
        # "100 Personentage", "geschätzt 150 Personentage"
        r'(?:ca\.?\s*|etwa\s*|bis\s+zu\s*|maximal\s*|geschätzt\s*)?(\d+(?:[.,]\d+)?)\s*Personentage?',
        
        # "500 Arbeitsstunden", "max. 1000 Stunden"
        r'(?:ca\.?\s*|etwa\s*|bis\s+zu\s*|max\.?\s*|maximal\s*|geschätzt\s*)?(\d+(?:[.,]\d+)?)\s*(?:Arbeits)?[Ss]tunden?',
        
        # "PT = 50" (manchmal als Abkürzung)
        r'PT\s*[=:]\s*(\d+)',
        
        # "MT: 100" (Manntage Abkürzung)
        r'MT\s*[=:]\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', '.'))
            
            # Bestimme Typ
            if 'Mann' in match.group(0):
                effort_type = 'manntage'
            elif 'Personen' in match.group(0):
                effort_type = 'personentage'
            elif 'Stunden' in match.group(0) or 'stunden' in match.group(0):
                effort_type = 'arbeitsstunden'
            elif 'PT' in match.group(0):
                effort_type = 'personentage'
            elif 'MT' in match.group(0):
                effort_type = 'manntage'
            else:
                effort_type = 'unbekannt'
            
            return {
                'type': effort_type,
                'value': value,
                'unit': effort_type,
                'text_snippet': match.group(0)
            }
    
    return None


def estimate_budget_from_effort(effort_data):
    """
    Schätzt Budget basierend auf Aufwand
    
    Annahmen:
    - 1 Manntag = 8 Stunden
    - Durchschnittlicher Tagessatz: €800 (IT-Beratung)
    - Stundensatz: €100
    """
    
    if not effort_data:
        return None
    
    effort_type = effort_data['type']
    value = effort_data['value']
    
    if effort_type in ['manntage', 'personentage']:
        # Tagessatz: €800
        estimated_budget = value * 800
        
    elif effort_type == 'arbeitsstunden':
        # Stundensatz: €100
        estimated_budget = value * 100
    
    else:
        return None
    
    return {
        'estimated_value': estimated_budget,
        'confidence': 'medium',  # Schätzung basierend auf Standardsätzen
        'source': 'text_extraction',
        'effort': effort_data
    }


# Beispiel-Nutzung:
description = """
Die geschätzten Kosten für die Dienstleistung betragen ca. 150 Manntage 
für die Implementierung und weitere 50 Personentage für Schulungen.
"""

effort = extract_effort_from_description(description)
# → {'type': 'manntage', 'value': 150, 'unit': 'manntage', ...}

budget = estimate_budget_from_effort(effort)
# → {'estimated_value': 120000, 'confidence': 'medium', ...}
```

### Datenbank-Erweiterung:

```sql
-- Neue Spalten in searchable_tenders
ALTER TABLE searchable_tenders 
ADD COLUMN extracted_effort_type VARCHAR(50);

ALTER TABLE searchable_tenders 
ADD COLUMN extracted_effort_value DECIMAL(10,2);

ALTER TABLE searchable_tenders 
ADD COLUMN estimated_budget_from_effort DECIMAL(15,2);

ALTER TABLE searchable_tenders 
ADD COLUMN budget_source VARCHAR(50);  -- 'csv_field' oder 'text_extraction'

-- Update-Query
UPDATE searchable_tenders
SET 
    extracted_effort_type = extract_effort_type(description),
    extracted_effort_value = extract_effort_value(description),
    estimated_budget_from_effort = calculate_budget_from_effort(description),
    budget_source = CASE 
        WHEN estimated_value IS NOT NULL THEN 'csv_field'
        WHEN extracted_effort_value IS NOT NULL THEN 'text_extraction'
        ELSE NULL
    END;
```

### Vollständige Budget-Logik:

```python
def get_tender_budget(tender):
    """
    Gibt Budget zurück - priorisiert verschiedene Quellen
    
    Priorität:
    1. estimated_value (aus CSV)
    2. tender_value (tatsächlicher Wert bei Results)
    3. Extrahierter Aufwand → geschätztes Budget
    """
    
    # 1. Direkter Wert aus CSV
    if tender.estimated_value:
        return {
            'value': tender.estimated_value,
            'source': 'official_estimate',
            'confidence': 'high'
        }
    
    # 2. Tatsächlicher Auftragswert (bei Results)
    if tender.tender_value:
        return {
            'value': tender.tender_value,
            'source': 'actual_contract',
            'confidence': 'high'
        }
    
    # 3. Extrahiert aus Beschreibung
    effort = extract_effort_from_description(tender.description)
    if effort:
        budget = estimate_budget_from_effort(effort)
        return budget
    
    # 4. Kein Budget verfügbar
    return {
        'value': None,
        'source': 'unknown',
        'confidence': 'none'
    }
```

### Frontend-Anzeige:

```jsx
<TenderCard>
  <h3>{tender.title}</h3>
  
  <BudgetInfo budget={tender.budget}>
    {budget.source === 'official_estimate' && (
      <span>💰 Geschätzt: {formatCurrency(budget.value)}</span>
    )}
    
    {budget.source === 'text_extraction' && (
      <span>
        💡 Geschätzt: {formatCurrency(budget.value)} 
        <small>(basierend auf {budget.effort.value} {budget.effort.type})</small>
      </span>
    )}
    
    {budget.source === 'unknown' && (
      <span>💰 Budget: Nicht angegeben</span>
    )}
  </BudgetInfo>
</TenderCard>
```

---

## 📊 ERWARTETER IMPACT

### Vorher (nur CSV-Felder):
- Budget verfügbar: ~3.5% (25 von 702)
- Nicht filterbar: ~96.5%

### Nachher (mit Text-Extraktion):
- Budget aus CSV: ~3.5%
- Budget extrahiert: ~30-50% (geschätzt für IT/Beratung)
- **GESAMT: ~35-55% haben Budget-Info!**

### Besonders relevant für:
- ✅ IT-Dienstleistungen (CPV 72)
- ✅ Beratungsleistungen (CPV 79)
- ✅ Software-Entwicklung (CPV 48)

---

## 💾 DATEIEN BEREIT

1. **vergaberadar_complete_schema.sql** → Datenbank-Schema
2. **import_csv_robust_v2.py** → Import-Script
3. **VALIDATION_REPORT_COMPLETE.md** → Technische Dokumentation
4. **CSV_FILES_COMPLETE_OVERVIEW.md** → Datenstruktur
5. **PROJECT_STATUS_FINAL.md** → Dieser Status (mit Budget-Extraktion)

---

## 📊 KENNZAHLEN

- **Datenvolumen:** ~270.000 Ausschreibungen seit 2022-12
- **Täglicher Import:** ~300 neue Ausschreibungen
- **Datenbank-Größe:** ~2-3 GB
- **Azure Kosten:** ~€15-50/Monat (SQL + Storage)

---

## 🚀 NÄCHSTE SESSION

**Priorität 1:** Datenbank aufsetzen + Import testen  
**Priorität 2:** Backend API bauen  
**Priorität 3:** Budget-Extraktion implementieren  
**Priorität 4:** Frontend-Demo

**Geschätzter Zeitbedarf bis MVP:** 1 Woche intensiv ODER 2-3 Wochen entspannt

---

**Status:** 🟢 Ready to build! Alle Vorarbeiten erledigt.

**Neue Anforderung gespeichert:** ✅ Text-Analyse für Manntage/Personentage/Arbeitsstunden
