import streamlit as st
import pandas as pd
import json
import re
import os
from datetime import datetime, timedelta
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from geopy.geocoders import Nominatim
import config

# ==========================================
# --- 1. KONFIGURATION ---
# ==========================================
# Alle Secrets kommen aus Environment-Variablen (siehe .env.example)

SEARCH_ENDPOINT = config.SEARCH_ENDPOINT
SEARCH_KEY = config.SEARCH_KEY
INDEX_NAME = config.INDEX_NAME
SEMANTIC_CONFIG = config.SEMANTIC_CONFIG
PROFILES_FILE = "saved_profiles.json"

# ==========================================
# --- 2. SETUP & VERBINDUNG ---
# ==========================================

st.set_page_config(page_title="Vergaberadar Pro", layout="wide", page_icon="📡")

# Verbindung herstellen
try:
    # Hier passiert der Zugriff auf die oben definierten Variablen
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT, 
        index_name=INDEX_NAME, 
        credential=AzureKeyCredential(SEARCH_KEY)
    )
except Exception as e:
    st.error(f"⚠️ Verbindungsfehler zu Azure Search: {e}")
    st.info("Bitte prüfen Sie, ob Sie oben im Code 'SEARCH_ENDPOINT' und 'SEARCH_KEY' korrekt ausgefüllt haben.")
    st.stop()

# ==========================================
# --- 3. HELFER-FUNKTIONEN ---
# ==========================================

def get_geo_location(postal_code):
    """Wandelt PLZ in Koordinaten um (Nominatim)."""
    geolocator = Nominatim(user_agent="vergabe_radar_app")
    try:
        # Wir fügen "Deutschland" hinzu für bessere Treffer
        location = geolocator.geocode(f"{postal_code}, Deutschland")
        return location
    except:
        return None

def load_saved_profiles():
    """Lädt Profile aus einer lokalen JSON-Datei."""
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except:
            pass
    return pd.DataFrame(columns=["profile_name", "filter_data"])

def save_search_profile(name, filter_data):
    """Speichert ein Profil in die JSON-Datei."""
    try:
        df = load_saved_profiles()
        new_entry = {"profile_name": name, "filter_data": json.dumps(filter_data)}
        
        # Wenn Name existiert, überschreiben, sonst anhängen
        if not df.empty and name in df["profile_name"].values:
            idx = df.index[df["profile_name"] == name][0]
            df.at[idx, "filter_data"] = json.dumps(filter_data)
        else:
            new_df = pd.DataFrame([new_entry])
            df = pd.concat([df, new_df], ignore_index=True)
            
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict("records"), f, indent=4)
        return True
    except Exception as e:
        return str(e)

def load_cpv_levels(level, prefix=""):
    """
    Dummy-Funktion für CPV-Kategorien.
    Da keine Datenbankverbindung besteht, simulieren wir hier die Kategorien.
    Sie können diese Listen später erweitern.
    """
    data = []
    if level == 1:
        data = [
            {"cpv_2": "45", "beschreibung_de": "Bauarbeiten"},
            {"cpv_2": "72", "beschreibung_de": "IT-Dienste & Beratung"},
            {"cpv_2": "90", "beschreibung_de": "Abwasser- & Müllbeseitigung"},
            {"cpv_2": "33", "beschreibung_de": "Medizinische Ausrüstungen"}
        ]
    elif level == 2:
        # Beispielhafte Unterkategorien
        if prefix.startswith("45"):
            data = [{"cpv_3": "452", "beschreibung_de": "Komplett- oder Teilbauleistungen"}]
        elif prefix.startswith("72"):
            data = [{"cpv_3": "722", "beschreibung_de": "Softwareentwicklung"}]
            
    return pd.DataFrame(data)

# ==========================================
# --- 4. CALLBACKS (STATE MANAGEMENT) ---
# ==========================================

def reset_all_filters():
    """Löscht alle Filter-Werte (Keys die mit 'w_' starten)."""
    for key in list(st.session_state.keys()):
        if key.startswith("w_"):
            del st.session_state[key]
    if "profile_selector" in st.session_state:
        st.session_state.profile_selector = "Neu / Auswählen"

def apply_profile_callback():
    """Lädt gespeicherte Werte in den State."""
    selection = st.session_state.profile_selector
    if selection != "Neu / Auswählen":
        profiles = load_saved_profiles()
        if not profiles.empty:
            row = profiles[profiles['profile_name'] == selection].iloc[0]
            data = json.loads(row['filter_data'])
            for k, v in data.items():
                st.session_state[k] = v

# ==========================================
# --- 5. UI STYLING ---
# ==========================================
st.markdown("""
<style>
    .tender-card { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 15px; }
    .tender-title { color: #0078d4; font-size: 1.15rem; font-weight: 600; margin-bottom: 5px; }
    .meta-row { display: flex; gap: 15px; font-size: 0.85rem; color: #666; margin-bottom: 8px; }
    .cpv-label { background-color: #f5f5f5; color: #444; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# --- 6. SIDEBAR (FILTER) ---
# ==========================================
with st.sidebar:
    st.title("📡 Radar-Steuerung")
    
    # RESET
    st.button("🔄 Alles zurücksetzen", on_click=reset_all_filters, use_container_width=True)
    st.divider()

    # PROFIL LADEN
    st.subheader("Suchprofile")
    saved_df = load_saved_profiles()
    options = ["Neu / Auswählen"] + (saved_df['profile_name'].tolist() if not saved_df.empty else [])
    st.selectbox("Profil laden", options=options, key="profile_selector", on_change=apply_profile_callback)

    # REGION
    with st.expander("📍 Region & Ort", expanded=True):
        st.text_input("PLZ (für Umkreis)", placeholder="z.B. 60311", key="w_plz")
        st.slider("Radius (km)", 5, 500, 50, key="w_radius")
        st.divider() 
        st.text_input("Stadt (Namensfilter)", placeholder="z.B. Berlin", key="w_city")

    # CPV (Vereinfacht)
    with st.expander("📂 Branchen (CPV)", expanded=True):
        cpv_prefix = ""
        df_l1 = load_cpv_levels(1)
        # Wir bauen eine Liste für das Dropdown
        l1_display = ["Alle Branchen"] + [f"{r['cpv_2']}: {r['beschreibung_de']}" for _, r in df_l1.iterrows()]
        
        sel_l1 = st.selectbox("Hauptbranche", options=l1_display, key="w_cpv_l1")
        
        if sel_l1 != "Alle Branchen":
            # Extrahiere den Code vor dem Doppelpunkt (z.B. "45" aus "45: Bauarbeiten")
            cpv_prefix = sel_l1.split(":")[0]
            
            # Hier könnte Logik für Level 2/3 folgen
            # (Wir zeigen hier exemplarisch Level 2 an)
            df_l2 = load_cpv_levels(2, cpv_prefix)
            if not df_l2.empty:
                l2_display = ["Alle Gruppen"] + [f"{r['cpv_3']}: {r['beschreibung_de']}" for _, r in df_l2.iterrows()]
                sel_l2 = st.selectbox("Spezialisierung", options=l2_display, key="w_cpv_l2")
                if sel_l2 != "Alle Gruppen":
                    cpv_prefix = sel_l2.split(":")[0]

    # ZEITRAUM
    with st.expander("📅 Zeitfilter", expanded=False):
        st.date_input("Veröffentlicht ab", value=datetime.now() - timedelta(days=365), key="w_date_von")
        st.date_input("Veröffentlicht bis", value=datetime.now(), key="w_date_bis")

    # SPEICHERN
    st.divider()
    with st.expander("💾 Filter speichern"):
        with st.form("save_form"):
            new_name = st.text_input("Name für Profil")
            if st.form_submit_button("Speichern"):
                if new_name:
                    # Speichere alle Keys, die mit w_ anfangen
                    to_save = {k: v for k, v in st.session_state.items() if k.startswith("w_")}
                    res = save_search_profile(new_name, to_save)
                    if res is True:
                        st.success("Gespeichert!")
                        # Rerun aktualisiert die Liste oben
                        st.rerun()
                    else:
                        st.error(f"Fehler: {res}")

# ==========================================
# --- 7. HAUPTBEREICH: SUCHE ---
# ==========================================
st.subheader("Ausschreibungen finden")
col_q, col_b = st.columns([5, 1])
with col_q:
    query_raw = st.text_input("Suchbegriff", placeholder="z.B. Kettensäge Elektro", key="w_query", label_visibility="collapsed")
with col_b:
    do_search = st.button("Suche 🔍", use_container_width=True)

# ==========================================
# --- 8. LOGIK: FILTER & ABFRAGE ---
# ==========================================

# Werte aus Session State lesen (Sicherer Zugriff)
plz_val = st.session_state.get("w_plz")
rad_val = st.session_state.get("w_radius", 50)
city_val = st.session_state.get("w_city")
date_von = st.session_state.get("w_date_von", datetime.now() - timedelta(days=365))
date_bis = st.session_state.get("w_date_bis", datetime.now())

# Wir starten die Suche nur, wenn wirklich etwas eingegeben wurde
should_search = query_raw or do_search or cpv_prefix or (plz_val and len(plz_val) == 5) or city_val

if should_search:
    
    filters = []
    
    # A) CPV Filter (angepasst an Index-Feld 'cpv_code_main')
    if cpv_prefix:
        # Wir nutzen OData 'search.in' oder 'startswith' Logik. 
        # Da CPV Codes Strings sind, ist ein Regex-Match auf den Anfang des Strings am sichersten für alle Tiers.
        # Syntax: cpv_code_main/any(c: search.ismatch('/^45.*/', c)) -- WENN es eine Collection wäre.
        # Da es ein einfacher String ist, nutzen wir eine Range query (sehr schnell):
        # Alle Codes, die mit "45" anfangen, sind >= "45" und < "46"
        
        # Berechne den "nächsten" String für die Range
        prefix_len = len(cpv_prefix)
        last_char = cpv_prefix[-1]
        next_char = chr(ord(last_char) + 1)
        next_prefix = cpv_prefix[:-1] + next_char
        
        filters.append(f"cpv_code_main ge '{cpv_prefix}' and cpv_code_main lt '{next_prefix}'")
    
    # B) Datum
    # Konvertierung zu ISO 8601 String
    filters.append(f"publication_date ge {date_von.isoformat()}T00:00:00Z")
    filters.append(f"publication_date le {date_bis.isoformat()}T23:59:59Z")

    # C) PLZ Umkreis
    if plz_val and len(plz_val) == 5:
        loc = get_geo_location(plz_val)
        if loc:
            # Azure Geo-Distance Filter
            filters.append(f"geo.distance(geo_location, geography'POINT({loc.longitude} {loc.latitude})') le {rad_val}")
        else:
            st.warning(f"Konnte PLZ '{plz_val}' nicht finden. Umkreissuche deaktiviert.")
    
    # D) Stadt Name
    if city_val:
        filters.append(f"search.ismatch('{city_val}*', 'buyer_city')")

    filter_string = " and ".join(filters) if filters else None

    # --- DUAL SEARCH STRATEGIE ---
    all_results = {}
    select_fields = ["id", "title", "buyer_name", "buyer_city", "document_url", "publication_date", "cpv_code_main", "description", "geo_location"]

    # 1. Wildcard Suche (Standard)
    try:
        wild_term = "*"
        if query_raw and query_raw.strip():
            # Bereinigen und Wildcards hinzufügen
            safe = re.sub(r'[^\w\säöüÄÖÜß-]', '', query_raw) # Erlaubt Buchstaben, Zahlen, Bindestrich
            if safe.strip():
                parts = safe.split()
                # Baut: term1 OR *term1* ... für maximale Trefferquote bei Teilwörtern
                # Azure Syntax: (term1 OR *term1*) AND (term2 OR *term2*)
                # Damit "Dachdecker Berlin" -> findet Dachdecker UND Berlin
                wild_parts = []
                for p in parts:
                    wild_parts.append(f"({p} OR *{p}*)")
                wild_term = " AND ".join(wild_parts)
        
        res1 = client.search(
            search_text=wild_term,
            query_type="full", # Erlaubt Wildcards und Logik
            search_mode="all", # Alle Begriffe müssen passen (AND Logik)
            filter=filter_string,
            select=select_fields,
            top=100
        )
        for d in res1: all_results[d['id']] = d
    except Exception as e:
        st.error(f"Fehler bei der Suche: {e}")

    # 2. Semantische Suche (Optionaler Fallback)
    # Nur ausführen, wenn wir Text haben und Semantic Search konfiguriert ist
    if query_raw and query_raw.strip() and SEMANTIC_CONFIG:
        try:
            res2 = client.search(
                search_text=query_raw,
                query_type="semantic",
                semantic_configuration_name=SEMANTIC_CONFIG,
                filter=filter_string,
                select=select_fields,
                top=50
            )
            for d in res2: all_results[d['id']] = d
        except:
            # Ignorieren, falls Semantic Search im Free Tier nicht aktiv ist
            pass

    # --- ERGEBNISSE ANZEIGEN ---
    final_hits = list(all_results.values())
    st.markdown(f"### **{len(final_hits)} Ergebnisse gefunden**")
    
    tab1, tab2 = st.tabs(["📋 Liste", "🗺️ Karte"])
    
    with tab1:
        if not final_hits:
            st.info("Keine Treffer mit diesen Filtern gefunden.")
        
        for doc in final_hits:
            # Datum hübsch machen
            p_date = doc.get('publication_date')
            if p_date and isinstance(p_date, str): 
                p_date = p_date[:10] # 2023-01-01T... -> 2023-01-01

            # Beschreibung kürzen
            desc = doc.get('description') or ""
            if len(desc) > 250: desc = desc[:250] + "..."

            # Karte rendern
            st.markdown(f"""
            <div class="tender-card">
                <div class="tender-title">{doc.get('title', 'Ohne Titel')}</div>
                <div class="meta-row">
                    <span>🏢 <b>{doc.get('buyer_name', 'Unbekannt')}</b></span> | 📍 {doc.get('buyer_city', 'k.A.')} | 📅 {p_date}
                </div>
                <div class="meta-row">
                    <span class="cpv-label">CPV: {doc.get('cpv_code_main', 'k.A.')}</span>
                </div>
                <div style="font-size:0.9rem; color:#444; margin-top:5px;">
                    {desc}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if doc.get('document_url'):
                st.link_button("Zum Dokument ↗️", doc['document_url'])
            st.divider()
    
    with tab2:
        # MAP LOGIK
        map_data = []
        for doc in final_hits:
            geo = doc.get("geo_location")
            # Azure GeoPoint ist: {'type': 'Point', 'coordinates': [longitude, latitude]}
            if geo and "coordinates" in geo:
                # Streamlit map braucht 'lat' und 'lon' (oder 'latitude'/'longitude')
                map_data.append({
                    "lat": geo["coordinates"][1],
                    "lon": geo["coordinates"][0],
                    "name": doc.get("title", "Ausschreibung")
                })
        
        if map_data:
            # Wir zeigen die Karte
            st.map(pd.DataFrame(map_data), zoom=5, use_container_width=True)
        else:
            st.info("Für die aktuellen Treffer liegen keine Geodaten vor.")

else:
    st.info("👈 Bitte geben Sie Suchbegriffe ein oder nutzen Sie die Filter links, um zu starten.")