
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

# Importiere die Hilfsfunktionen zum Speichern von Dateien und Parsen von GPX/FIT
# (Diese sind nun im workout_form_utils, aber die Pfadauflösung wird noch hier benötigt)
# Da diese Datei die Pfade auflöst, belassen wir get_absolute_path hier.

# --- Konfiguration und Initialisierung ---
IMAGE_DIR = "images"
DATA_DIR = "data"
UPLOAD_DIR = "uploaded_files" # Muss hier auch definiert sein, da get_absolute_path es verwendet

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

# --- Hilfsfunktionen für die Datenverarbeitung und Dateihandhabung (beibehalten in trainingsliste.py) ---

def load_gpx_data(gpx_filepath):
    """
    Lädt und parst eine GPX-Datei.
    Gibt ein gpxpy.GPX-Objekt oder None bei Fehler zurück.
    """
    abs_filepath = gpx_filepath # Wichtig: Pfadauflösung hier
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    try:
        with open(abs_filepath, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            return gpx
    except FileNotFoundError:
        st.error(f"Fehler: GPX-Datei {repr(gpx_filepath)} wurde nicht gefunden.") # Korrigiert: repr()
        return None
    except gpxpy.gpx.GPXException as e:
        st.error(f"Fehler beim Parsen der GPX-Datei {repr(gpx_filepath)}: {e}.") # Korrigiert: repr()
        return None
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten beim Laden von {repr(gpx_filepath)}: {e}") # Korrigiert: repr()
        return None

def load_ekg_data(ekg_filepath):
    """
    Lädt den Inhalt einer EKG-Datei (oder einer beliebigen Textdatei).
    Gibt den Dateiinhalt als String oder None bei Fehler zurück.
    """
    abs_filepath = ekg_filepath # Wichtig: Pfadauflösung hier
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    try:
        with open(abs_filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Fehler: EKG-Datei {repr(ekg_filepath)} wurde nicht gefunden.") # Korrigiert: repr()
        return None
    except Exception as e:
        st.error(f"Fehler beim Lesen der EKG-Datei {repr(ekg_filepath)}: {e}") # Korrigiert: repr()
        return None

def load_fit_data(fit_filepath):
    """
    Lädt und parst eine FIT-Datei und extrahiert relevante Daten.
    Gibt ein Pandas DataFrame mit Zeit, Herzfrequenz, Leistung usw. zurück oder None bei Fehler.
    """
    abs_filepath = fit_filepath # Wichtig: Pfadauflösung hier
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    try:
        fitfile = fitparse.FitFile(abs_filepath)

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
        # Füllen Sie NaN-Werte vor und zurück auf, um durchgehende Linien in Plots zu gewährleisten
        df = df.fillna(method='ffill').fillna(method='bfill')
        return df

    except FileNotFoundError:
        st.error(f"Fehler: FIT-Datei {repr(fit_filepath)} wurde nicht gefunden.") # Korrigiert: repr()
        return None
    except fitparse.FitParseError as e:
        st.error(f"Fehler beim Parsen der FIT-Datei {repr(fit_filepath)}: {e}.") # Korrigiert: repr()
        return None
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten beim Laden von {repr(fit_filepath)}: {e}") # Korrigiert: repr()
        return None

# --- UI-Komponenten als Funktionen (beibehalten) ---

def display_gpx_on_map_ui(gpx_object):
    """Zeigt einen GPX-Track auf einer Folium-Karte an."""
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
    """Zeigt ein Höhenprofil basierend auf GPX-Daten an."""
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
    """Zeigt Herzfrequenz- und Leistungskurven aus FIT-Daten an."""
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


# --- Callback-Funktionen (aktualisiert) ---
def set_training_to_edit(training_id):
    """
    Setzt die ID des Trainings, das bearbeitet werden soll, im Session State
    und wechselt zur Bearbeitungsseite.
    """
    st.session_state.editing_training_id = training_id
    # Reset last_editing_id for workout_form_utils to ensure fresh load
    if 'last_editing_id' in st.session_state:
        del st.session_state.last_editing_id
    st.switch_page("pages/add workout.py") # Wechselt zur Bearbeitungsseite


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

# --- UI für Details und Liste (aktualisiert) ---

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

        # Pfadauflösung für das Bild
        image_path_from_db = training_data.get('image')
        local_image_path = image_path_from_db
        if local_image_path and os.path.exists(local_image_path):
            st.image(local_image_path, caption=f"Bild für {training_data['name']}", use_container_width=True)
        elif image_path_from_db and image_path_from_db != "-":
            st.warning(f"Bilddatei {repr(image_path_from_db)} konnte nicht gefunden werden.") # Korrigiert: repr()

        st.markdown("**Verlinkte Dateien:**")

        gpx_file_path_from_db = training_data.get('gpx_file')
        gpx_data = load_gpx_data(gpx_file_path_from_db) # load_gpx_data enthält nun repr() in seinen Fehlermeldungen
        if gpx_data:
            st.markdown("### GPX-Track auf Karte")
            display_gpx_on_map_ui(gpx_data)
            st.markdown("---")
            st.markdown("### Höhenprofil")
            display_elevation_profile_ui(gpx_data)
        else:
            if gpx_file_path_from_db and gpx_file_path_from_db != "-":
                st.warning(f"GPX-Datei {repr(gpx_file_path_from_db)} konnte nicht geladen oder geparst werden.") # Korrigiert: repr()
            else:
                st.markdown("Keine GPX-Datei verlinkt.")

        fit_file_path_from_db = training_data.get('fit_file')
        fit_data_df = load_fit_data(fit_file_path_from_db) # load_fit_data enthält nun repr() in seinen Fehlermeldungen
        if fit_data_df is not None and not fit_data_df.empty:
            st.markdown("---")
            st.markdown("### FIT-Dateianalyse")
            display_fit_data_ui(fit_data_df)
        else:
            if fit_file_path_from_db and fit_file_path_from_db != "-":
                st.warning(f"FIT-Datei {repr(fit_file_path_from_db)} konnte nicht geladen oder geparst werden.") # Korrigiert: repr()
            else:
                st.markdown("Keine FIT-Datei verlinkt.")

        ekg_file_path_from_db = training_data.get('ekg_file')
        ekg_content = load_ekg_data(ekg_file_path_from_db) # load_ekg_data enthält nun repr() in seinen Fehlermeldungen
        if ekg_content:
            st.markdown(f"- **EKG-Datei ({os.path.basename(ekg_file_path_from_db) if ekg_file_path_from_db else 'N/A'}):**")
            st.code(ekg_content, language='text')
        else:
            if ekg_file_path_from_db and ekg_file_path_from_db != "-":
                st.warning(f"EKG-Datei {repr(ekg_file_path_from_db)} konnte nicht geladen werden.") # Korrigiert: repr()
            else:
                # Zeige dies nur an, wenn keine der anderen Dateien verlinkt ist
                if not (gpx_file_path_from_db and gpx_file_path_from_db != "-") and \
                   not (fit_file_path_from_db and fit_file_path_from_db != "-"):
                    st.markdown("Keine weiteren Dateien verlinkt.")

        st.markdown("---")

        col_edit, col_delete, col_spacer = st.columns([0.15, 0.15, 0.7])
        with col_edit:
            if st.button("Bearbeiten 📝", key=f"edit_btn_{training_id_str}"):
                on_edit_callback(training_data.doc_id) # Ruft die aktualisierte Funktion auf
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
        # Übergeben Sie set_training_to_edit als Callback
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
        # Filtere die Trainings, die der Person zugeordnet sind
        user_trainings = [t for t in all_trainings if t.doc_id in ekg_test_ids]
        return user_trainings
    return []

# --- Hauptanwendung ---
def main():
    st.title("Dein Trainings-Tagebuch 🏋️‍♂️")
    st.markdown("---")

    initialize_directories()

    if "current_user_id" not in st.session_state:
        st.info("Bitte wähle im Dashboard zuerst eine Person aus, um deine Trainings anzuzeigen.")
        return

    if 'editing_training_id' not in st.session_state:
        st.session_state.editing_training_id = None
    
    if 'initial_expand_done' not in st.session_state:
        st.session_state.initial_expand_done = False

    st.subheader("Deine Trainingsübersicht")
    trainings_for_user = get_trainings_for_current_user()
    display_training_list_ui(trainings_for_user)

if __name__ == "__main__":
    main()
