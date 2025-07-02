import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import fitparse
import os
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64 # Importiere base64
import io # Importiere io für BytesIO

from tinydb import TinyDB, Query

# Stelle sicher, dass das Verzeichnis mit hilfsfunktionenedittraining.py im sys.path ist
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from hilfsfunktionenedittraining import parse_fit_data # Importiere die aktualisierte Funktion

# --- Konfiguration und Initialisierung ---
# DATA_DIR, UPLOAD_DIR und initialize_directories werden entfernt,
# da Dateien nicht mehr auf dem Dateisystem gespeichert werden.

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen (aus Trainingsliste.py übernommen oder angepasst) ---

def load_fit_data(fit_base64_string):
    """
    Lädt und parst eine FIT-Datei aus einem Base64-String und extrahiert relevante Daten.
    Handhabt fehlende Felder, indem sie None setzt.
    Gibt ein Pandas DataFrame mit Zeit, Herzfrequenz, Leistung, Lat/Lon usw. zurück oder None bei Fehler.
    """
    if not fit_base64_string:
        return None
    try:
        fit_bytes = base64.b64decode(fit_base64_string)
        fitfile = FitFile(io.BytesIO(fit_bytes))

        data = []
        for record in fitfile.get_messages('record'):
            row = {'timestamp': record.get_value('timestamp')}
            # Fügen Sie alle gewünschten Felder hinzu
            for field_name in ['heart_rate', 'power', 'speed', 'distance', 'altitude', 'cadence']:
                row[field_name] = record.get_value(field_name)
            data.append(row)
        
        if data:
            df = pd.DataFrame(data)
            # Konvertiere Zeitstempel in datetime-Objekte und berechne Dauer in Sekunden
            if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['duration_seconds'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
            return df
        return None
    except Exception as e:
        st.error(f"Fehler beim Laden der FIT-Daten: {e}")
        return None

@st.cache_data(show_spinner="Lade Trainingsdaten...")
def get_trainings_for_dashboard(person_doc_id):
    """
    Lädt alle relevanten Trainingsdaten für das Dashboard.
    """
    person_data = dp.get(doc_id=int(person_doc_id))
    if person_data and 'ekg_tests' in person_data:
        ekg_test_ids = person_data['ekg_tests']
        all_trainings = db.all()
        user_trainings = [t for t in all_trainings if hasattr(t, 'doc_id') and t.doc_id in ekg_test_ids]
        return user_trainings
    return []

def calculate_accumulated_power_curve(all_power_data_df):
    """
    Berechnet die kumulierte Power Curve aus einem DataFrame mit Power-Daten.
    """
    if all_power_data_df.empty:
        return pd.DataFrame()

    # Sicherstellen, dass 'power' numerisch ist
    all_power_data_df['power'] = pd.to_numeric(all_power_data_df['power'], errors='coerce').fillna(0)

    # Sortiere nach Leistung absteigend, um die höchsten Leistungen für jede Dauer zu finden
    all_power_data_df = all_power_data_df.sort_values(by='power', ascending=False)

    # Berechne die rollierende Durchschnittsleistung für verschiedene Intervalle
    durations = [1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600] # Sekunden
    power_curve_data = []

    for duration in durations:
        # Berechne den rollierenden Durchschnitt nur, wenn genügend Datenpunkte vorhanden sind
        if len(all_power_data_df) >= duration:
            rolling_avg_power = all_power_data_df['power'].rolling(window=duration, min_periods=1).mean().max()
            power_curve_data.append({'duration_seconds': duration, 'max_avg_power': rolling_avg_power})
    
    return pd.DataFrame(power_curve_data)

def plot_power_curve(power_curve_df):
    """
    Plottet die Power Curve.
    """
    if power_curve_df.empty:
        return go.Figure()

    fig = px.line(power_curve_df, 
                  x='duration_seconds', 
                  y='max_avg_power', 
                  log_x=True, # Logarithmische Skala für Dauer
                  title='Akkumulierte Power Curve',
                  labels={'duration_seconds': 'Dauer (Sekunden, log-Skala)', 'max_avg_power': 'Maximale Durchschnittsleistung (Watt)'},
                  markers=True)
    fig.update_layout(hovermode="x unified")
    return fig

# --- Hauptanwendung ---
def main():
    st.title("Dashboard 📊")
    st.markdown("---")

    # initialize_directories() wird nicht mehr benötigt

    current_user_id = st.session_state.get("person_doc_id")
    current_user_name = st.session_state.get("profile_to_see_name", st.session_state.get("name", "Dein"))

    if not current_user_id:
        st.info("Bitte melden Sie sich an, um das Dashboard anzuzeigen.")
        return

    st.markdown(f"### {current_user_name} Trainingsübersicht")

    trainings = get_trainings_for_dashboard(current_user_id)

    if not trainings:
        st.info("Noch keine Trainingsdaten zum Anzeigen im Dashboard vorhanden.")
        return

    # Konvertiere Trainingsdaten in ein DataFrame für einfache Analyse
    # Filtern Sie die Base64-Felder heraus, da sie nicht direkt in den DataFrame gehören
    filtered_trainings = []
    for t in trainings:
        temp_t = {k: v for k, v in t.items() if k not in ['image', 'gpx_file', 'ekg_file', 'fit_file']}
        filtered_trainings.append(temp_t)

    df_trainings = pd.DataFrame(filtered_trainings)
    df_trainings['date'] = pd.to_datetime(df_trainings['date'])

    st.subheader("Trainingsstatistiken")
    col1, col2, col3 = st.columns(3)

    with col1:
        total_distance = df_trainings['distanz'].sum()
        st.metric(label="Gesamtdistanz", value=f"{total_distance:.2f} km")
    with col2:
        total_duration_minutes = df_trainings['dauer'].sum()
        st.metric(label="Gesamtdauer", value=format_duration(total_duration_minutes))
    with col3:
        avg_pulse = df_trainings['puls'].mean()
        st.metric(label="Durchschnittlicher Puls", value=f"{avg_pulse:.0f} bpm")

    st.markdown("---")

    st.subheader("Distanzentwicklung über Zeit")
    fig_distance = px.line(df_trainings.sort_values('date'), x='date', y='distanz', title='Distanz pro Training')
    st.plotly_chart(fig_distance, use_container_width=True)

    st.subheader("Verteilung der Sportarten")
    sportart_counts = df_trainings['sportart'].value_counts().reset_index()
    sportart_counts.columns = ['Sportart', 'Anzahl']
    fig_sportart = px.pie(sportart_counts, values='Anzahl', names='Sportart', title='Verteilung der Sportarten')
    st.plotly_chart(fig_sportart, use_container_width=True)

    st.subheader("Anstrengung und Bewertung")
    col_anstrengung, col_rating = st.columns(2)
    with col_anstrengung:
        anstrengung_counts = df_trainings['anstrengung'].value_counts().reset_index()
        anstrengung_counts.columns = ['Anstrengung', 'Anzahl']
        fig_anstrengung = px.bar(anstrengung_counts, x='Anstrengung', y='Anzahl', title='Verteilung der Anstrengung')
        st.plotly_chart(fig_anstrengung, use_container_width=True)
    with col_rating:
        star_rating_counts = df_trainings['star_rating'].value_counts().sort_index().reset_index()
        star_rating_counts.columns = ['Sterne', 'Anzahl']
        fig_rating = px.bar(star_rating_counts, x='Sterne', y='Anzahl', title='Verteilung der Sternebewertung')
        st.plotly_chart(fig_rating, use_container_width=True)

    st.markdown("---")
    st.subheader("Höhenmeter Analyse")

    total_elevation_gain_pos = df_trainings['elevation_gain_pos'].sum()
    total_elevation_gain_neg = df_trainings['elevation_gain_neg'].sum()

    col_elev1, col_elev2 = st.columns(2)
    with col_elev1:
        st.metric(label="Gesamte Höhenmeter aufwärts", value=f"{total_elevation_gain_pos} m")
    with col_elev2:
        st.metric(label="Gesamte Höhenmeter abwärts", value=f"{total_elevation_gain_neg} m")
    
    st.info("Diese Werte basieren auf den aus GPX/FIT-Dateien extrahierten Höhenmetern, oder manuell eingegebenen Werten.")

    st.markdown("---")
    ### Akkumulierte Power Curve (aus allen FIT-Dateien)

    # Sammle alle Leistungsdaten aus allen FIT-Dateien
    all_power_data = pd.DataFrame()
    for training in trainings:
        fit_base64 = training.get('fit_file')
        if fit_base64:
            fit_df = load_fit_data(fit_base64)
            if fit_df is not None and 'power' in fit_df.columns and 'duration_seconds' in fit_df.columns:
                all_power_data = pd.concat([all_power_data, fit_df[['duration_seconds', 'power']]], ignore_index=True)

    @st.cache_data(show_spinner="Erstelle Power Curve...")
    def get_cached_power_curve(all_power_data_df_for_hash):
        return calculate_accumulated_power_curve(all_power_data_df_for_hash)

    # all_power_data ist bereits das Ergebnis aus dem ersten Cache, wenn es von load_fit_data kommt
    accumulated_pc_df = get_cached_power_curve(all_power_data) 

    if not accumulated_pc_df.empty:
        # plot_power_curve ist nicht rechenintensiv, daher muss es nicht gecached werden
        fig_power_curve = plot_power_curve(accumulated_pc_df)
        st.plotly_chart(fig_power_curve, use_container_width=True)
    else:
        st.info("Nicht genügend Leistungsdaten in den FIT-Dateien gefunden, um eine Power Curve zu erstellen.")

    st.markdown("---")
    ### Weitere Metriken (Platzhalter)

    col_dummy1, col_dummy2 = st.columns(2)
    with col_dummy1:
        st.metric(label="Durchschnittliche Trittfrequenz (Dummy)", value="N/A") # Platzhalter
    with col_dummy2:
        st.metric(label="Durchschnittliche Watt (Dummy)", value="N/A") # Platzhalter

# Dies ist, wie Streamlit die Seite ausführt, wenn sie ausgewählt wird
if __name__ == "__main__":
    main()
