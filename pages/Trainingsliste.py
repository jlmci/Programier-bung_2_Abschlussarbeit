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

# --- Konfiguration der Streamlit-Seite ---
#st.set_page_config(layout="wide") # Moved to the very top!

# --- Konfiguration und Initialisierung ---
IMAGE_DIR = "images"
DATA_DIR = "data"

def initialize_directories():
    """Stellt sicher, dass notwendige Verzeichnisse existieren."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def get_initial_training_data():
    """
    Gibt initiale Trainingsdaten zurück.
    Im echten Szenario würde diese Funktion Daten aus einer Datenbank laden.
    Die Pfade zu lokalen Dateien sind hier beispielhaft relativ zum Skript-Verzeichnis.
    """
    return [
        {
            "id": 1,
            "name": "Morgenlauf im Wald",
            "date": "2025-06-17",
            "sportart": "Laufen",
            "dauer": "60 min",
            "distanz": "10 km",
            "puls": "155 bpm (avg)",
            "kalorien": "700 kcal",
            "anstrengung": 7,
            "star_rating": 4,
            "description": "Schöner, erfrischender Lauf im Wald. Keine Probleme, angenehme Temperatur.",
            "image": os.path.join(IMAGE_DIR, "laufbild.jpg"),
            "gpx_file": os.path.join(DATA_DIR, "UM_28_5__Elgen.gpx"),
            "ekg_file": "",
            "fit_file": ""
        },
        {
            "id": 2,
            "name": "Beintraining Gym",
            "date": "2025-06-16",
            "sportart": "Krafttraining",
            "dauer": "75 min",
            "distanz": "-",
            "puls": "130 bpm (avg)",
            "kalorien": "550 kcal",
            "anstrengung": 8,
            "star_rating": 5,
            "description": "Intensives Beintraining mit Fokus auf Kniebeugen und Kreuzheben. Gute Progression bei den Gewichten.",
            "image": os.path.join(IMAGE_DIR, "krafttraining.jpg"),
            "gpx_file": "-",
            "ekg_file": "-",
            "fit_file": ""
        },
        {
            "id": 3,
            "name": "Radtour Seeufer",
            "date": "2025-06-15",
            "sportart": "Radfahren",
            "dauer": "120 min",
            "distanz": "35 km",
            "puls": "140 bpm (avg)",
            "kalorien": "900 kcal",
            "anstrengung": 6,
            "star_rating": 4,
            "description": "Entspannte Radtour entlang des Sees. Wenig Wind, gute Sicht.",
            "image": os.path.join(IMAGE_DIR, "radfahren.jpg"),
            "gpx_file": os.path.join(DATA_DIR, "UM_28_5__Elgen.gpx"),
            "ekg_file": "",
            "fit_file": os.path.join(DATA_DIR, "FTP_Test.fit")
        }
    ]

# --- Hilfsfunktionen für die Datenverarbeitung und Dateihandhabung ---

def get_absolute_path(relative_path):
    """Konvertiert einen relativen Pfad in einen absoluten Pfad."""
    if not relative_path or relative_path == "-":
        return None
    return os.path.join(os.path.dirname(__file__), relative_path)

def load_gpx_data(gpx_filepath):
    """
    Lädt und parst eine GPX-Datei.
    Gibt ein gpxpy.GPX-Objekt oder None bei Fehler zurück.
    """
    abs_filepath = get_absolute_path(gpx_filepath)
    if not abs_filepath:
        return None
    try:
        with open(abs_filepath, 'r') as gpx_file:
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
    abs_filepath = get_absolute_path(ekg_filepath)
    if not abs_filepath:
        return None
    try:
        with open(abs_filepath, 'r') as f:
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
    abs_filepath = get_absolute_path(fit_filepath)
    if not abs_filepath:
        return None
    try:
        fitfile = fitparse.FitFile(abs_filepath)

        time = []
        velocity = []
        heartrate = []
        distance = []
        cadence = []
        power = []

        garmin_epoch = datetime(1989, 12, 31, 0, 0, 0, tzinfo=None)

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

    if not gpx_object.tracks[0].segments[0].points:
        st.warning("GPX-Track hat keine Punkte für die Karte.")
        return

    first_point = gpx_object.tracks[0].segments[0].points[0]
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
        pass # Zeitstempel sind bereits datetime Objekte

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


def display_training_details_ui(training_data, on_delete_callback, on_edit_callback):
    """
    Zeigt die Details eines einzelnen Trainings in einem Expander an.
    """
    expander_title = f"**{training_data['name']}** - {training_data['date']} ({training_data['sportart']})"
    with st.expander(expander_title):
        st.markdown(f"**Datum:** {training_data['date']}")
        st.markdown(f"**Sportart:** {training_data['sportart']}")
        st.markdown(f"**Dauer:** {training_data['dauer']}")
        st.markdown(f"**Distanz:** {training_data['distanz']}")
        st.markdown(f"**Puls:** {training_data['puls']}")
        st.markdown(f"**Kalorien:** {training_data['kalorien']}")
        st.markdown(f"**Anstrengung:** {training_data['anstrengung']}/10")
        st.markdown(f"**Bewertung:** {'⭐' * training_data['star_rating']}")

        st.markdown(f"**Beschreibung:**")
        if training_data['description']:
            st.info(training_data['description'])
        else:
            st.markdown("Keine Beschreibung vorhanden.")

        if training_data['image']:
            if training_data['image'].startswith('http'):
                st.image(training_data['image'], caption=f"Bild für {training_data['name']}", use_container_width=True)
            else:
                local_image_path = get_absolute_path(training_data['image'])
                if local_image_path and os.path.exists(local_image_path):
                    st.image(local_image_path, caption=f"Bild für {training_data['name']}", use_container_width=True)
                else:
                    st.warning(f"Bilddatei '{training_data['image']}' nicht gefunden. Stelle sicher, dass sie im '{IMAGE_DIR}' Ordner liegt.")

        st.markdown("**Verlinkte Dateien:**")

        if training_data['gpx_file'] and training_data['gpx_file'] != "-":
            gpx_data = load_gpx_data(training_data['gpx_file'])
            if gpx_data:
                st.markdown("### GPX-Track auf Karte")
                display_gpx_on_map_ui(gpx_data)
                st.markdown("---")
                st.markdown("### Höhenprofil")
                display_elevation_profile_ui(gpx_data)
        else:
            st.markdown("Keine GPX-Datei verlinkt.")

        if training_data['fit_file'] and training_data['fit_file'] != "-":
            fit_data_df = load_fit_data(training_data['fit_file'])
            if fit_data_df is not None and not fit_data_df.empty:
                st.markdown("---")
                st.markdown("### FIT-Dateianalyse")
                display_fit_data_ui(fit_data_df)
            else:
                st.markdown("Keine FIT-Datei verlinkt oder Daten konnten nicht geladen werden.")
        else:
            if not (training_data['gpx_file'] and training_data['gpx_file'] != "-"):
                st.markdown("Keine FIT-Datei verlinkt.")


        if training_data['ekg_file'] and training_data['ekg_file'] != "-":
            ekg_content = load_ekg_data(training_data['ekg_file'])
            if ekg_content:
                st.markdown(f"- **EKG-Datei ({training_data['ekg_file']}):**")
                st.code(ekg_content, language='text')
            else:
                if not (training_data['gpx_file'] and training_data['gpx_file'] != "-") and \
                   not (training_data['fit_file'] and training_data['fit_file'] != "-"):
                    st.markdown("Keine weiteren Dateien verlinkt.")
        else:
            if not (training_data['gpx_file'] and training_data['gpx_file'] != "-") and \
               not (training_data['fit_file'] and training_data['fit_file'] != "-") and \
               not (training_data['ekg_file'] and training_data['ekg_file'] != "-"):
                st.markdown("Keine weiteren Dateien verlinkt.")


        st.markdown("---")

        col_edit, col_delete, col_spacer = st.columns([0.15, 0.15, 0.7])
        with col_edit:
            if st.button("Bearbeiten 📝", key=f"edit_btn_{training_data['id']}"):
                on_edit_callback(training_data['id'])
                st.rerun()
        with col_delete:
            if st.button("Löschen 🗑️", key=f"delete_btn_{training_data['id']}"):
                on_delete_callback(training_data['id'])
                st.success(f"Training '{training_data['name']}' vom {training_data['date']} wurde gelöscht.")
                st.rerun()

def display_training_list_ui(trainings):
    """
    Zeigt die Liste aller Trainings an.
    """
    st.subheader("Deine Trainingsübersicht")

    if not trainings:
        st.info("Es sind noch keine Trainings vorhanden. Füge Trainings hinzu, damit sie hier angezeigt werden! 👆")
        return

    sorted_trainings = sorted(
        trainings,
        key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"),
        reverse=True
    )

    for training in sorted_trainings:
        display_training_details_ui(training, delete_training_from_session_state, set_training_to_edit)

def delete_training_from_session_state(training_id):
    """Callback-Funktion zum Löschen eines Trainings aus dem Session State."""
    st.session_state.trainings = [t for t in st.session_state.trainings if t['id'] != training_id]

def set_training_to_edit(training_id):
    """Setzt die ID des Trainings, das bearbeitet werden soll, im Session State."""
    st.session_state.editing_training_id = training_id

def update_training_in_session_state(updated_training):
    """Aktualisiert ein Training im Session State."""
    for i, training in enumerate(st.session_state.trainings):
        if training['id'] == updated_training['id']:
            st.session_state.trainings[i] = updated_training
            break
    st.session_state.editing_training_id = None
    st.success("Training erfolgreich aktualisiert!")
    st.rerun()

def edit_training_ui(training_data):
    """
    Zeigt ein Formular zum Bearbeiten eines Trainings an.
    """
    st.subheader(f"Training bearbeiten: {training_data['name']}")
    with st.form(key=f"edit_training_form_{training_data['id']}"):
        edited_name = st.text_input("Name", value=training_data['name'])
        edited_date = st.date_input("Datum", value=datetime.strptime(training_data['date'], "%Y-%m-%d"))
        edited_sportart = st.text_input("Sportart", value=training_data['sportart'])
        edited_dauer = st.text_input("Dauer", value=training_data['dauer'])
        edited_distanz = st.text_input("Distanz", value=training_data['distanz'])
        edited_puls = st.text_input("Puls", value=training_data['puls'])
        edited_kalorien = st.text_input("Kalorien", value=training_data['kalorien'])
        edited_description = st.text_area("Beschreibung", value=training_data['description'])
        
        st.markdown(f"**Anstrengung (nicht editierbar):** {training_data['anstrengung']}/10")
        st.markdown(f"**Bewertung (nicht editierbar):** {'⭐' * training_data['star_rating']}")

        edited_image = st.text_input(f"Bilddatei (im Ordner '{IMAGE_DIR}')", value=training_data['image'])
        edited_gpx_file = st.text_input(f"GPX-Datei (im Ordner '{DATA_DIR}')", value=training_data['gpx_file'])
        edited_ekg_file = st.text_input(f"EKG-Datei (im Ordner '{DATA_DIR}')", value=training_data['ekg_file'])
        edited_fit_file = st.text_input(f"FIT-Datei (im Ordner '{DATA_DIR}')", value=training_data['fit_file'])

        submit_button = st.form_submit_button("Änderungen speichern")
        cancel_button = st.form_submit_button("Abbrechen")

        if submit_button:
            updated_training = training_data.copy()
            updated_training.update({
                "name": edited_name,
                "date": edited_date.strftime("%Y-%m-%d"),
                "sportart": edited_sportart,
                "dauer": edited_dauer,
                "distanz": edited_distanz,
                "puls": edited_puls,
                "kalorien": edited_kalorien,
                "description": edited_description,
                "image": edited_image,
                "gpx_file": edited_gpx_file,
                "ekg_file": edited_ekg_file,
                "fit_file": edited_fit_file,
            })
            update_training_in_session_state(updated_training)
        elif cancel_button:
            st.session_state.editing_training_id = None
            st.rerun()

# --- Hauptanwendung ---
def main():
    st.title("Dein Trainings-Tagebuch 🏋️‍♂️")
    st.markdown("---")

    initialize_directories()

    if 'trainings' not in st.session_state:
        st.session_state.trainings = get_initial_training_data()
    
    if 'editing_training_id' not in st.session_state:
        st.session_state.editing_training_id = None

    if st.session_state.editing_training_id is not None:
        training_to_edit = next((t for t in st.session_state.trainings if t['id'] == st.session_state.editing_training_id), None)
        if training_to_edit:
            edit_training_ui(training_to_edit)
        else:
            st.error("Training zum Bearbeiten nicht gefunden.")
            st.session_state.editing_training_id = None
    else:
        display_training_list_ui(st.session_state.trainings)

if __name__ == "__main__":
    main()