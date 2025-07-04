
# workout_form_utils.py

import streamlit as st
from datetime import datetime, timedelta
import os
import gpxpy
import gpxpy.gpx
import pandas as pd
from fitparse import FitFile
import numpy as np


import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) # Stellt sicher, dass das Projekt-Root im Python-Pfad ist

from Module.utils import normalize_path_slashes 

# --- Konfiguration & Konstanten ---
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Sicherstellen, dass das Verzeichnis existiert

# --- Hilfsfunktion zum Speichern von Dateien ---
def save_uploaded_file(uploaded_file, file_prefix, workout_name):
    """
    Speichert eine hochgeladene Datei im UPLOAD_DIR mit einem eindeutigen Namen.
    Normalisiert den Pfad mit Forward-Slashes.

    Args:
        uploaded_file (streamlit.runtime.uploaded_file_manager.UploadedFile):
            Das von st.file_uploader erhaltene Dateiobjekt.
        file_prefix (str): Ein Präfix für den Dateinamen (z.B. "img", "gpx").
        workout_name (str): Der Name des Workouts, um den Dateinamen aussagekräftiger zu machen.

    Returns:
        str or None: Der Pfad zur gespeicherten Datei (mit Forward-Slashes) oder None, wenn keine Datei hochgeladen wurde.
    """
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = uploaded_file.name.split(".")[-1]
        safe_name = workout_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        unique_filename = f"{safe_name}_{file_prefix}_{timestamp}.{file_extension}"
        
        # Originalpfad erstellen und dann normalisieren
        raw_file_path = os.path.join(UPLOAD_DIR, unique_filename)
        file_path = normalize_path_slashes(raw_file_path) 
        
        try:
            with open(raw_file_path, "wb") as f: 
                f.write(uploaded_file.getbuffer())
            return file_path 
        except Exception as e:
            st.error(f"Fehler beim Speichern der Datei {uploaded_file.name}: {e}")
            return None
    return None

# --- Funktion zum Parsen von GPX-Dateien ---
def parse_gpx_data(gpx_file_path):
    """
    Parst eine GPX-Datei und extrahiert Dauer, Distanz, Datum,
    Durchschnittsgeschwindigkeit und Höhenmeter (hoch und runter).

    Args:
        gpx_file_path (str): Der Pfad zur GPX-Datei.

    Returns:
        tuple: (duration_minutes, total_distance_km, start_date, avg_speed_kmh, elevation_gain_pos, elevation_gain_neg)
               oder (0, 0.0, None, None, 0.0, 0, 0) bei Fehler.
    """
    duration_minutes = 0
    total_distance_km = 0.0
    min_time = None
    max_time = None
    start_date = None
    avg_speed_kmh = 0.0
    elevation_gain_pos = 0
    elevation_gain_neg = 0
    
    elevations = []
    times = []
    distances = []

   
    gpx_file_path_os_native = os.path.normpath(gpx_file_path) 

    if not os.path.exists(gpx_file_path_os_native):
        return 0, 0.0, None, None, 0.0, 0, 0

    try:
        with open(gpx_file_path_os_native, 'r') as gpx_file: 
            gpx = gpxpy.parse(gpx_file)

        # Extract points for elevation and time calculations
        current_distance = 0.0
        prev_point = None
        for track in gpx.tracks:
            if track.segments:
                for segment in track.segments:
                    for i, point in enumerate(segment.points):
                        if point.time:
                            if min_time is None or point.time < min_time:
                                min_time = point.time
                            if max_time is None or point.time > max_time:
                                max_time = point.time
                            times.append(point.time)

                        if point.elevation is not None:
                            elevations.append(point.elevation)
                        
                        if prev_point:
                            # Calculate distance between points
                            point_distance_2d = point.distance_2d(prev_point)
                            current_distance += point_distance_2d
                        distances.append(current_distance) # Store cumulative distance
                        prev_point = point

        
        if min_time and max_time:
            time_difference = max_time - min_time
            duration_minutes = int(time_difference.total_seconds() / 60)
            start_date = min_time.date()
        
        # Total distance from gpxpy (more accurate than summing point-to-point 2D distances for total)
        total_distance_meters = gpx.length_2d()
        total_distance_km = total_distance_meters / 1000.0

        # Calculate average speed
        if duration_minutes > 0:
            avg_speed_kmh = (total_distance_km / duration_minutes) * 60 # km/min * 60 min/h = km/h
        
        # Calculate Elevation Gain (Positive and Negative)
        if len(elevations) > 1:
            diff_elevations = np.diff(elevations)
            elevation_gain_pos = int(np.sum(diff_elevations[diff_elevations > 0]))
            elevation_gain_neg = int(np.sum(diff_elevations[diff_elevations < 0]))
            
        return duration_minutes, total_distance_km, start_date, avg_speed_kmh, elevation_gain_pos, abs(elevation_gain_neg)
    except Exception as e:
        st.error(f"Fehler beim Parsen der GPX-Datei: {e}")
        return 0, 0.0, None, None, 0.0, 0, 0

# --- Funktion zum Parsen von FIT-Dateien ---
def parse_fit_data(fit_file_path):
    """
    Parst eine FIT-Datei und extrahiert Dauer, Distanz, Datum, Sportart, Puls,
    Durchschnittsgeschwindigkeit und Höhenmeter (hoch und runter).

    Args:
        fit_file_path (str): Der Pfad zur FIT-Datei.

    Returns:
        tuple: (duration_minutes, total_distance_km, start_date, sportart, average_heart_rate, avg_speed_kmh, elevation_gain_pos, elevation_gain_neg)
               oder (0, 0.0, None, None, 0, 0.0, 0, 0) bei Fehler.
    """
    duration_minutes = 0
    total_distance_km = 0.0
    start_date = None
    sportart = None
    heart_rates = []
    speeds = []
    elevations = []

    fit_file_path_os_native = os.path.normpath(fit_file_path) 

    if not os.path.exists(fit_file_path_os_native):
        return 0, 0.0, None, None, 0, 0.0, 0, 0

    try:
        fitfile = FitFile(fit_file_path_os_native) 
        
        min_timestamp = None
        max_timestamp = None

        for record in fitfile.get_messages('record'):
            timestamp = record.get_value('timestamp')
            if timestamp:
                if min_timestamp is None or timestamp < min_timestamp:
                    min_timestamp = timestamp
                if max_timestamp is None or timestamp > max_timestamp:
                    max_timestamp = timestamp
                if start_date is None: # Set start_date from the first timestamp
                    start_date = timestamp.date()

            # Distance is cumulative, so take the max value
            distance_meters = record.get_value('distance')
            if distance_meters is not None:
                total_distance_km = max(total_distance_km, distance_meters / 1000.0) 
            
            hr_val = record.get_value('heart_rate')
            if hr_val is not None:
                heart_rates.append(hr_val)
            
            speed_val_ms = record.get_value('speed') # speed in m/s
            if speed_val_ms is not None:
                speeds.append(speed_val_ms)

            elevation_val = record.get_value('altitude') # altitude in meters
            if elevation_val is not None:
                elevations.append(elevation_val)


        # Get session messages for total duration and sport (prefer these if available)
        for session in fitfile.get_messages('session'):
            if session.get_value('total_timer_time'):
                duration_minutes = int(session.get_value('total_timer_time') / 60)
            if session.get_value('sport'):
                sportart = str(session.get_value('sport')).replace('_', ' ').title()

        average_heart_rate = int(sum(heart_rates) / len(heart_rates)) if heart_rates else 0
        
        avg_speed_kmh = 0.0
        if speeds:
            # Average of speeds from records (in m/s), then convert to km/h
            avg_speed_ms = np.mean(speeds)
            avg_speed_kmh = avg_speed_ms * 3.6 # m/s * (3600 s / 1000 m) = km/h
        
        # Fallback for duration and speed if session data is missing, using timestamps
        if duration_minutes == 0 and min_timestamp and max_timestamp:
            time_diff_seconds = (max_timestamp - min_timestamp).total_seconds()
            duration_minutes = int(time_diff_seconds / 60)
            if total_distance_km > 0 and duration_minutes > 0:
                # Recalculate average speed if duration was derived from timestamps and total_distance_km exists
                avg_speed_kmh = (total_distance_km / duration_minutes) * 60

        # Calculate Elevation Gain (Positive and Negative)
        elevation_gain_pos = 0
        elevation_gain_neg = 0
        if len(elevations) > 1:
            # Ensure elevations are float for diff, then convert back to int for sum
            diff_elevations = np.diff(np.array(elevations, dtype=float))
            elevation_gain_pos = int(np.sum(diff_elevations[diff_elevations > 0]))
            elevation_gain_neg = int(np.sum(diff_elevations[diff_elevations < 0]))


        return duration_minutes, total_distance_km, start_date, sportart, average_heart_rate, avg_speed_kmh, elevation_gain_pos, abs(elevation_gain_neg)

    except Exception as e:
        st.error(f"Fehler beim Parsen der FIT-Datei: {e}")
        return 0, 0.0, None, None, 0, 0.0, 0, 0


# --- Hilfsfunktion zur Formatierung der Dauer ---
def format_duration(total_minutes):
    """
    Formatiert eine Dauer in Minuten in ein lesbares Stunden- und Minutenformat.

    Args:
        total_minutes (int): Die Gesamtzahl der Minuten.

    Returns:
        str: Die formatierte Dauer (z.B. "1 Stunde und 30 Minuten", "45 Minuten").
    """
    if total_minutes < 60:
        return f"{total_minutes} Minuten"
    else:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if minutes == 0:
            return f"{hours} Stunden"
        else:
            return f"{hours} Stunden und {minutes} Minuten"

# --- Hauptfunktion zum Anzeigen des Workout-Formulars ---
def display_workout_form(initial_data=None, form_key_suffix="add"):
    """
    Zeigt ein Streamlit-Formular zum Hinzufügen oder Bearbeiten eines Workouts an.

    Args:
        initial_data (dict, optional): Ein Dictionary mit initialen Daten zum Vorbefüllen des Formulars im Bearbeitungsmodus.
                                       Enthält Felder wie 'name', 'date', 'sportart', 'dauer', 'distanz', 'puls',
                                       'kalorien', 'anstrengung', 'star_rating', 'description', 'image', 'gpx_file',
                                       'ekg_file', 'fit_file', 'avg_speed_kmh', 'elevation_gain_pos', 'elevation_gain_neg'.
                                       Standardwert ist None für den Hinzufügen-Modus.
        form_key_suffix (str, optional): Ein Suffix, das zu den Schlüsseln der Streamlit-Widgets hinzugefügt wird,
                                         um Kollisionen bei mehreren Formularinstanzen zu vermeiden. Standardwert ist "add".

    Returns:
        dict or str or None: Ein Dictionary mit den Formulardaten, wenn das Formular erfolgreich übermittelt wurde.
                              Gibt "CANCEL" zurück, wenn der Abbruch-Button im Bearbeitungsmodus geklickt wurde.
                              Gibt None zurück, wenn das Formular noch nicht übermittelt wurde oder die Validierung fehlschlägt.
    """
    is_edit_mode = initial_data is not None
    prefix = f"workout_form_{form_key_suffix}_"
    initial_doc_id = initial_data.doc_id if is_edit_mode and hasattr(initial_data, 'doc_id') else None

    # Robuste Initialisierung der Session State Variablen
    # Wir setzen diese Werte nur, wenn das Formular zum ersten Mal geladen wird
    # oder wenn im Bearbeitungsmodus eine NEUE Trainings-ID geladen wird.
    if st.session_state.get(f"{prefix}last_loaded_id_check") != initial_doc_id:
        st.session_state[f"{prefix}name_input"] = initial_data.get('name', "") if is_edit_mode else ""
        
        date_val = datetime.now().date()
        if is_edit_mode and 'date' in initial_data:
            try:
                date_val = datetime.strptime(initial_data['date'], "%Y-%m-%d").date()
            except ValueError:
                st.warning(f"Ungültiges Datumsformat '{initial_data['date']}' für Workout-ID {initial_doc_id}. Setze auf aktuelles Datum.")
        st.session_state[f"{prefix}date_input"] = date_val

        st.session_state[f"{prefix}sportart_input"] = initial_data.get('sportart', "") if is_edit_mode else ""
        st.session_state[f"{prefix}dauer_total_minutes_input"] = int(initial_data.get('dauer', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}distanz_input"] = float(initial_data.get('distanz', 0.0)) if is_edit_mode else 0.0
        st.session_state[f"{prefix}puls_input"] = int(initial_data.get('puls', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}kalorien_input"] = int(initial_data.get('kalorien', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}description_input"] = initial_data.get('description', "") if is_edit_mode else ""
        st.session_state[f"{prefix}selected_antrengung"] = initial_data.get('anstrengung', None) if is_edit_mode else None
        st.session_state[f"{prefix}selected_star_rating"] = initial_data.get('star_rating', None) if is_edit_mode else None
        
        # Neue Initialisierungen für Durchschnittsgeschwindigkeit und Höhenmeter
        st.session_state[f"{prefix}avg_speed_input"] = float(initial_data.get('avg_speed_kmh', 0.0)) if is_edit_mode else 0.0
        st.session_state[f"{prefix}elevation_gain_pos_input"] = int(initial_data.get('elevation_gain_pos', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}elevation_gain_neg_input"] = int(initial_data.get('elevation_gain_neg', 0)) if is_edit_mode else 0

        # Dateipfade aus initial_data müssen normalisiert werden, da sie aus der DB kommen könnten
        st.session_state[f"{prefix}current_image_path"] = normalize_path_slashes(initial_data.get('image', None)) if is_edit_mode else None # <--- HIER ANGEWENDET
        st.session_state[f"{prefix}current_gpx_path"] = normalize_path_slashes(initial_data.get('gpx_file', None)) if is_edit_mode else None # <--- HIER ANGEWENDET
        st.session_state[f"{prefix}current_ekg_path"] = normalize_path_slashes(initial_data.get('ekg_file', None)) if is_edit_mode else None # <--- HIER ANGEWENDET
        st.session_state[f"{prefix}current_fit_path"] = normalize_path_slashes(initial_data.get('fit_file', None)) if is_edit_mode else None # <--- HIER ANGEWENDET

        # Dies ist der Schlüssel, der anzeigt, wann die Initialisierung erfolgt ist
        st.session_state[f"{prefix}last_loaded_id_check"] = initial_doc_id


    # --- Buttons für Anstrengung (Smiley-Buttons) ---
    name = st.text_input("Name des Workouts", placeholder="Test 1", value=st.session_state.get(f"{prefix}name_input", ""), key=f"{prefix}name_input_form")
        
    st.write("Wie anstrengend war das Training?")
    col1, col2, col3, col4, col5 = st.columns(5)
    antrengung_value = st.session_state.get(f"{prefix}selected_antrengung", None)

    with col1:
        if antrengung_value == "good":
            st.markdown("### 😃 Sehr leicht")
        elif st.button("😃 Sehr leicht", key=f"{prefix}smiley_good_btn"): 
            st.session_state[f"{prefix}selected_antrengung"] = "good"
            st.rerun()
    with col2:
        if antrengung_value == "ok":
            st.markdown("### 🙂 leicht")
        elif st.button("🙂 leicht", key=f"{prefix}smiley_ok_btn"): 
            st.session_state[f"{prefix}selected_antrengung"] = "ok"
            st.rerun()
    with col3:
        if antrengung_value == "neutral":
            st.markdown("### 😐 Neutral")
        elif st.button("😐 Neutral", key=f"{prefix}smiley_neutral_btn"): 
            st.session_state[f"{prefix}selected_antrengung"] = "neutral"
            st.rerun()
    with col4:
        if antrengung_value == "acceptable":
            st.markdown("### 😟 anstrengend")
        elif st.button("😟 anstrengend", key=f"{prefix}smiley_acceptable_btn"): 
            st.session_state[f"{prefix}selected_antrengung"] = "acceptable"
            st.rerun()
    with col5:
        if antrengung_value == "bad":
            st.markdown("### 🥵 sehr anstrengend")
        elif st.button("🥵 sehr anstrengend", key=f"{prefix}smiley_bad_btn"): 
            st.session_state[f"{prefix}selected_antrengung"] = "bad"
            st.rerun()

    # --- Sternebewertung (Highlighting Implementierung) ---
    st.write("---")
    st.write("Wie würdest du dieses Workout bewerten?")
    star_rating_value = st.session_state.get(f"{prefix}selected_star_rating", None)
    
    cols_stars = st.columns(5)
    for i in range(1, 6):
        with cols_stars[i-1]:
            if star_rating_value == i:
                st.markdown(f"**{'⭐' * i}**")
            elif st.button("⭐" * i, key=f"{prefix}star_button_{i}_btn"): 
                st.session_state[f"{prefix}selected_star_rating"] = i
                st.rerun()
    
    st.write("---")
    st.markdown(
    f"<span style='font-size: 24px; font-weight: bold;'>Dateien hochladen</span>",
    unsafe_allow_html=True
)
    bild, ekg, gpx, fit = st.columns(4)
    with bild:
    # --- Dateiuploader (MÜSSEN außerhalb des Formulars bleiben) ---
        uploaded_image_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"], help="Optional: Füge ein Bild deines Workouts hinzu.", key=f"{prefix}image_uploader")
    with ekg:
        uploaded_ekg_file = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"], help="Optional: Füge eine EKG-Datei deines Workouts hinzu. Max. Größe = 200MB", key=f"{prefix}ekg_uploader")
    with gpx:
        uploaded_gpx_file = st.file_uploader("GPX Datei hochladen", type=["gpx"], help="Optional: Füge eine GPX-Datei deines Workouts hinzu. Max. Größe = 200MB", key=f"{prefix}gpx_uploader")
        if st.button("GPX-Datei auswerten", key=f"{prefix}parse_gpx_button"):
            if uploaded_gpx_file:
                # Spinner um die Abarbeitung der GPX-Datei
                with st.spinner('GPX-Datei wird ausgewertet... Dies kann einen Moment dauern.'):
                    # Temporäre Datei speichern (hier keine Normalisierung, da es nur eine temporäre Datei ist)
                    temp_gpx_path = os.path.join(UPLOAD_DIR, "temp_gpx_for_parsing.gpx")
                    with open(temp_gpx_path, "wb") as f:
                        f.write(uploaded_gpx_file.getbuffer())
                    
                    duration_minutes, distance_km, start_date, avg_speed, elev_pos, elev_neg = parse_gpx_data(temp_gpx_path)
                    sport = None # GPX enthält normalerweise keine Sportart-Info
                    if duration_minutes > 0:
                        st.session_state[f"{prefix}dauer_total_minutes_input"] = duration_minutes
                        st.success(f"Dauer aus GPX-Datei erkannt: {format_duration(duration_minutes)}.")
                    if distance_km > 0.0:
                        st.session_state[f"{prefix}distanz_input"] = round(distance_km, 2)
                        st.success(f"Distanz aus GPX-Datei erkannt: {round(distance_km, 2)} km.")
                    if start_date:
                        st.session_state[f"{prefix}date_input"] = start_date
                        st.success(f"Datum aus GPX-Datei erkannt: {start_date.strftime('%Y-%m-%d')}.")
                    if sport: # Dieser Block wird für GPX normalerweise nicht ausgeführt
                        st.session_state[f"{prefix}sportart_input"] = sport
                        st.success(f"Sportart aus GPX-Datei erkannt: {sport}.")
                    if avg_speed > 0.0:
                        st.session_state[f"{prefix}avg_speed_input"] = round(avg_speed, 2)
                        st.success(f"Durchschnittsgeschwindigkeit aus GPX-Datei erkannt: {round(avg_speed, 2)} km/h.")
                    if elev_pos > 0:
                        st.session_state[f"{prefix}elevation_gain_pos_input"] = elev_pos
                        st.success(f"Höhenmeter aufwärts aus GPX-Datei erkannt: {elev_pos} m.")
                    if elev_neg > 0:
                        st.session_state[f"{prefix}elevation_gain_neg_input"] = elev_neg
                        st.success(f"Höhenmeter abwärts aus GPX-Datei erkannt: {elev_neg} m.")

                    if os.path.exists(temp_gpx_path):
                        os.remove(temp_gpx_path)
                st.rerun() # Wichtig, damit die neuen Werte in den Input-Feldern angezeigt werden
            else:
                st.warning("Bitte lade zuerst eine GPX-Datei hoch, um sie auszuwerten.")
    with fit:
        uploaded_fit_file = st.file_uploader("FIT Datei hochladen", type=["fit"], help="Optional: Füge eine FIT-Datei deines Workouts hinzu. Max. Größe = 200MB", key=f"{prefix}fit_uploader")
        if st.button("FIT-Datei auswerten", key=f"{prefix}parse_fit_button"):
            if uploaded_fit_file:
                # Spinner um die Abarbeitung der FIT-Datei
                with st.spinner('FIT-Datei wird ausgewertet... Dies kann einen Moment dauern.'):
                    # Temporäre Datei speichern (hier keine Normalisierung, da es nur eine temporäre Datei ist)
                    temp_fit_path = os.path.join(UPLOAD_DIR, "temp_fit_for_parsing.fit")
                    with open(temp_fit_path, "wb") as f:
                        f.write(uploaded_fit_file.getbuffer())
                    
                    duration_minutes, distance_km, start_date, sport, average_heart_rate, avg_speed, elev_pos, elev_neg = parse_fit_data(temp_fit_path)
                    
                    if duration_minutes > 0:
                        st.session_state[f"{prefix}dauer_total_minutes_input"] = duration_minutes
                        st.success(f"Dauer aus FIT-Datei erkannt: {format_duration(duration_minutes)}.")
                    if distance_km > 0.0:
                        st.session_state[f"{prefix}distanz_input"] = round(distance_km, 2)
                        st.success(f"Distanz aus FIT-Datei erkannt: {round(distance_km, 2)} km.")
                    if start_date:
                        st.session_state[f"{prefix}date_input"] = start_date
                        st.success(f"Datum aus FIT-Datei erkannt: {start_date.strftime('%Y-%m-%d')}.")
                    if sport:
                        st.session_state[f"{prefix}sportart_input"] = sport
                        st.success(f"Sportart aus FIT-Datei erkannt: {sport}.")
                    if average_heart_rate > 0:
                        st.session_state[f"{prefix}puls_input"] = average_heart_rate
                        st.success(f"Durchschnittlicher Puls aus FIT-Datei erkannt: {average_heart_rate} bpm.")
                    if avg_speed > 0.0:
                        st.session_state[f"{prefix}avg_speed_input"] = round(avg_speed, 2)
                        st.success(f"Durchschnittsgeschwindigkeit aus FIT-Datei erkannt: {round(avg_speed, 2)} km/h.")
                    if elev_pos > 0:
                        st.session_state[f"{prefix}elevation_gain_pos_input"] = elev_pos
                        st.success(f"Höhenmeter aufwärts aus FIT-Datei erkannt: {elev_pos} m.")
                    if elev_neg > 0:
                        st.session_state[f"{prefix}elevation_gain_neg_input"] = elev_neg
                        st.success(f"Höhenmeter abwärts aus FIT-Datei erkannt: {elev_neg} m.")

                    if os.path.exists(temp_fit_path):
                        os.remove(temp_fit_path)
                st.rerun() # Wichtig, damit die neuen Werte in den Input-Feldern angezeigt werden
            else:
                st.warning("Bitte lade zuerst eine FIT-Datei hoch, um sie auszuwerten.")
    

    # --- Das Formular selbst (Start des Formular-Kontexts) ---
    with st.form(key=f"{prefix}workout_form"):
        # Zeige aktuelle Dateipfade im Bearbeitungsmodus an
        if is_edit_mode:
            # Hier die Pfade normalisieren, bevor sie angezeigt werden (falls sie noch nicht normalisiert sind)
            # Sie sollten aber bereits in st.session_state normalisiert worden sein (siehe oben)
            display_image_path = os.path.basename(st.session_state.get(f'{prefix}current_image_path', '')) if st.session_state.get(f'{prefix}current_image_path') else 'Kein Bild'
            display_gpx_path = os.path.basename(st.session_state.get(f'{prefix}current_gpx_path', '')) if st.session_state.get(f'{prefix}current_gpx_path') else 'Keine GPX-Datei'
            display_ekg_path = os.path.basename(st.session_state.get(f'{prefix}current_ekg_path', '')) if st.session_state.get(f'{prefix}current_ekg_path') else 'Keine EKG-Datei'
            display_fit_path = os.path.basename(st.session_state.get(f'{prefix}current_fit_path', '')) if st.session_state.get(f'{prefix}current_fit_path') else 'Keine FIT-Datei'

            st.markdown(f"**Aktuelles Bild:** {display_image_path}")
            st.markdown(f"**Aktuelle GPX-Datei:** {display_gpx_path}")
            st.markdown(f"**Aktuelle EKG-Datei:** {display_ekg_path}")
            st.markdown(f"**Aktuelle FIT-Datei:** {display_fit_path}")
            st.markdown("---")

        # Verwende get() für die value-Parameter, um KeyError zu vermeiden, falls ein Wert mal fehlen sollte
        date = st.date_input("Datum", value=st.session_state.get(f"{prefix}date_input", datetime.now().date()), key=f"{prefix}date_input_form")
        sportart = st.text_input("Sportart", placeholder="z.B. Laufen, Radfahren, Schwimmen", value=st.session_state.get(f"{prefix}sportart_input", ""), key=f"{prefix}sportart_input_form")

        description = st.text_area("Beschreibung", value=st.session_state.get(f"{prefix}description_input", ""), key=f"{prefix}description_input_form")
        
        st.write("---")
        st.write("Kerninformationen zum Workout (falls nicht in Uploads enthalten):")
        
        # NEUES Feld für Dauer in Stunden und Minuten
        initial_total_minutes = st.session_state.get(f"{prefix}dauer_total_minutes_input", 0)
        initial_hours = initial_total_minutes // 60
        initial_minutes = initial_total_minutes % 60

        col_h, col_m = st.columns(2)
        with col_h:
            hours = st.number_input("Dauer (Stunden)", min_value=0, step=1, value=initial_hours, key=f"{prefix}dauer_hours_input_form")
        with col_m:
            minutes = st.number_input("Dauer (Minuten)", min_value=0, max_value=59, step=1, value=initial_minutes, key=f"{prefix}dauer_minutes_input_form")

        # Berechne die Gesamtdauer in Minuten für die Speicherung
        dauer_to_save = (hours * 60) + minutes

        distanz = st.number_input("Distanz (in km)", min_value=0.0, step=0.1, value=st.session_state.get(f"{prefix}distanz_input", 0.0), key=f"{prefix}distanz_input_form")
        puls = st.number_input("Puls (in bpm)", min_value=0, step=1, value=st.session_state.get(f"{prefix}puls_input", 0), key=f"{prefix}puls_input_form")
        kalorien = st.number_input("Kalorien (in kcal)", min_value=0, step=1, value=st.session_state.get(f"{prefix}kalorien_input", 0), key=f"{prefix}kalorien_input_form")
        
        # NEUE FELDER
        avg_speed = st.number_input("Durchschnittsgeschwindigkeit (km/h)", min_value=0.0, step=0.1, value=st.session_state.get(f"{prefix}avg_speed_input", 0.0), format="%.2f", key=f"{prefix}avg_speed_input_form")
        elevation_gain_pos = st.number_input("Höhenmeter aufwärts (m)", min_value=0, step=1, value=st.session_state.get(f"{prefix}elevation_gain_pos_input", 0), key=f"{prefix}elevation_gain_pos_input_form")
        elevation_gain_neg = st.number_input("Höhenmeter abwärts (m)", min_value=0, step=1, value=st.session_state.get(f"{prefix}elevation_gain_neg_input", 0), key=f"{prefix}elevation_gain_neg_input_form")

        st.write("---")
        
        # Submit-Button für das gesamte Formular
        submit_label = "Workout speichern" if is_edit_mode else "Workout hinzufügen"
        submitted = st.form_submit_button(submit_label)

        if submitted:
            # Validierung
            if not name:
                st.error("Bitte gib einen Namen für das Workout ein.")
                return None
            elif not sportart:
                st.error("Bitte gib eine Sportart ein.")
                return None
            elif st.session_state.get(f"{prefix}selected_antrengung") is None:
                st.error("Bitte bewerte die Anstrengung des Trainings.")
                return None
            elif st.session_state.get(f"{prefix}selected_star_rating") is None:
                st.error("Bitte gib eine Sternebewertung ab.")
                return None
            
            # Dateipfade handhaben: Neue Uploads überschreiben alte Pfade
            # Die save_uploaded_file Funktion gibt bereits normalisierte Pfade zurück.
            # Wenn kein neuer Upload erfolgt, bleibt der Pfad aus session_state erhalten,
            # welcher bereits normalisiert ist (siehe Initialisierung).
            link_image = save_uploaded_file(uploaded_image_file, "img", name) or st.session_state.get(f"{prefix}current_image_path")
            link_gpx = save_uploaded_file(uploaded_gpx_file, "gpx", name) or st.session_state.get(f"{prefix}current_gpx_path")
            link_ekg = save_uploaded_file(uploaded_ekg_file, "ekg", name) or st.session_state.get(f"{prefix}current_ekg_path")
            link_fit = save_uploaded_file(uploaded_fit_file, "fit", name) or st.session_state.get(f"{prefix}current_fit_path")

            return {
                "name": name,
                "date": date.strftime("%Y-%m-%d"),
                "sportart": sportart,
                "dauer": dauer_to_save, 
                "distanz": distanz,
                "puls": puls,
                "kalorien": kalorien,
                "anstrengung": st.session_state[f"{prefix}selected_antrengung"], 
                "star_rating": st.session_state[f"{prefix}selected_star_rating"], 
                "description": description,
                "image": link_image, # Diese Pfade sind bereits normalisiert
                "gpx_file": link_gpx, # Diese Pfade sind bereits normalisiert
                "ekg_file": link_ekg, # Diese Pfade sind bereits normalisiert
                "fit_file": link_fit, # Diese Pfade sind bereits normalisiert
                "avg_speed_kmh": avg_speed, 
                "elevation_gain_pos": elevation_gain_pos, 
                "elevation_gain_neg": elevation_gain_neg 
            }
        
        # Cancel-Button (für den Bearbeitungsmodus)
        if is_edit_mode:
            cancel_submitted = st.form_submit_button("Abbrechen")
            if cancel_submitted:
                return "CANCEL"
    
    return None