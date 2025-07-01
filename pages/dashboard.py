
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import fitparse
import os
from tinydb import TinyDB, Query
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- Konfiguration und Initialisierung (falls nicht bereits global in main.py) ---
DATA_DIR = "data"
UPLOAD_DIR = "uploaded_files"

def initialize_directories():
    """Stellt sicher, dass notwendige Verzeichnisse existieren."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen (aus Trainingsliste.py übernommen oder angepasst) ---

def load_fit_data(fit_filepath):
    """
    Lädt und parst eine FIT-Datei und extrahiert relevante Daten.
    Handhabt fehlende Felder, indem sie None setzt.
    Gibt ein Pandas DataFrame mit Zeit, Herzfrequenz, Leistung, Lat/Lon usw. zurück oder None bei Fehler.
    """
    abs_filepath = fit_filepath
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    try:
        fitfile = fitparse.FitFile(abs_filepath)

        time_data = []
        velocity_data = []
        heartrate_data = []
        distance_data = []
        cadence_data = []
        power_data = []
        latitude_data = []
        longitude_data = []

        for record in fitfile.get_messages('record'):
            record_values = {data.name: data.value for data in record}

            timestamp = record_values.get("timestamp")
            speed_val = record_values.get("speed")
            hr_val = record_values.get("heart_rate")
            dist_val = record_values.get("distance")
            cadence_val = record_values.get("cadence")
            power_val = record_values.get("power")
            
            lat_semicircles = record_values.get("position_lat")
            lon_semicircles = record_values.get("position_long")

            lat_val = lat_semicircles * (180.0 / 2**31) if lat_semicircles is not None else None
            lon_val = lon_semicircles * (180.0 / 2**31) if lon_semicircles is not None else None

            time_data.append(timestamp)
            velocity_data.append(speed_val)
            heartrate_data.append(hr_val)
            distance_data.append(dist_val)
            cadence_data.append(cadence_val)
            power_data.append(power_val)
            latitude_data.append(lat_val)
            longitude_data.append(lon_val)

        df = pd.DataFrame({
            "time": time_data,
            "velocity": velocity_data,
            "heart_rate": heartrate_data,
            "distance": distance_data,
            "cadence": cadence_data,
            "power": power_data,
            "latitude": latitude_data,
            "longitude": longitude_data
        })
        # Füllen Sie NaN-Werte vor und zurück auf
        df = df.fillna(method='ffill').fillna(method='bfill')
        return df

    except FileNotFoundError:
        return None
    except fitparse.FitParseError:
        return None
    except Exception:
        return None

def find_best_effort(df, window_size, power_col="power"):
    """Findet den besten Durchschnittswert für eine gegebene Fenstergröße."""
    if df.empty or power_col not in df.columns or df[power_col].isnull().all():
        return None
    
    if window_size > len(df): # Handle cases where window_size exceeds df length
        return None
    max_value = df[power_col].rolling(window=window_size).mean()
    # Check if max_value is empty or all NaN before taking max
    return int(max_value.max()) if not max_value.empty and not pd.isna(max_value.max()) else None

def format_time_duration(total_minutes):
    """Formatiert eine Gesamtdauer in Minuten in eine lesbare Zeichenkette (Tage, Stunden, Minuten)."""
    if total_minutes is None:
        return "N/A"
    
    total_seconds = total_minutes * 60
    
    days = int(total_seconds // (24 * 3600))
    total_seconds %= (24 * 3600)
    hours = int(total_seconds // 3600)
    total_seconds %= 3600
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    parts = []
    if days > 0:
        parts.append(f"{days} Tag{'e' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} Std.")
    if minutes > 0:
        parts.append(f"{minutes} Min.")
    if seconds > 0 and not parts: # Only show seconds if no larger units
        parts.append(f"{seconds} Sek.")
    
    return ", ".join(parts) if parts else "0 Min."

# --- Hauptfunktionen für das Dashboard ---

def get_trainings_for_current_user():
    """Lädt die Trainings für die aktuell ausgewählte Person aus der TinyDB."""
    if "person_doc_id" not in st.session_state:
        return []
    
    person_doc_id = int(st.session_state["person_doc_id"])
    person_data = dp.get(doc_id=person_doc_id)

    if person_data and 'ekg_tests' in person_data:
        ekg_test_ids = person_data['ekg_tests']
        all_trainings = db.all()
        user_trainings = [t for t in all_trainings if t.doc_id in ekg_test_ids]
        return user_trainings
    return []

def calculate_total_metrics(trainings):
    """
    Berechnet die Gesamtdistanz, Gesamtzeit, maximale Herzfrequenz
    und die gesamten Höhenmeter (positiv und negativ).
    """
    total_distance_km = 0.0
    total_duration_minutes = 0
    max_hr_measured = 0 # Höchste HR aus FIT/EKG-Dateien
    total_elevation_gain_pos = 0 # Gesamthöhenmeter aufwärts
    total_elevation_gain_neg = 0 # Gesamthöhenmeter abwärts

    all_power_data = pd.DataFrame() # Für die akkumulierte Power Curve

    for training in trainings:
        # Distanz
        try:
            distance = float(training.get('distanz', 0))
            total_distance_km += distance
        except (ValueError, TypeError):
            pass # Ignoriere ungültige Distanzwerte

        # Dauer
        try:
            duration = int(training.get('dauer', 0)) # Dauer in Minuten
            total_duration_minutes += duration
        except (ValueError, TypeError):
            pass # Ignoriere ungültige Dauerwerte

        # Höhenmeter
        try:
            # Annahme: 'elevation_gain_pos' und 'elevation_gain_neg' sind bereits in der DB gespeichert
            # durch das Parsen von GPX/FIT in add_workout.py oder Trainingsliste.py.
            # Falls sie fehlen oder ungültig sind, werden sie als 0 behandelt.
            pos_elevation = int(training.get('elevation_gain_pos', 0))
            neg_elevation = int(training.get('elevation_gain_neg', 0))
            total_elevation_gain_pos += pos_elevation
            total_elevation_gain_neg += neg_elevation
        except (ValueError, TypeError):
            pass # Ignoriere ungültige Höhenmeterwerte

        # FIT-Dateien für gemessene HR und Power
        fit_file_path = training.get('fit_file')
        if fit_file_path and os.path.exists(fit_file_path):
            fit_df = load_fit_data(fit_file_path)
            if fit_df is not None and not fit_df.empty:
                # Max gemessene HR
                if 'heart_rate' in fit_df.columns and fit_df['heart_rate'].dropna().any():
                    current_max_hr_measured = fit_df['heart_rate'].max()
                    if current_max_hr_measured > max_hr_measured:
                        max_hr_measured = int(current_max_hr_measured)
                
                # Power Daten für akkumulierte Power Curve
                if 'power' in fit_df.columns and fit_df['power'].dropna().any():
                    if 'time' in fit_df.columns and pd.api.types.is_datetime64_any_dtype(fit_df['time']):
                        fit_df_for_power = fit_df[['time', 'power']].set_index('time')
                        all_power_data = pd.concat([all_power_data, fit_df_for_power]).sort_index()
                    else:
                        st.warning(f"FIT-Datei '{os.path.basename(fit_file_path)}' hat keine gültige 'time'-Spalte für die Power Curve.")

    # Bereinige all_power_data: Entferne Duplikate im Index (falls Zeitstempel identisch sind)
    all_power_data = all_power_data[~all_power_data.index.duplicated(keep='first')]

    return total_distance_km, total_duration_minutes, max_hr_measured, all_power_data, total_elevation_gain_pos, total_elevation_gain_neg

def create_accumulated_power_curve(all_power_data_df):
    """
    Erstellt eine akkumulierte Power Curve aus allen vorhandenen Power-Daten.
    Dazu wird der höchste Power-Wert für jede Fenstergröße über alle Trainings hinweg gefunden.
    """
    if all_power_data_df.empty or 'power' not in all_power_data_df.columns or all_power_data_df['power'].isnull().all():
        return pd.DataFrame() # Leeren DataFrame zurückgeben, wenn keine Power-Daten

    window_sizes = [1, 5, 10, 30, 60, 120, 300, 600, 900, 1200, 1800, 3600] 
    
    accumulated_best_efforts = {}

    power_values = all_power_data_df['power'].dropna().reset_index(drop=True)
    
    if power_values.empty:
        return pd.DataFrame()

    for size_seconds in window_sizes:
        if size_seconds > len(power_values):
            accumulated_best_efforts[size_seconds] = None # Nicht genug Daten für dieses Fenster
            continue

        rolling_means = power_values.rolling(window=size_seconds).mean()
        
        max_power_for_window = rolling_means.max()
        
        if not pd.isna(max_power_for_window):
            accumulated_best_efforts[size_seconds] = int(max_power_for_window)
        else:
            accumulated_best_efforts[size_seconds] = None

    power_curve_df = pd.DataFrame.from_dict(accumulated_best_efforts, orient='index', columns=['BestEffort'])
    power_curve_df = power_curve_df.dropna() # Entferne Fenstergrößen ohne Daten
    
    if power_curve_df.empty:
        return pd.DataFrame()

    power_curve_df["formated_Time"] = power_curve_df.index.map(format_time_for_power_curve)
    return power_curve_df

def format_time_for_power_curve(s):
    """Formatiert Sekunden in lesbare Zeitangaben (s, m, h) für die Power Curve."""
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s//60}m"
    else:
        return f"{s//3600}h"

def plot_power_curve(power_curve_df): # <-- This function definition
    """Plottet die Power-Kurve mit Plotly."""
    if power_curve_df.empty:
        return None

    fig = px.line(
        power_curve_df,
        x="formated_Time",
        y="BestEffort",
        title="Akkumulierte Power Curve"
    )

    fig.update_layout(
        xaxis_title="Zeitfenster",
        yaxis_title="Leistung (Watt)",
        template="plotly_white",
        hovermode="x unified"
    )
    return fig

# --- Streamlit Dashboard Layout ---

def main():
    st.title("Dein Trainings-Dashboard 📊")
    st.markdown("---")

    initialize_directories()

    if "person_doc_id" not in st.session_state:
        st.info("Bitte warte")
        return

    # Initialisiere den Session State für die Anzeigeart der Höhenmeter
    if 'show_elevation_type' not in st.session_state:
        st.session_state.show_elevation_type = 'pos' # 'pos' für aufwärts, 'neg' für abwärts

    st.subheader("Übersicht der Trainingsdaten")

    trainings_for_user = get_trainings_for_current_user()

    if not trainings_for_user:
        st.info("Es sind noch keine Trainingsdaten für diese Person verfügbar. Füge Trainings hinzu!")
        if st.button("Trainings hinzufügen"):
            st.switch_page("pages/add workout.py")
        return

    # Cache die Ergebnisse von calculate_total_metrics mit st.cache_data, da sich diese nur bei neuen Trainings ändern.
    # WICHTIG: Wenn sich die Trainingsdaten in der DB ändern, musst du den Cache leeren (z.B. durch eine Schaltfläche oder Neustart der App)
    @st.cache_data(show_spinner="Berechne Metriken...")
    def get_cached_total_metrics(trainings_list_for_hash):
        # Um st.cache_data zu nutzen, benötigen wir einen hashbaren Input.
        # Wir können z.B. die doc_ids der Trainings als Tupel übergeben.
        # Oder einfach die Rohdaten der Trainings, falls sie nicht zu groß sind.
        # Hier nutzen wir eine Liste der Trainings-Dokumente.
        # Wenn sich der Inhalt eines Trainingsdokuments ändert, muss der Cache invalidiert werden.
        return calculate_total_metrics(trainings_list_for_hash)

    # Erstelle einen hashbaren "Fingerabdruck" der Trainings, um den Cache zu steuern
    # Hier verwenden wir die Liste der doc_ids, da sich der Inhalt der Trainings ändert,
    # aber die IDs bleiben gleich, es sei denn, ein Training wird hinzugefügt/gelöscht.
    # Für eine robustere Caching-Strategie müsste man ggf. einen Hash über alle relevanten Trainingsdaten bilden.
    trainings_ids_for_cache = tuple(sorted([t.doc_id for t in trainings_for_user]))

    total_distance, total_duration, max_hr_measured, all_power_data, total_elevation_gain_pos, total_elevation_gain_neg = get_cached_total_metrics(trainings_for_user)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Gesamtdistanz", value=f"{total_distance:.2f} km")
    with col2:
        st.metric(label="Gesamtzeit", value=format_time_duration(total_duration))
    with col3:
        person_doc_id = int(st.session_state["person_doc_id"])
        person_data = dp.get(doc_id=person_doc_id)
        st.session_state.max_hr_reported_cached = person_data.get('maximalpuls')
        
        st.metric(label="Max. Herzfrequenz (Angabe)", value=f"{st.session_state.max_hr_reported_cached} bpm")
    
    # Zusätzliche Metrik für die höchste gemessene Herzfrequenz
    st.markdown("---")
    st.metric(label="Max. Herzfrequenz (Gemessen aus Dateien)", value=f"{max_hr_measured} bpm" if max_hr_measured > 0 else "N/A")

    st.markdown("---")
    ### Gesamthöhenmeter

    # Funktion zum Umschalten der Höhenmeter-Anzeigeart
    def toggle_elevation_type():
        st.session_state.show_elevation_type = 'neg' if st.session_state.show_elevation_type == 'pos' else 'pos'

    # Spaltenlayout für Metrik und Button
    metric_col, button_col = st.columns([0.7, 0.3])

    with metric_col:
        if st.session_state.show_elevation_type == 'pos':
            st.metric(label="Höhenmeter aufwärts", value=f"{total_elevation_gain_pos} m")
        else:
            st.metric(label="Höhenmeter abwärts", value=f"{total_elevation_gain_neg} m")
    
    with button_col:
        st.write("") # Platzhalter für vertikale Ausrichtung
        st.write("") # Platzhalter für vertikale Ausrichtung
        if st.session_state.show_elevation_type == 'pos':
            st.button("⬇️ Abwärts anzeigen", on_click=toggle_elevation_type, key="toggle_elevation_down", help="Klicken, um die gesamten Höhenmeter abwärts anzuzeigen.")
        else:
            st.button("⬆️ Aufwärts anzeigen", on_click=toggle_elevation_type, key="toggle_elevation_up", help="Klicken, um die gesamten Höhenmeter aufwärts anzuzeigen.")

    st.markdown("---")
    ### Akkumulierte Power Curve (aus allen FIT-Dateien)

    # Auch hier den Cache nutzen, da die Power Curve eine aufwändige Berechnung sein kann
    @st.cache_data(show_spinner="Erstelle Power Curve...")
    def get_cached_power_curve(all_power_data_df_for_hash):
        return create_accumulated_power_curve(all_power_data_df_for_hash)

    accumulated_pc_df = get_cached_power_curve(all_power_data) # all_power_data ist bereits das Ergebnis aus dem ersten Cache

    if not accumulated_pc_df.empty:
        # plot_power_curve ist nicht rechenintensiv, daher muss es nicht gecached werden
        fig_power_curve = plot_power_curve(accumulated_pc_df)
        st.plotly_chart(fig_power_curve, use_container_width=True)
    else:
        st.info("Nicht genügend Leistungsdaten in den FIT-Dateien gefunden, um eine Power Curve zu erstellen.")

    st.markdown("---")
    ### Weitere Metriken

    col_dummy1, col_dummy2 = st.columns(2)
    with col_dummy1:
        st.metric(label="Durchschnittliche Trittfrequenz (Dummy)", value="N/A") # Platzhalter
    with col_dummy2:
        st.metric(label="Herzfrequenzvariabilität (Dummy)", value="N/A") # Platzhalter

    st.info("Diese Metriken sind Platzhalter und werden in zukünftigen Updates befüllt.")

# Um die `dashboard.py` direkt auszuführen, falls nötig (ansonsten wird sie von main.py importiert)
if __name__ == "__main__":
    main()