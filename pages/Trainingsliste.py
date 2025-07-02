# File: pages/Trainingsliste.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import os
import sys
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import fitparse
import gpxpy
import gpxpy.gpx
import base64 # Importiere base64
import io # Importiere io für BytesIO

from tinydb import TinyDB, Query

# Stelle sicher, dass das Verzeichnis mit hilfsfunktionenedittraining.py im sys.path ist
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from hilfsfunktionenedittraining import parse_gpx_data, parse_fit_data, format_duration # Importiere die aktualisierten Funktionen
from auswertungen.ekgdata import EKGdata # Annahme: EKGdata kann mit BytesIO arbeiten oder erwartet einen Pfad, den wir simulieren können

# --- Konfiguration und Initialisierung ---
# IMAGE_DIR, DATA_DIR, UPLOAD_DIR und initialize_directories werden entfernt,
# da Dateien nicht mehr auf dem Dateisystem gespeichert werden.

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen für die Datenverarbeitung und Dateihandhabung (angepasst) ---

def load_gpx_data_for_map(gpx_base64_string):
    """
    Lädt und parst eine GPX-Datei aus einem Base64-String und gibt eine Liste von Punkten zurück.
    """
    if not gpx_base64_string:
        return None

    try:
        gpx_bytes = base64.b64decode(gpx_base64_string)
        gpx_file = io.BytesIO(gpx_bytes)
        gpx = gpxpy.parse(gpx_file)
        
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append((point.latitude, point.longitude))
        return points
    except Exception as e:
        st.error(f"Fehler beim Laden der GPX-Daten für die Karte: {e}")
        return None

def load_fit_data_for_power_curve(fit_base64_string):
    """
    Lädt und parst eine FIT-Datei aus einem Base64-String und extrahiert Leistungsdaten.
    Gibt ein Pandas DataFrame mit Zeit, Leistung (in Watt) zurück oder None bei Fehler.
    """
    if not fit_base64_string:
        return None

    try:
        fit_bytes = base64.b64decode(fit_base64_string)
        fitfile = FitFile(io.BytesIO(fit_bytes))

        power_data = []
        for record in fitfile.get_messages('record'):
            timestamp = record.get_value('timestamp')
            power = record.get_value('power') # Leistung in Watt
            if timestamp and power is not None:
                power_data.append({'timestamp': timestamp, 'power': power})
        
        if power_data:
            df = pd.DataFrame(power_data)
            df['duration_seconds'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
            return df
        return None
    except Exception as e:
        st.error(f"Fehler beim Laden der FIT-Daten für Power Curve: {e}")
        return None

def load_ekg_data(ekg_base64_string):
    """
    Lädt EKG-Daten aus einem Base64-String.
    EKGdata-Klasse müsste angepasst werden, um BytesIO oder String zu akzeptieren.
    Fürs Erste geben wir nur an, dass Daten vorhanden sind.
    """
    if not ekg_base64_string:
        return None
    try:
        ekg_bytes = base64.b64decode(ekg_base64_string)
        # Annahme: EKGdata kann direkt mit Bytes arbeiten oder hat eine Methode dafür
        # Oder Sie müssen einen temporären Dateipfad erstellen, wenn EKGdata nur Pfade akzeptiert
        # temp_ekg_path = ...
        # with open(temp_ekg_path, "wb") as f: f.write(ekg_bytes)
        # ekg_data_obj = EKGdata(temp_ekg_path)
        # os.remove(temp_ekg_path)
        
        # Für diese Implementierung gehen wir davon aus, dass EKGdata mit BytesIO arbeiten kann
        # oder dass die Visualisierung direkt aus dem Base64-String erfolgt.
        # Wenn EKGdata einen Pfad benötigt, müssten Sie eine temporäre Datei erstellen.
        
        # Beispiel: Wenn EKGdata einen Dateipfad benötigt, müssten Sie hier eine temporäre Datei erstellen
        # und diese dann an EKGdata übergeben.
        # from tempfile import NamedTemporaryFile
        # with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        #     tmp_file.write(ekg_bytes)
        #     tmp_file_path = tmp_file.name
        # ekg_data_obj = EKGdata(tmp_file_path) # Annahme: EKGdata kann so initialisiert werden
        # os.remove(tmp_file_path)
        
        # Für den Zweck der Anzeige, dass Daten vorhanden sind:
        return "EKG-Daten vorhanden und können verarbeitet werden."
    except Exception as e:
        st.error(f"Fehler beim Laden der EKG-Daten: {e}")
        return None

# --- Funktionen für die Anzeige von Trainingsdetails ---

def display_training_details(training, delete_callback, edit_callback, expanded=False):
    """
    Zeigt die Details eines einzelnen Trainings in einem expander an.
    """
    doc_id = training.doc_id
    with st.expander(f"**{training['name']}** - {training['date']} ({training['sportart']})", expanded=expanded, key=f"expander_{doc_id}"):
        st.markdown(f"**Dauer:** {format_duration(training.get('dauer', 0))}")
        st.markdown(f"**Distanz:** {training.get('distanz', 0.0):.2f} km")
        st.markdown(f"**Durchschnittlicher Puls:** {training.get('puls', 0)} bpm")
        st.markdown(f"**Kalorien:** {training.get('kalorien', 0)} kcal")
        st.markdown(f"**Anstrengung:** {training.get('anstrengung', 'N/A')}")
        st.markdown(f"**Bewertung:** {'⭐' * training.get('star_rating', 0)}")
        st.markdown(f"**Beschreibung:** {training.get('description', 'Keine Beschreibung.')}")
        st.markdown(f"**Durchschnittsgeschwindigkeit:** {training.get('avg_speed_kmh', 0.0):.2f} km/h")
        st.markdown(f"**Höhenmeter aufwärts:** {training.get('elevation_gain_pos', 0)} m")
        st.markdown(f"**Höhenmeter abwärts:** {training.get('elevation_gain_neg', 0)} m")

        # Anzeige des Bildes (wenn Base64 vorhanden)
        image_base64 = training.get('image')
        if image_base64:
            try:
                st.image(base64.b64decode(image_base64), caption=f"Bild von {training['name']}", use_column_width=True)
            except Exception as e:
                st.warning(f"Fehler beim Anzeigen des Bildes: {e}")

        # Anzeige der GPX-Karte (wenn Base64 vorhanden)
        gpx_base64 = training.get('gpx_file')
        if gpx_base64:
            st.subheader("GPX-Track")
            gpx_points = load_gpx_data_for_map(gpx_base64)
            if gpx_points:
                # Erstelle eine Karte mit Folium
                m = folium.Map(location=[gpx_points[0][0], gpx_points[0][1]], zoom_start=13)
                folium.PolyLine(gpx_points, color="red", weight=2.5, opacity=1).add_to(m)
                folium_static(m, width=700, height=500)
            else:
                st.info("Keine gültigen GPX-Daten für die Karte gefunden.")

        # Anzeige von EKG-Daten (wenn Base64 vorhanden)
        ekg_base64 = training.get('ekg_file')
        if ekg_base64:
            st.subheader("EKG-Daten")
            ekg_info = load_ekg_data(ekg_base64)
            if ekg_info:
                st.write(ekg_info) # Oder hier eine Visualisierung einbinden
            else:
                st.info("Keine EKG-Daten verfügbar oder Fehler beim Laden.")

        # Anzeige von FIT-Daten (wenn Base64 vorhanden)
        fit_base64 = training.get('fit_file')
        if fit_base64:
            st.subheader("FIT-Daten")
            fit_df = load_fit_data_for_power_curve(fit_base64)
            if fit_df is not None and not fit_df.empty:
                st.write("Leistungsdaten aus FIT-Datei:")
                st.dataframe(fit_df.head()) # Zeige die ersten Zeilen der Daten
                
                # Beispielplot für Leistung über Zeit
                fig_power = px.line(fit_df, x='duration_seconds', y='power', title='Leistung über Zeit')
                st.plotly_chart(fig_power, use_container_width=True)
            else:
                st.info("Keine Leistungsdaten in der FIT-Datei gefunden.")

        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("Bearbeiten", key=f"edit_btn_{doc_id}"):
                edit_callback(doc_id)
        with col_delete:
            if st.button("Löschen", key=f"delete_btn_{doc_id}"):
                delete_callback(doc_id)

# --- Datenbank-Operationen ---

def get_trainings_for_current_user():
    """
    Lädt die Trainings für die aktuell ausgewählte Person aus der TinyDB.
    """
    if "current_user_id" not in st.session_state:
        return []
    
    person_doc_id = int(st.session_state["current_user_id"])
    person_data = dp.get(doc_id=person_doc_id)

    if person_data and 'ekg_tests' in person_data:
        ekg_test_ids = person_data['ekg_tests']
        all_trainings = db.all()
        # Stellen Sie sicher, dass doc_id in den Trainingsdaten vorhanden ist, bevor Sie darauf zugreifen
        user_trainings = [t for t in all_trainings if hasattr(t, 'doc_id') and t.doc_id in ekg_test_ids]
        return user_trainings
    return []

def delete_training_from_db(doc_id):
    """Löscht ein Training aus der dbtests-Datenbank und entfernt die Verknüpfung zur Person."""
    try:
        # Zuerst aus dbtests löschen
        db.remove(doc_ids=[doc_id])
        st.success(f"Training mit ID {doc_id} erfolgreich gelöscht.")

        # Dann die Verknüpfung aus dbperson entfernen
        person_doc_id = st.session_state.get("current_user_id")
        if person_doc_id:
            person_data = dp.get(doc_id=int(person_doc_id))
            if person_data and 'ekg_tests' in person_data:
                current_ekg_tests = person_data['ekg_tests']
                if doc_id in current_ekg_tests:
                    current_ekg_tests.remove(doc_id)
                    dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_doc_id)])
                    st.info(f"Verknüpfung zu Training {doc_id} von Person {person_doc_id} entfernt.")
        st.rerun() # Seite neu laden, um die gelöschte Liste anzuzeigen
    except Exception as e:
        st.error(f"Fehler beim Löschen des Trainings: {e}")

def set_training_to_edit(doc_id):
    """Setzt die Session State Variable, um den Bearbeitungsmodus zu aktivieren."""
    st.session_state['editing_training_id'] = doc_id
    st.switch_page("pages/add workout.py") # Wechsel zur "Workout hinzufügen"-Seite

# --- Hauptanwendung ---
def main():
    st.title("Dein Trainings-Tagebuch 🏋️‍♂️")
    st.markdown("---")

    # initialize_directories() wird nicht mehr benötigt

    if "current_user_id" not in st.session_state:
        st.info("Bitte warten")
        return

    if 'editing_training_id' not in st.session_state:
        st.session_state['editing_training_id'] = None
    
    # Lade alle Trainings für den aktuellen Benutzer
    all_user_trainings = get_trainings_for_current_user()

    if not all_user_trainings:
        st.info("Du hast noch keine Trainings hinzugefügt. Füge jetzt dein erstes Workout hinzu!")
    else:
        st.subheader("Deine Workouts:")
        # Sortiere die Trainings nach Datum absteigend
        all_user_trainings.sort(key=lambda x: datetime.strptime(x.get('date', '1900-01-01'), '%Y-%m-%d'), reverse=True)

        # Überprüfe, ob ein Training gerade hinzugefügt/bearbeitet wurde und erweitere es
        # Dies ist nützlich, um das zuletzt hinzugefügte/bearbeitete Training sofort anzuzeigen
        if 'initial_expand_done' not in st.session_state:
            st.session_state.initial_expand_done = False

        if not st.session_state.initial_expand_done and all_user_trainings:
            # Erweitere das erste Training in der Liste (das neueste, da sortiert)
            display_training_details(all_user_trainings[0], delete_training_from_db, set_training_to_edit, expanded=True)
            st.session_state.initial_expand_done = True
            # Zeige den Rest der Trainings an
            for i, training in enumerate(all_user_trainings[1:]):
                display_training_details(training, delete_training_from_db, set_training_to_edit)
        else:
            for training in all_user_trainings:
                display_training_details(training, delete_training_from_db, set_training_to_edit)

# Dies ist, wie Streamlit die Seite ausführt, wenn sie ausgewählt wird
if __name__ == "__main__":
    main()
