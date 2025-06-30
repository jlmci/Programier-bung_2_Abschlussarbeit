
import streamlit as st
from datetime import datetime, timedelta
import os
import gpxpy
import gpxpy.gpx
import pandas as pd
from fitparse import FitFile # Import the fitparse library

# --- Konfiguration & Konstanten ---
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True) # Sicherstellen, dass das Verzeichnis existiert

# --- Hilfsfunktion zum Speichern von Dateien ---
def save_uploaded_file(uploaded_file, file_prefix, workout_name):
    """
    Speichert eine hochgeladene Datei im UPLOAD_DIR mit einem eindeutigen Namen.

    Args:
        uploaded_file (streamlit.runtime.uploaded_file_manager.UploadedFile):
            Das von st.file_uploader erhaltene Dateiobjekt.
        file_prefix (str): Ein Präfix für den Dateinamen (z.B. "img", "gpx").
        workout_name (str): Der Name des Workouts, um den Dateinamen aussagekräftiger zu machen.

    Returns:
        str or None: Der Pfad zur gespeicherten Datei oder None, wenn keine Datei hochgeladen wurde.
    """
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = uploaded_file.name.split(".")[-1]
        safe_name = workout_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        unique_filename = f"{safe_name}_{file_prefix}_{timestamp}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return file_path
        except Exception as e:
            st.error(f"Fehler beim Speichern der Datei {uploaded_file.name}: {e}")
            return None
    return None

# --- Funktion zum Parsen von GPX-Dateien ---
def parse_gpx_data(gpx_file_path):
    """
    Parst eine GPX-Datei und extrahiert Dauer, Distanz, Datum, gegebenenfalls Sportart.

    Args:
        gpx_file_path (str): Der Pfad zur GPX-Datei.

    Returns:
        tuple: (duration_minutes, total_distance_km, start_date, sportart) oder (0, 0.0, None, None) bei Fehler.
    """
    duration_minutes = 0
    total_distance_km = 0.0
    min_time = None
    max_time = None
    start_date = None
    sportart = None # GPX files don't typically store sport type directly in a parseable field

    if not os.path.exists(gpx_file_path):
        return 0, 0.0, None, None

    try:
        with open(gpx_file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        for track in gpx.tracks:
            if track.segments:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time:
                            if min_time is None or point.time < min_time:
                                min_time = point.time
                            if max_time is None or point.time > max_time:
                                max_time = point.time
            # Try to get sport from track name if available
            if track.name and not sportart:
                sportart = track.name
        
        if min_time and max_time:
            time_difference = max_time - min_time
            duration_minutes = int(time_difference.total_seconds() / 60)
            start_date = min_time.date()
        
        total_distance_meters = gpx.length_2d()
        total_distance_km = total_distance_meters / 1000.0

        return duration_minutes, total_distance_km, start_date, sportart
    except Exception as e:
        st.error(f"Fehler beim Parsen der GPX-Datei: {e}")
        return 0, 0.0, None, None

# --- Funktion zum Parsen von FIT-Dateien ---
def parse_fit_data(fit_file_path):
    """
    Parst eine FIT-Datei und extrahiert Dauer, Distanz, Datum, Sportart und Puls.

    Args:
        fit_file_path (str): Der Pfad zur FIT-Datei.

    Returns:
        tuple: (duration_minutes, total_distance_km, start_date, sportart, average_heart_rate) oder (0, 0.0, None, None, 0) bei Fehler.
    """
    duration_minutes = 0
    total_distance_km = 0.0
    start_date = None
    sportart = None
    heart_rates = []

    if not os.path.exists(fit_file_path):
        return 0, 0.0, None, None, 0

    try:
        fitfile = FitFile(fit_file_path)
        
        # Iterate over all messages of type 'record'
        for record in fitfile.get_messages('record'):
            for data in record:
                if data.name == 'timestamp' and start_date is None:
                    start_date = data.value.date()
                if data.name == 'distance':
                    # Fit files typically store distance in meters
                    total_distance_km = max(total_distance_km, data.value / 1000.0) 
                if data.name == 'heart_rate':
                    heart_rates.append(data.value)

        # Get session messages for duration and sport
        for session in fitfile.get_messages('session'):
            if session.get_value('total_timer_time'):
                duration_minutes = int(session.get_value('total_timer_time') / 60)
            if session.get_value('sport'):
                # Convert sport enum to string
                sportart = str(session.get_value('sport')).replace('_', ' ').title()

        average_heart_rate = int(sum(heart_rates) / len(heart_rates)) if heart_rates else 0

        return duration_minutes, total_distance_km, start_date, sportart, average_heart_rate

    except Exception as e:
        st.error(f"Fehler beim Parsen der FIT-Datei: {e}")
        return 0, 0.0, None, None, 0


# --- Hilfsfunktion zur Formatierung der Dauer ---
def format_duration(total_minutes):
    """
    Formatiert eine Dauer in Minuten in ein lesbares Stunden- und Minutenformat.
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
        # Speichere die Dauer immer noch als Minuten, aber handhabe die Anzeige anders
        st.session_state[f"{prefix}dauer_total_minutes_input"] = int(initial_data.get('dauer', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}distanz_input"] = float(initial_data.get('distanz', 0.0)) if is_edit_mode else 0.0
        st.session_state[f"{prefix}puls_input"] = int(initial_data.get('puls', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}kalorien_input"] = int(initial_data.get('kalorien', 0)) if is_edit_mode else 0
        st.session_state[f"{prefix}description_input"] = initial_data.get('description', "") if is_edit_mode else ""
        st.session_state[f"{prefix}selected_antrengung"] = initial_data.get('anstrengung', None) if is_edit_mode else None
        st.session_state[f"{prefix}selected_star_rating"] = initial_data.get('star_rating', None) if is_edit_mode else None
        
        st.session_state[f"{prefix}current_image_path"] = initial_data.get('image', None) if is_edit_mode else None
        st.session_state[f"{prefix}current_gpx_path"] = initial_data.get('gpx_file', None) if is_edit_mode else None
        st.session_state[f"{prefix}current_ekg_path"] = initial_data.get('ekg_file', None) if is_edit_mode else None
        st.session_state[f"{prefix}current_fit_path"] = initial_data.get('fit_file', None) if is_edit_mode else None

        # Dies ist der Schlüssel, der anzeigt, wann die Initialisierung erfolgt ist
        st.session_state[f"{prefix}last_loaded_id_check"] = initial_doc_id
    name = st.text_input("Name des Workouts", placeholder="Test 1", value=st.session_state.get(f"{prefix}name_input", ""), key=f"{prefix}name_input_form")
    st.write("---")

    # --- Anstrengung (Smiley-Buttons) ---
    st.write("Wie anstrengend war das Training?")
    col1, col2, col3, col4, col5 = st.columns(5)
    # Sicherstellen, dass der Wert existiert, bevor er gelesen wird
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
    # Sicherstellen, dass der Wert existiert, bevor er gelesen wird
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

    # --- Dateiuploader (Außerhalb des Formulars) ---
    uploaded_image_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"], help="Optional: Füge ein Bild deines Workouts hinzu.", key=f"{prefix}image_uploader")
    uploaded_gpx_file = st.file_uploader("GPX Datei hochladen", type=["gpx"], help="Optional: Füge eine GPX-Datei deines Workouts hinzu. Max. Größe = 200MB", key=f"{prefix}gpx_uploader")
    uploaded_ekg_file = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"], help="Optional: Füge eine EKG-Datei deines Workouts hinzu. Max. Größe = 200MB", key=f"{prefix}ekg_uploader")
    uploaded_fit_file = st.file_uploader("FIT Datei hochladen", type=["fit"], help="Optional: Füge eine FIT-Datei deines Workouts hinzu. Max. Größe = 200MB", key=f"{prefix}fit_uploader")

    # Button zum Parsen der GPX-Daten
    if st.button("GPX-Datei auswerten", key=f"{prefix}parse_gpx_button"):
        if uploaded_gpx_file:
            temp_gpx_path = os.path.join(UPLOAD_DIR, "temp_gpx_for_parsing.gpx")
            with open(temp_gpx_path, "wb") as f:
                f.write(uploaded_gpx_file.getbuffer())
            
            duration_minutes, distance_km, start_date, sport = parse_gpx_data(temp_gpx_path)
            
            if duration_minutes > 0:
                st.session_state[f"{prefix}dauer_total_minutes_input"] = duration_minutes
                st.success(f"Dauer aus GPX-Datei erkannt: {format_duration(duration_minutes)}.")
            if distance_km > 0.0:
                st.session_state[f"{prefix}distanz_input"] = round(distance_km, 2)
                st.success(f"Distanz aus GPX-Datei erkannt: {round(distance_km, 2)} km.")
            if start_date:
                st.session_state[f"{prefix}date_input"] = start_date
                st.success(f"Datum aus GPX-Datei erkannt: {start_date.strftime('%Y-%m-%d')}.")
            if sport:
                st.session_state[f"{prefix}sportart_input"] = sport
                st.success(f"Sportart aus GPX-Datei erkannt: {sport}.")

            if os.path.exists(temp_gpx_path):
                os.remove(temp_gpx_path)
            st.rerun()
        else:
            st.warning("Bitte lade zuerst eine GPX-Datei hoch, um sie auszuwerten.")

    # Button zum Parsen der FIT-Daten
    if st.button("FIT-Datei auswerten", key=f"{prefix}parse_fit_button"):
        if uploaded_fit_file:
            temp_fit_path = os.path.join(UPLOAD_DIR, "temp_fit_for_parsing.fit")
            with open(temp_fit_path, "wb") as f:
                f.write(uploaded_fit_file.getbuffer())
            
            duration_minutes, distance_km, start_date, sport, average_heart_rate = parse_fit_data(temp_fit_path)
            
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

            if os.path.exists(temp_fit_path):
                os.remove(temp_fit_path)
            st.rerun()
        else:
            st.warning("Bitte lade zuerst eine FIT-Datei hoch, um sie auszuwerten.")

    st.write("---")

    # --- Das Formular selbst ---
    with st.form(key=f"{prefix}workout_form"):
        # Zeige aktuelle Dateipfade im Bearbeitungsmodus an
        if is_edit_mode:
            st.markdown(f"**Aktuelles Bild:** {os.path.basename(st.session_state.get(f'{prefix}current_image_path', '')) if st.session_state.get(f'{prefix}current_image_path') else 'Kein Bild'}")
            st.markdown(f"**Aktuelle GPX-Datei:** {os.path.basename(st.session_state.get(f'{prefix}current_gpx_path', '')) if st.session_state.get(f'{prefix}current_gpx_path') else 'Keine GPX-Datei'}")
            st.markdown(f"**Aktuelle EKG-Datei:** {os.path.basename(st.session_state.get(f'{prefix}current_ekg_path', '')) if st.session_state.get(f'{prefix}current_ekg_path') else 'Keine EKG-Datei'}")
            st.markdown(f"**Aktuelle FIT-Datei:** {os.path.basename(st.session_state.get(f'{prefix}current_fit_path', '')) if st.session_state.get(f'{prefix}current_fit_path') else 'Keine FIT-Datei'}")
            st.markdown("---")

        # Verwende get() für die value-Parameter, um KeyError zu vermeiden, falls ein Wert mal fehlen sollte
        # Workout Name ist jetzt das erste Eingabefeld
        #name = st.text_input("Name des Workouts", placeholder="Test 1", value=st.session_state.get(f"{prefix}name_input", ""), key=f"{prefix}name_input_form")
        
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

        # Aktualisiere den Session State für die Gesamtdauer in Minuten, falls sich die Stunden/Minuten ändern
        if dauer_to_save != st.session_state.get(f"{prefix}dauer_total_minutes_input"):
            st.session_state[f"{prefix}dauer_total_minutes_input"] = dauer_to_save
            # st.rerun() # Ggf. rerun hier, wenn Änderungen sofort visuell werden sollen

        distanz = st.number_input("Distanz (in km)", min_value=0.0, step=0.1, value=st.session_state.get(f"{prefix}distanz_input", 0.0), key=f"{prefix}distanz_input_form")
        puls = st.number_input("Puls (in bpm)", min_value=0, step=1, value=st.session_state.get(f"{prefix}puls_input", 0), key=f"{prefix}puls_input_form")
        kalorien = st.number_input("Kalorien (in kcal)", min_value=0, step=1, value=st.session_state.get(f"{prefix}kalorien_input", 0), key=f"{prefix}kalorien_input_form")

        st.write("---")
        
        # Submit-Button für das gesamte Formular (ohne Key!)
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
            # Verwende get() hier auch für die Werte, die von den Buttons kommen könnten
            elif st.session_state.get(f"{prefix}selected_antrengung") is None:
                st.error("Bitte bewerte die Anstrengung des Trainings.")
                return None
            elif st.session_state.get(f"{prefix}selected_star_rating") is None:
                st.error("Bitte gib eine Sternebewertung ab.")
                return None
            
            # Dateipfade handhaben: Neue Uploads überschreiben alte Pfade
            link_image = save_uploaded_file(uploaded_image_file, "img", name) or st.session_state.get(f"{prefix}current_image_path")
            link_gpx = save_uploaded_file(uploaded_gpx_file, "gpx", name) or st.session_state.get(f"{prefix}current_gpx_path")
            link_ekg = save_uploaded_file(uploaded_ekg_file, "ekg", name) or st.session_state.get(f"{prefix}current_ekg_path")
            link_fit = save_uploaded_file(uploaded_fit_file, "fit", name) or st.session_state.get(f"{prefix}current_fit_path")

            return {
                "name": name,
                "date": date.strftime("%Y-%m-%d"),
                "sportart": sportart,
                "dauer": dauer_to_save, # Speichere die Dauer immer noch in Minuten
                "distanz": distanz,
                "puls": puls,
                "kalorien": kalorien,
                "anstrengung": st.session_state[f"{prefix}selected_antrengung"], # Diese sind immer gesetzt, da Buttons reruns
                "star_rating": st.session_state[f"{prefix}selected_star_rating"], # diese
                "description": description,
                "image": link_image,
                "gpx_file": link_gpx,
                "ekg_file": link_ekg,
                "fit_file": link_fit
            }
        # Cancel-Button (für den Bearbeitungsmodus), ebenfalls ohne Key!
        if is_edit_mode:
            cancel_submitted = st.form_submit_button("Abbrechen")
            if cancel_submitted:
                return "CANCEL"
    
    return None
 