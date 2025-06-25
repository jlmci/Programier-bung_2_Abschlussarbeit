import streamlit as st
import pandas as pd
from datetime import datetime
import folium
import gpxpy
import gpxpy.gpx
from streamlit_folium import folium_static
import os

# --- Konfiguration und Initialisierung ---
# Verzeichnis für lokale Bilder. Streamlit muss darauf zugreifen können.
# Es wird empfohlen, diesen Ordner relativ zum Skript zu halten.
IMAGE_DIR = "images"
DATA_DIR = "data" # Verzeichnis für GPX- und EKG-Dateien

def initialize_directories():
    """Stellt sicher, dass notwendige Verzeichnisse existieren."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    # Optional: Initialisierungsmeldungen, falls Ordner neu erstellt wurden
    # if not os.path.exists(IMAGE_DIR): st.info(f"Ordner '{IMAGE_DIR}' erstellt.")
    # if not os.path.exists(DATA_DIR): st.info(f"Ordner '{DATA_DIR}' erstellt.")

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
            "ekg_file": ""
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
            "ekg_file": "-"
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
            "gpx_file": os.path.join("../data/", "UM_28_5__Elgen.gpx"), # Beispiel GPX-Datei
            "ekg_file": ""
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
            return gpxpy.parse(gpx_file)
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

# --- UI-Komponenten als Funktionen ---

def display_gpx_on_map_ui(gpx_object):
    """
    Zeigt einen GPX-Track auf einer Folium-Karte an.
    Erwartet ein geparstes gpxpy.GPX-Objekt.
    """
    if not gpx_object or not gpx_object.tracks:
        st.markdown("Keine GPX-Daten zum Anzeigen vorhanden.")
        return

    # Finde den Mittelpunkt des ersten Tracks, um die Karte zu zentrieren
    first_point = gpx_object.tracks[0].segments[0].points[0]
    m = folium.Map(location=[first_point.latitude, first_point.longitude], zoom_start=13)

    for track in gpx_object.tracks:
        for segment in track.segments:
            points = [(point.latitude, point.longitude) for point in segment.points]
            folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(m)

    # Passe den Zoom der Karte an
    bounds = gpx_object.get_bounds()
    if bounds:
        m.fit_bounds([[bounds.min_latitude, bounds.min_longitude], [bounds.max_latitude, bounds.max_longitude]])

    folium_static(m)

def display_training_details_ui(training_data, on_delete_callback):
    """
    Zeigt die Details eines einzelnen Trainings in einem Expander an.
    training_data: Ein Dictionary mit den Trainingsdetails.
    on_delete_callback: Eine Funktion, die aufgerufen wird, wenn das Löschen geklickt wird.
                        Sie sollte die ID des zu löschenden Trainings erhalten.
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

        # Lokale Bilder oder URLs anzeigen
        if training_data['image']:
            # Prüfen, ob es sich um eine lokale Datei oder eine URL handelt
            if training_data['image'].startswith('http'):
                st.image(training_data['image'], caption=f"Bild für {training_data['name']}", use_container_width=True)
            else:
                local_image_path = get_absolute_path(training_data['image'])
                if local_image_path and os.path.exists(local_image_path):
                    st.image(local_image_path, caption=f"Bild für {training_data['name']}", use_container_width=True)
                else:
                    st.warning(f"Bilddatei '{training_data['image']}' nicht gefunden. Stelle sicher, dass sie im '{IMAGE_DIR}' Ordner liegt.")

        st.markdown("**Verlinkte Dateien:**")

        # GPX-Karte anzeigen
        if training_data['gpx_file'] and training_data['gpx_file'] != "-":
            gpx_data = load_gpx_data(training_data['gpx_file'])
            display_gpx_on_map_ui(gpx_data)
        else:
            st.markdown("Keine GPX-Datei verlinkt.")

        # EKG-Datei anzeigen/laden
        if training_data['ekg_file'] and training_data['ekg_file'] != "-":
            ekg_content = load_ekg_data(training_data['ekg_file'])
            if ekg_content:
                st.markdown(f"- **EKG-Datei ({training_data['ekg_file']}):**")
                st.code(ekg_content, language='text')
        else:
            if not (training_data['gpx_file'] and training_data['gpx_file'] != "-"):
                st.markdown("Keine weiteren Dateien verlinkt.")

        st.markdown("---")

        col_edit, col_delete, col_spacer = st.columns([0.15, 0.15, 0.7])
        with col_delete:
            if st.button("Löschen 🗑️", key=f"delete_btn_{training_data['id']}"):
                on_delete_callback(training_data['id'])
                st.success(f"Training '{training_data['name']}' vom {training_data['date']} wurde gelöscht.")
                st.rerun()

def display_training_list_ui(trainings):
    """
    Zeigt die Liste aller Trainings an.
    trainings: Eine Liste von Dictionarys mit den Trainingsdaten.
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
        display_training_details_ui(training, delete_training_from_session_state)

def delete_training_from_session_state(training_id):
    """Callback-Funktion zum Löschen eines Trainings aus dem Session State."""
    st.session_state.trainings = [t for t in st.session_state.trainings if t['id'] != training_id]


# --- Hauptanwendung ---
def main():
    st.title("Dein Trainings-Tagebuch 🏋️‍♂️")
    st.markdown("---")

    # Sicherstellen, dass die Verzeichnisse existieren
    initialize_directories()

    # Initialisiere Trainingsdaten im Session State, falls nicht vorhanden
    # In einem echten Szenario würde dies von der Datenbank geladen
    if 'trainings' not in st.session_state:
        st.session_state.trainings = get_initial_training_data()

    # UI zum Anzeigen der Trainingsliste
    display_training_list_ui(st.session_state.trainings)

if __name__ == "__main__":
    main()