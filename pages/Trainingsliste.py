import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
import gpxpy
import gpxpy.gpx
from streamlit_folium import folium_static
import os
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import fitparse
from tinydb import TinyDB, Query


# --- Konfiguration und Initialisierung ---
IMAGE_DIR = "images"
DATA_DIR = "data"
UPLOAD_DIR = "uploaded_files"

def initialize_directories():
    """Stellt sicher, dass notwendige Verzeichnisse existieren."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen für die Datenverarbeitung und Dateihandhabung ---

def get_absolute_path(path_from_db):
    """
    Versucht, einen Dateipfad, der aus der Datenbank gelesen wurde,
    in einen absoluten, existierenden Pfad auf dem Dateisystem umzuwandeln.

    Args:
        path_from_db (str): Der Dateipfad, wie er in der Datenbank gespeichert ist.

    Returns:
        str oder None: Der absolute Pfad zur Datei, wenn gefunden, sonst None.
    """
    if not path_from_db or path_from_db == "-":
        return None

    # Ermittle das absolute Verzeichnis, in dem das Streamlit-Skript ausgeführt wird.
    # Dies ist der Ankerpunkt für alle relativen Pfade.
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Versuche, den Pfad aufzulösen (von spezifisch zu allgemeiner) ---

    # 1. Fall: Der Pfad in der DB ist bereits ein vollständiger absoluter Pfad (z.B. C:\User\...)
    # Dies ist seltener, wenn Sie relative Pfade speichern, aber möglich.
    if os.path.isabs(path_from_db):
        if os.path.exists(path_from_db):
            return path_from_db
        # Wenn der absolute Pfad nicht existiert, versuchen wir andere Relativ-Pfade als Fallback
        # Das kann passieren, wenn die Anwendung auf ein anderes System verschoben wird.

    # 2. Fall: Der Pfad in der DB ist relativ zum Skript-Verzeichnis.
    # Dies ist der häufigste Fall für hochgeladene Dateien (z.B. "uploaded_files/mein_bild.png").
    candidate_path_relative_to_script = os.path.join(script_dir, path_from_db)
    if os.path.exists(candidate_path_relative_to_script):
        return candidate_path_relative_to_script

    # 3. Fall: Der Pfad in der DB ist *nur* der Dateiname (z.B. "mein_bild.png"),
    # aber die Datei liegt in einem deiner vordefinierten Upload/Image-Verzeichnisse
    # (relativ zum Skript-Verzeichnis). Dies ist ein wichtiger Fallback.
    base_filename = os.path.basename(path_from_db) # Extrahiert nur den Dateinamen

    candidate_path_in_upload_dir = os.path.join(script_dir, UPLOAD_DIR, base_filename)
    if os.path.exists(candidate_path_in_upload_dir):
        return candidate_path_in_upload_dir

    candidate_path_in_image_dir = os.path.join(script_dir, IMAGE_DIR, base_filename)
    if os.path.exists(candidate_path_in_image_dir):
        return candidate_path_in_image_dir
    
    # 4. Fall: Der Pfad könnte in der DB ohne das "uploaded_files/" Präfix gespeichert sein,
    # aber er ist als Pfad *innerhalb* des UPLOAD_DIR gemeint.
    # Beispiel: DB speichert "2023/bild.png", und UPLOAD_DIR ist "uploaded_files/".
    # Dann wäre der vollständige Pfad "uploaded_files/2023/bild.png".
    if path_from_db.startswith(f"{UPLOAD_DIR}{os.sep}"): # Prüft, ob der Pfad schon das UPLOAD_DIR enthält
        pass # Schon von candidate_path_relative_to_script abgedeckt
    else:
        candidate_path_within_upload_dir_full = os.path.join(script_dir, UPLOAD_DIR, path_from_db)
        if os.path.exists(candidate_path_within_upload_dir_full):
            return candidate_path_within_upload_dir_full

    # Wenn nach allen Versuchen kein existierender Pfad gefunden wurde
    return None


def load_gpx_data(gpx_filepath):
    """
    Lädt und parst eine GPX-Datei.
    Gibt ein gpxpy.GPX-Objekt oder None bei Fehler zurück.
    """
    #abs_filepath = get_absolute_path(gpx_filepath)
    if not gpx_filepath or not os.path.exists(gpx_filepath):
        return None
    try:
        with open(gpx_filepath, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            return gpx
    except FileNotFoundError:
        st.error(f"Fehler: GPX-Datei '{gpx_filepath}' wurde nicht gefunden.")
        return None
    except gpxpy.gpx.GPXException as e:
        st.error(f"Fehler beim Parsen der GPX-Datei '{gpx_filepath}': {e}.")
        return None
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten beim Laden von '{gpx_filepath}': {e}")
        return None

def load_ekg_data(ekg_filepath):
    """
    Lädt den Inhalt einer EKG-Datei (oder einer beliebigen Textdatei).
    Gibt den Dateiinhalt als String oder None bei Fehler zurück.
    """
    #abs_filepath = get_absolute_path(ekg_filepath)
    if not ekg_filepath or not os.path.exists(ekg_filepath):
        return None
    try:
        with open(ekg_filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Fehler: EKG-Datei '{ekg_filepath}' wurde nicht gefunden.")
        return None
    except Exception as e:
        st.error(f"Fehler beim Lesen der EKG-Datei '{ekg_filepath}': {e}")
        return None

def load_fit_data(fit_filepath):
    """
    Lädt und parst eine FIT-Datei und extrahiert relevante Daten.
    Gibt ein Pandas DataFrame mit Zeit, Herzfrequenz, Leistung usw. zurück oder None bei Fehler.
    """
    #abs_filepath = get_absolute_path(fit_filepath)
    if not fit_filepath or not os.path.exists(fit_filepath):
        return None
    try:
        fitfile = fitparse.FitFile(fit_filepath)

        time = []
        velocity = []
        heartrate = []
        distance = []
        cadence = []
        power = []

        for record in fitfile.get_messages('record'):
            timestamp = None
            speed_val = None
            hr_val = None
            dist_val = None
            cadence_val = None
            power_val = None

            for record_data in record:
                if record_data.name == "timestamp":
                    timestamp = record_data.value
                elif record_data.name == "speed":
                    speed_val = record_data.value
                elif record_data.name == "heart_rate":
                    hr_val = record_data.value
                elif record_data.name == "distance":
                    dist_val = record_data.value
                elif record_data.name == "cadence":
                    cadence_val = record_data.value
                elif record_data.name == "power":
                    power_val = record_data.value

            if timestamp is not None:
                time.append(timestamp)
                velocity.append(speed_val)
                heartrate.append(hr_val)
                distance.append(dist_val)
                cadence.append(cadence_val)
                power.append(power_val)

        df = pd.DataFrame({
            "time": time,
            "velocity": velocity,
            "heart_rate": heartrate,
            "distance": distance,
            "cadence": cadence,
            "power": power
        })
        df = df.fillna(method='ffill').fillna(method='bfill')
        return df

    except FileNotFoundError:
        st.error(f"Fehler: FIT-Datei '{fit_filepath}' wurde nicht gefunden.")
        return None
    except fitparse.FitParseError as e:
        st.error(f"Fehler beim Parsen der FIT-Datei '{fit_filepath}': {e}.")
        return None
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten beim Laden von '{fit_filepath}': {e}")
        return None

# --- UI-Komponenten als Funktionen ---

def display_gpx_on_map_ui(gpx_object):
    """
    Zeigt einen GPX-Track auf einer Folium-Karte an.
    Erwartet ein geparstes gpxpy.GPX-Objekt.
    """
    if not gpx_object or not gpx_object.tracks:
        st.markdown("Keine GPX-Daten zum Anzeigen vorhanden.")
        return

    has_points = False
    for track in gpx_object.tracks:
        for segment in track.segments:
            if segment.points:
                has_points = True
                break
        if has_points:
            break
    
    if not has_points:
        st.warning("GPX-Track hat keine Punkte für die Karte.")
        return

    first_point = None
    for track in gpx_object.tracks:
        if track.segments and track.segments[0].points:
            first_point = track.segments[0].points[0]
            break
    
    if not first_point:
        st.warning("Konnte keinen Startpunkt für die Karte finden.")
        return


    m = folium.Map(location=[first_point.latitude, first_point.longitude], zoom_start=13)

    for track in gpx_object.tracks:
        for segment in track.segments:
            points = [(point.latitude, point.longitude) for point in segment.points]
            if points:
                folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(m)

    bounds = gpx_object.get_bounds()
    if bounds:
        m.fit_bounds([[bounds.min_latitude, bounds.min_longitude], [bounds.max_latitude, bounds.max_longitude]])

    folium_static(m)

def display_elevation_profile_ui(gpx_object):
    """
    Zeigt ein Höhenprofil basierend auf GPX-Daten an.
    Erwartet ein geparstes gpxpy.GPX-Objekt.
    """
    if not gpx_object or not gpx_object.tracks:
        st.markdown("Keine GPX-Daten für das Höhenprofil vorhanden.")
        return

    elevations = []
    distances = []
    total_distance_km = 0.0

    for track in gpx_object.tracks:
        for segment in track.segments:
            for i, point in enumerate(segment.points):
                if point.elevation is not None:
                    elevations.append(point.elevation)
                    if i > 0:
                        dist_inc_m = point.distance_2d(segment.points[i-1])
                        total_distance_km += dist_inc_m / 1000.0
                    distances.append(total_distance_km)

    if not elevations:
        st.warning("Keine Höheninformationen in der GPX-Datei gefunden.")
        return

    df_elevation = pd.DataFrame({
        'Distanz (km)': distances,
        'Höhe (m)': elevations
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_elevation['Distanz (km)'],
        y=df_elevation['Höhe (m)'],
        mode='lines',
        name='Höhenprofil',
        line=dict(width=3, color='rgb(63, 103, 126)'),
        fill='tozeroy',
        fillcolor='rgba(120, 171, 203, 0.4)'
    ))

    fig.update_layout(
        title_text='Höhenprofil',
        title_x=0.5,
        xaxis_title='Distanz (km)',
        yaxis_title='Höhe (m)',
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black'),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='LightGrey'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='LightGrey'
    )

    st.plotly_chart(fig, use_container_width=True)

def display_fit_data_ui(fit_df):
    """
    Zeigt Herzfrequenz- und Leistungskurven aus FIT-Daten an.
    Erwartet ein Pandas DataFrame mit 'time', 'heart_rate' und 'power' Spalten.
    """
    if fit_df is None or fit_df.empty:
        st.markdown("Keine FIT-Daten zum Anzeigen vorhanden.")
        return

    st.subheader("FIT-Daten Analyse")

    if not pd.api.types.is_datetime64_any_dtype(fit_df['time']):
        try:
            fit_df['time'] = pd.to_datetime(fit_df['time'])
        except Exception:
            st.error("Konnte 'time' Spalte in FIT-Daten nicht in Datetime konvertieren.")
            return

    if 'heart_rate' in fit_df.columns and fit_df['heart_rate'].dropna().any():
        fig_hr = px.line(fit_df, x='time', y='heart_rate', title='Herzfrequenz über die Zeit',
                         labels={'time': 'Zeit', 'heart_rate': 'Herzfrequenz (bpm)'})
        fig_hr.update_layout(hovermode="x unified")
        st.plotly_chart(fig_hr, use_container_width=True)
    else:
        st.info("Keine Herzfrequenzdaten in der FIT-Datei gefunden.")

    if 'power' in fit_df.columns and fit_df['power'].dropna().any():
        fig_power = px.line(fit_df, x='time', y='power', title='Leistung über die Zeit',
                            labels={'time': 'Zeit', 'power': 'Leistung (Watt)'})
        fig_power.update_layout(hovermode="x unified")
        st.plotly_chart(fig_power, use_container_width=True)
    else:
        st.info("Keine Leistungsdaten in der FIT-Datei gefunden.")

    if 'velocity' in fit_df.columns and fit_df['velocity'].dropna().any():
        fig_vel = px.line(fit_df, x='time', y='velocity', title='Geschwindigkeit über die Zeit',
                          labels={'time': 'Zeit', 'velocity': 'Geschwindigkeit (m/s)'})
        fig_vel.update_layout(hovermode="x unified")
        st.plotly_chart(fig_vel, use_container_width=True)

    if 'cadence' in fit_df.columns and fit_df['cadence'].dropna().any():
        fig_cad = px.line(fit_df, x='time', y='cadence', title='Trittfrequenz über die Zeit',
                          labels={'time': 'Zeit', 'cadence': 'Trittfrequenz (rpm)'})
        fig_cad.update_layout(hovermode="x unified")
        st.plotly_chart(fig_cad, use_container_width=True)


def display_training_details_ui(training_data, on_delete_callback, on_edit_callback, expanded=False):
    """
    Zeigt die Details eines einzelnen Trainings in einem Expander an.
    `expanded` steuert, ob der Expander beim Laden offen ist.
    """
    training_id_str = str(training_data.doc_id) if hasattr(training_data, 'doc_id') else str(training_data.get('id', 'no_id'))
    
    expander_title = f"**{training_data['name']}** - {training_data['date']} ({training_data['sportart']})"
    
    with st.expander(expander_title, expanded=expanded):
        st.markdown(f"**Datum:** {training_data['date']}")
        st.markdown(f"**Sportart:** {training_data['sportart']}")
        st.markdown(f"**Dauer:** {training_data.get('dauer', 'N/A')} min") 
        st.markdown(f"**Distanz:** {training_data.get('distanz', 'N/A')} km")
        st.markdown(f"**Puls:** {training_data.get('puls', 'N/A')} bpm (avg)")
        st.markdown(f"**Kalorien:** {training_data.get('kalorien', 'N/A')} kcal")
        
        anstrengung_map = {
            "good": "😃 Sehr leicht",
            "ok": "🙂 leicht",
            "neutral": "😐 Neutral",
            "acceptable": "😟 anstrengend",
            "bad": "🥵 sehr anstrengend"
        }
        st.markdown(f"**Anstrengung:** {anstrengung_map.get(training_data.get('anstrengung', ''), 'N/A')}")
        st.markdown(f"**Bewertung:** {'⭐' * training_data.get('star_rating', 0)}")

        st.markdown(f"**Beschreibung:**")
        description = training_data.get('description', '')
        if description:
            st.info(description)
        else:
            st.markdown("Keine Beschreibung vorhanden.")

        image_path = training_data.get('image') # Dies liest den Pfad aus Ihrer DB
        if image_path and image_path != "-": # Stellt sicher, dass ein Pfad vorhanden ist
            local_image_path = image_path # <<< Hier wird die Magie der Pfadauflösung vollbracht
            if local_image_path and os.path.exists(local_image_path):
                st.image(local_image_path, caption=f"Bild für {training_data['name']}", use_container_width=True)
            else:
                # Wichtige Debug-Ausgabe, wenn das Bild nicht gefunden wird
                st.warning(f"Bilddatei '{image_path}' konnte nicht unter dem aufgelösten Pfad '{local_image_path}' gefunden werden. Bitte prüfen Sie, ob die Datei existiert und der Pfad in der DB korrekt ist.")

        st.markdown("**Verlinkte Dateien:**")

        gpx_file_path = training_data.get('gpx_file')
        if gpx_file_path and gpx_file_path != "-":
            gpx_data = load_gpx_data(gpx_file_path)
            if gpx_data:
                st.markdown("### GPX-Track auf Karte")
                display_gpx_on_map_ui(gpx_data)
                st.markdown("---")
                st.markdown("### Höhenprofil")
                display_elevation_profile_ui(gpx_data)
        else:
            st.markdown("Keine GPX-Datei verlinkt.")

        fit_file_path = training_data.get('fit_file')
        if fit_file_path and fit_file_path != "-":
            fit_data_df = load_fit_data(fit_file_path)
            if fit_data_df is not None and not fit_data_df.empty:
                st.markdown("---")
                st.markdown("### FIT-Dateianalyse")
                display_fit_data_ui(fit_data_df)
            else:
                st.markdown("Keine FIT-Datei verlinkt oder Daten konnten nicht geladen werden.")

        ekg_file_path = training_data.get('ekg_file')
        if ekg_file_path and ekg_file_path != "-":
            ekg_content = load_ekg_data(ekg_file_path)
            if ekg_content:
                st.markdown(f"- **EKG-Datei ({ekg_file_path}):**")
                st.code(ekg_content, language='text')
            else:
                if not (gpx_file_path and gpx_file_path != "-") and \
                   not (fit_file_path and fit_file_path != "-"):
                    st.markdown("Keine weiteren Dateien verlinkt.")
        else:
            if not (gpx_file_path and gpx_file_path != "-") and \
               not (fit_file_path and fit_file_path != "-") and \
               not (ekg_file_path and ekg_file_path != "-"):
                st.markdown("Keine weiteren Dateien verlinkt.")

        st.markdown("---")

        col_edit, col_delete, col_spacer = st.columns([0.15, 0.15, 0.7])
        with col_edit:
            if st.button("Bearbeiten 📝", key=f"edit_btn_{training_id_str}"):
                on_edit_callback(training_data.doc_id)
                st.rerun()
        with col_delete:
            if st.button("Löschen 🗑️", key=f"delete_btn_{training_id_str}"):
                on_delete_callback(training_data.doc_id, st.session_state.current_user_id)
                st.success(f"Training '{training_data['name']}' vom {training_data['date']} wurde gelöscht.")
                st.rerun()

def display_training_list_ui(trainings):
    """
    Zeigt die Liste aller Trainings an.
    """
    if not trainings:
        st.info("Es sind noch keine Trainings für diese Person vorhanden. Füge Trainings hinzu, damit sie hier angezeigt werden! ")
        if st.button("Trainings hinzufügen"):
            st.switch_page("pages/add workout.py")
        return

    sorted_trainings = sorted(
        trainings,
        key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"),
        reverse=True
    )

    if 'last_expanded_training_id' not in st.session_state:
        st.session_state.last_expanded_training_id = None

    if sorted_trainings and st.session_state.get('initial_expand_done', False) == False:
        st.session_state.last_expanded_training_id = sorted_trainings[0].doc_id
        st.session_state.initial_expand_done = True

    for i, training in enumerate(sorted_trainings):
        is_expanded = (training.doc_id == st.session_state.last_expanded_training_id)
        display_training_details_ui(training, delete_training_from_db, set_training_to_edit, expanded=is_expanded)

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
        user_trainings = [t for t in all_trainings if t.doc_id in ekg_test_ids]
        return user_trainings
    return []

def delete_training_from_db(training_id, person_id):
    """Löscht ein Training aus dbtests und seine ID aus der ekg_tests Liste in dbperson."""
    try:
        db.remove(doc_ids=[training_id])
        st.success(f"Training mit ID {training_id} erfolgreich aus der Trainingsdatenbank gelöscht.")

        person_doc = dp.get(doc_id=int(person_id))
        if person_doc:
            current_ekg_tests = person_doc.get('ekg_tests', [])
            if training_id in current_ekg_tests:
                current_ekg_tests.remove(training_id)
                dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_id)])
                st.success(f"Training ID {training_id} erfolgreich aus der Personendatenbank für Person {person_id} entfernt.")
            else:
                st.warning(f"Training ID {training_id} wurde nicht in der EKG-Testliste für Person {person_id} gefunden.")
        else:
            st.error(f"Fehler: Person mit ID {person_id} nicht in der Personendatenbank gefunden.")
    except Exception as e:
        st.error(f"Fehler beim Löschen des Trainings: {e}")


def set_training_to_edit(training_id):
    """Setzt die ID des Trainings, das bearbeitet werden soll, im Session State."""
    st.session_state.editing_training_id = training_id

def update_training_in_db(updated_training_data, training_doc_id):
    """Aktualisiert ein Training in der TinyDB."""
    try:
        db.update(updated_training_data, doc_ids=[training_doc_id])
        st.session_state.editing_training_id = None
        # Setze last_editing_id zurück, damit beim nächsten Edit die Werte neu geladen werden
        st.session_state.last_editing_id = None 
        st.session_state.initial_expand_done = False
        st.rerun()
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren des Trainings: {e}")

def edit_training_ui(training_data):
    """
    Zeigt ein Formular zum Bearbeiten eines Trainings an, ähnlich wie 'add_workout'.
    """
    st.subheader(f"Training bearbeiten: {training_data['name']}")
    
    # Zustand für die Smiley- und Sterne-Buttons im Bearbeitungsformular
    # Setze initial nur, wenn der editing_training_id neu ist oder nicht das gleiche Training ist
    if st.session_state.get('last_editing_id') != training_data.doc_id:
        st.session_state.edit_selected_antrengung = training_data.get('anstrengung', None)
        st.session_state.edit_selected_star_rating = training_data.get('star_rating', None)
    
    # Speichere die aktuelle ID, um zu erkennen, wann ein neues Training zum Editieren ausgewählt wurde
    st.session_state.last_editing_id = training_data.doc_id

    # --- Anstrengungsauswahl (Buttons außerhalb des Formulars) ---
    st.write("---")
    st.write("Wie anstrengend war das Training?")
    
    # Sicherstellen, dass der Wert aus dem Session State gelesen wird
    antrengung_value = st.session_state.edit_selected_antrengung 

    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Logik für Smiley-Buttons: Ähnlich wie Sterne, Button wird zu Text bei Auswahl
    with col1:
        if antrengung_value == "good":
            st.markdown("### 😃 Sehr leicht") # Highlighted
        elif st.button("😃 Sehr leicht", key=f"smiley_good_{training_data.doc_id}"): # Eindeutiger Key
            st.session_state.edit_selected_antrengung = "good"
            st.rerun()
    with col2:
        if antrengung_value == "ok":
            st.markdown("### 🙂 leicht") # Highlighted
        elif st.button("🙂 leicht", key=f"smiley_ok_{training_data.doc_id}"): # Eindeutiger Key
            st.session_state.edit_selected_antrengung = "ok"
            st.rerun()
    with col3:
        if antrengung_value == "neutral":
            st.markdown("### 😐 Neutral") # Highlighted
        elif st.button("😐 Neutral", key=f"smiley_neutral_{training_data.doc_id}"): # Eindeutiger Key
            st.session_state.edit_selected_antrengung = "neutral"
            st.rerun()
    with col4:
        if antrengung_value == "acceptable":
            st.markdown("### 😟 anstrengend") # Highlighted
        elif st.button("😟 anstrengend", key=f"smiley_acceptable_{training_data.doc_id}"): # Eindeutiger Key
            st.session_state.edit_selected_antrengung = "acceptable"
            st.rerun()
    with col5:
        if antrengung_value == "bad":
            st.markdown("### 🥵 sehr anstrengend") # Highlighted
        elif st.button("🥵 sehr anstrengend", key=f"smiley_bad_{training_data.doc_id}"): # Eindeutiger Key
            st.session_state.edit_selected_antrengung = "bad"
            st.rerun()

    # --- Sternebewertung (Highlighting Implementierung) ---
    st.write("---")
    st.write("Wie würdest du dieses Workout bewerten?")
    
    # Sicherstellen, dass der Wert aus dem Session State gelesen wird
    star_rating_value = st.session_state.edit_selected_star_rating 

    cols_stars = st.columns(5)
    for i in range(1, 6):
        with cols_stars[i-1]:
            # Wenn der aktuelle Stern der ausgewählte ist, zeige ihn als fettgedruckten Text
            if star_rating_value == i:
                st.markdown(f"**{'⭐' * i}**") # Verwende Markdown für fette Sterne
            # Andernfalls zeige den Button an
            elif st.button("⭐" * i, key=f"edit_star_button_{i}_{training_data.doc_id}"): # Eindeutiger Key
                st.session_state.edit_selected_star_rating = i
                st.rerun() # Führt einen Rerun aus, um den "gehighlighteten" Zustand zu zeigen


    st.write("---") # Trennlinie vor dem Formular

    # --- Das Bearbeitungsformular selbst ---
    with st.form(key=f"edit_training_form_{training_data.doc_id}"):
        edited_name = st.text_input("Name", value=training_data['name'])
        
        # Datumshandhabung: string aus DB zu datetime Objekt für date_input
        date_obj = datetime.strptime(training_data['date'], "%Y-%m-%d").date()
        edited_date = st.date_input("Datum", value=date_obj)
        
        edited_sportart = st.text_input("Sportart", value=training_data['sportart'])

        st.write("---") # Trennlinie für Dateiuploads
        
        current_image_path = training_data.get('image', '')
        current_gpx_path = training_data.get('gpx_file', '')
        current_ekg_path = training_data.get('ekg_file', '')
        current_fit_path = training_data.get('fit_file', '')

        st.markdown(f"**Aktuelles Bild:** {os.path.basename(current_image_path) if current_image_path else 'Kein Bild'}")
        uploaded_image = st.file_uploader("Neues Bild hochladen (ersetzt aktuelles)", type=["jpg", "jpeg", "png"], key=f"image_uploader_edit_{training_data.doc_id}")

        st.markdown(f"**Aktuelle GPX-Datei:** {os.path.basename(current_gpx_path) if current_gpx_path else 'Keine GPX-Datei'}")
        uploaded_gpx = st.file_uploader("Neue GPX-Datei hochladen (ersetzt aktuelle)", type=["gpx"], key=f"gpx_uploader_edit_{training_data.doc_id}")
        
        st.markdown(f"**Aktuelle EKG-Datei:** {os.path.basename(current_ekg_path) if current_ekg_path else 'Keine EKG-Datei'}")
        uploaded_ekg = st.file_uploader("Neue EKG-Datei hochladen (ersetzt aktuelle)", type=["csv", "txt"], key=f"ekg_uploader_edit_{training_data.doc_id}")

        st.markdown(f"**Aktuelle FIT-Datei:** {os.path.basename(current_fit_path) if current_fit_path else 'Keine FIT-Datei'}")
        uploaded_fit = st.file_uploader("Neue FIT-Datei hochladen (ersetzt aktuelle)", type=["fit"], key=f"fit_uploader_edit_{training_data.doc_id}")

        edited_description = st.text_area("Beschreibung", value=training_data.get('description', ''))
        
        st.write("---")
        st.write("Kerninformationen zum Workout (falls nicht in Uploads enthalten):")
        edited_dauer = st.number_input("Dauer (in Minuten)", min_value=0, step=1, value=int(training_data.get('dauer', 0)))
        edited_distanz = st.number_input("Distanz (in km)", min_value=0.0, step=0.1, value=float(training_data.get('distanz', 0.0)))
        edited_puls = st.number_input("Puls (in bpm)", min_value=0, step=1, value=int(training_data.get('puls', 0)))
        edited_kalorien = st.number_input("Kalorien (in kcal)", min_value=0, step=1, value=int(training_data.get('kalorien', 0)))

        # Submit- und Cancel-Buttons innerhalb des Formulars
        col_submit, col_cancel = st.columns([0.2, 0.8])
        with col_submit:
            submit_button = st.form_submit_button("Änderungen speichern")
        with col_cancel:
            cancel_button = st.form_submit_button("Abbrechen")

        if submit_button:
            # Validierung der Auswahl, die außerhalb des Formulars getroffen wurde
            if st.session_state.edit_selected_antrengung is None:
                st.error("Bitte bewerte die Anstrengung des Trainings.")
                return
            elif st.session_state.edit_selected_star_rating is None:
                st.error("Bitte gib eine Sternebewertung ab.")
                return
            
            new_image_path = save_uploaded_file(uploaded_image, "img", edited_name) if uploaded_image else current_image_path
            new_gpx_path = save_uploaded_file(uploaded_gpx, "gpx", edited_name) if uploaded_gpx else current_gpx_path
            new_ekg_path = save_uploaded_file(uploaded_ekg, "ekg", edited_name) if uploaded_ekg else current_ekg_path
            new_fit_path = save_uploaded_file(uploaded_fit, "fit", edited_name) if uploaded_fit else current_fit_path

            updated_training = {
                "name": edited_name,
                "date": edited_date.strftime("%Y-%m-%d"),
                "sportart": edited_sportart,
                "dauer": edited_dauer,
                "distanz": edited_distanz,
                "puls": edited_puls,
                "kalorien": edited_kalorien,
                "anstrengung": st.session_state.edit_selected_antrengung, # Wert aus Session State
                "star_rating": st.session_state.edit_selected_star_rating, # Wert aus Session State
                "description": edited_description,
                "image": new_image_path,
                "gpx_file": new_gpx_path,
                "ekg_file": new_ekg_path,
                "fit_file": new_fit_path
            }
            update_training_in_db(updated_training, training_data.doc_id)
        elif cancel_button:
            st.session_state.editing_training_id = None
            st.session_state.last_editing_id = None # Reset
            st.session_state.initial_expand_done = False
            st.rerun()


def save_uploaded_file(uploaded_file, file_prefix, workout_name):
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = uploaded_file.name.split(".")[-1]
        safe_name = workout_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        file_path = os.path.join(UPLOAD_DIR, f"{safe_name}_{file_prefix}_{timestamp}.{file_extension}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

# --- Hauptanwendung ---
def main():
    st.title("Dein Trainings-Tagebuch 🏋️‍♂️")
    st.markdown("---")

    initialize_directories()

    if "current_user_id" not in st.session_state:
        st.warning("Bitte wähle im Dashboard zuerst eine Person aus.")
        return

    if 'editing_training_id' not in st.session_state:
        st.session_state.editing_training_id = None
    
    if 'initial_expand_done' not in st.session_state:
        st.session_state.initial_expand_done = False

    if 'last_editing_id' not in st.session_state:
        st.session_state.last_editing_id = None

    trainings_for_user = get_trainings_for_current_user()

    if st.session_state.editing_training_id is not None:
        training_to_edit = None
        for t in trainings_for_user:
            if t.doc_id == st.session_state.editing_training_id:
                training_to_edit = t
                break
        
        if training_to_edit:
            edit_training_ui(training_to_edit)
        else:
            st.error("Training zum Bearbeiten nicht gefunden oder gehört nicht zur ausgewählten Person.")
            st.session_state.editing_training_id = None
            st.session_state.last_editing_id = None # Reset
            st.session_state.initial_expand_done = False
            st.rerun()
    else:
        st.subheader("Deine Trainingsübersicht")
        display_training_list_ui(trainings_for_user)

if __name__ == "__main__":
    main()
