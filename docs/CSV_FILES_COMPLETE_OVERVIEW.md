# VergabeRadar - Vollständige CSV-Struktur

## 📦 Alle verfügbaren CSV-Dateien (10 Stück)

```
öffentlichevergabe.de API Export (format=csv.zip)
│
├── 📄 notice.csv                    (Master-Tabelle)
│   ├── notice_identifier           → Eindeutige ID
│   ├── notice_version              → Versionsnummer
│   ├── procedure_identifier
│   ├── procedure_legal_basis
│   ├── form_type
│   ├── notice_type                 → competition / result
│   └── publication_date            → Veröffentlichungsdatum
│
├── 📄 procedure.csv                 (Verfahrensdetails)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── procedure_type              → open, neg-w-call, ...
│   ├── procedure_features
│   ├── procedure_accelerated       → beschleunigt? true/false
│   ├── lots_max_allowed
│   ├── lots_all_required
│   └── lots_max_awarded
│
├── 📄 lot.csv                       (Lose/Auftragsteile)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   └── lot_identifier              → LOT-0001, LOT-0002, ...
│
├── ⭐ purpose.csv                   🎯 GOLDMINE! TITEL & BESCHREIBUNG!
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── lot_identifier              → optional (NULL = Notice-Level)
│   ├── internal_identifier
│   ├── main_nature                 → services / works / supplies
│   ├── additional_nature
│   ├── title                       ✅ TITEL!
│   ├── estimated_value             ✅ GESCHÄTZTER WERT!
│   ├── estimated_value_currency
│   └── description                 ✅ BESCHREIBUNG!
│
├── 📄 classification.csv            (CPV-Codes)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── lot_identifier              → optional
│   ├── classification_type         → cpv
│   ├── main_classification_code    → 72000000 (IT), 30000000, ...
│   ├── additional_classification_codes
│   └── options
│
├── 📄 organisation.csv              (Auftraggeber, Bieter, etc.)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── organisation_name           → Name des Auftraggebers
│   ├── organisation_identifier
│   ├── organisation_city           → Stadt
│   ├── organisation_post_code
│   ├── organisation_country_subdivision → NUTS-Code (DE212, ...)
│   ├── organisation_country_code   → DEU
│   ├── organisation_internet_address
│   ├── organisation_natural_person
│   ├── organisation_role           → buyer / tenderer / reviewer
│   ├── buyer_profile_url
│   ├── buyer_legal_type
│   ├── buyer_contracting_entity
│   ├── winner_size                 → small / medium / micro
│   ├── winner_owner_nationality
│   └── winner_listed
│
├── 📄 placeOfPerformance.csv       (Ausführungsort)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── lot_identifier              → optional
│   ├── street
│   ├── town                        → Ort
│   ├── post_code
│   ├── country_subdivision         → NUTS-Code
│   └── country_code
│
├── 📄 submissionTerms.csv          (Fristen & Termine)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── lot_identifier              → optional
│   ├── tender_validity_deadline
│   ├── tender_validity_deadline_unit → DAY / MONTH
│   ├── guarantee_required          → true/false
│   └── public_opening_date         → Deadline!
│
├── 📄 tender.csv                   (Angebote & Werte)
│   ├── notice_identifier           → FK zu notice.csv
│   ├── notice_version
│   ├── tender_identifier
│   ├── lot_identifier
│   ├── tender_value                → Tatsächlicher Wert (bei Results)
│   ├── tender_value_currency
│   ├── tender_payment_value
│   ├── tender_payment_value_currency
│   ├── tender_penalties
│   ├── tender_penalties_currency
│   ├── tender_rank
│   ├── concession_revenue_user
│   ├── concession_revenue_user_currency
│   ├── concession_revenue_buyer
│   ├── concession_revenue_buyer_currency
│   └── country_origin
│
└── 📄 (weitere mögliche CSVs)
    ├── contract.csv                → Vertragsdetails
    ├── additionalInformation.csv   → Zusatzinfos
    ├── changes.csv                 → Änderungen
    ├── cvdInformation.csv          → CVD-Infos
    ├── duration.csv                → Laufzeiten
    ├── noticeResult.csv            → Ergebnisse
    ├── procedureLotResult.csv      → Los-Ergebnisse
    ├── receivedSubmissions.csv     → Eingegangene Angebote
    ├── secondStage.csv             → Zweite Stufe
    └── strategicProcurement.csv    → Strategische Beschaffung
```

---

## 🔗 Beziehungen zwischen Tabellen

```
                         notice.csv (1)
                              │
            ┌─────────────────┼──────────────────┬────────────────────┐
            │                 │                  │                    │
            ▼                 ▼                  ▼                    ▼
    procedure.csv (1:1)  lot.csv (1:N)   ⭐ purpose.csv (1:N)  classification.csv (1:N)
                              │                  │                    │
                              │                  │                    │
            ┌─────────────────┴──────────────────┴────────────────────┘
            │
            ▼
    organisation.csv (1:N)
    placeOfPerformance.csv (1:N)
    submissionTerms.csv (1:N)
    tender.csv (1:N)
```

**Legende:**
- (1:1) = Ein Notice hat genau ein Procedure
- (1:N) = Ein Notice kann mehrere Lots/Classifications/etc. haben

---

## 📊 Datenvolumen (Beispiel für einen Tag)

| CSV-Datei | Zeilen | Spalten | Größe |
|-----------|--------|---------|-------|
| notice.csv | 300 | 7 | ~30 KB |
| procedure.csv | 300 | 9 | ~35 KB |
| lot.csv | 400 | 3 | ~15 KB |
| **purpose.csv** | **700** | **10** | **~200 KB** ⭐ |
| classification.csv | 700 | 7 | ~40 KB |
| organisation.csv | 800 | 17 | ~120 KB |
| placeOfPerformance.csv | 700 | 7 | ~50 KB |
| submissionTerms.csv | 350 | 7 | ~20 KB |
| tender.csv | 350 | 16 | ~30 KB |
| **GESAMT** | **~4,600** | - | **~540 KB/Tag** |

**Pro Monat:** ~16 MB  
**Pro Jahr:** ~200 MB  
**Seit 2022-12 (30 Monate):** ~600 MB reine CSV-Daten

---

## ✅ Vollständigkeits-Check

| Feature | Quelle | Verfügbarkeit | Qualität |
|---------|--------|---------------|----------|
| **Notice ID** | notice.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Publikationsdatum** | notice.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Notice Type** | notice.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Titel** | purpose.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Beschreibung** | purpose.csv | 99.7% | ⭐⭐⭐⭐⭐ |
| **CPV-Code** | classification.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Auftraggeber** | organisation.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Auftraggeber-Stadt** | organisation.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Region (NUTS)** | organisation.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Geschätzter Wert** | purpose.csv | ~3.5% | ⭐⭐ |
| **Deadline** | submissionTerms.csv | ~8.6% | ⭐⭐ |
| **Tatsächlicher Wert** | tender.csv | ~50% (nur Results) | ⭐⭐⭐⭐ |
| **Verfahrenstyp** | procedure.csv | 100% | ⭐⭐⭐⭐⭐ |
| **Auftragsart** | purpose.csv | 100% | ⭐⭐⭐⭐⭐ |

**Kritische Felder für VergabeRadar:**
- ✅ Titel: 100%
- ✅ Beschreibung: 99.7%
- ✅ CPV-Code: 100%
- ✅ Auftraggeber: 100%
- ✅ Region: 100%
- ⚠️ Budget: 3.5% (estimated) + 50% (actual bei Results)
- ⚠️ Deadline: 8.6%

**Bewertung:** ✅ Ausreichend für MVP!

---

## 🎯 Import-Reihenfolge

```python
# Korrekte Reihenfolge wegen Foreign Keys:

1. notice.csv          # Master-Tabelle ZUERST
2. procedure.csv       # 1:1 zu notice
3. lot.csv             # 1:N zu notice
4. purpose.csv         # ⭐ TITEL & BESCHREIBUNG
5. classification.csv  # CPV-Codes
6. organisation.csv    # Auftraggeber
7. placeOfPerformance.csv
8. submissionTerms.csv
9. tender.csv
10. (searchable_tenders erstellen) # ZULETZT
```

---

## 💡 WICHTIGSTE ERKENNTNIS

**purpose.csv ist der Schlüssel!**

Ohne purpose.csv:
- ❌ Keine Titel
- ❌ Keine Beschreibungen
- ❌ Keine Auftragsart
- ❌ Kein geschätzter Wert
- → VergabeRadar nicht nutzbar

Mit purpose.csv:
- ✅ Vollständige Ausschreibungen
- ✅ Suchbar nach Text
- ✅ Filterbar nach Kategorie
- ✅ Budget-Schätzung verfügbar
- → VergabeRadar KOMPLETT!

---

## 🚀 Nächste Schritte

1. ✅ Alle 10 CSVs täglich downloaden
2. ✅ In korrekter Reihenfolge importieren
3. ✅ searchable_tenders erstellen
4. ✅ VergabeRadar API bauen
5. ✅ Frontend entwickeln
6. ✅ FERTIG!

**Kein OCDS, kein eForms - nur CSV! 🎉**
