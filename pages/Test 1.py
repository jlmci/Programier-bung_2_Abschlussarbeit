import streamlit as st
import pandas as pd
from datetime import datetime
import folium
import gpxpy
import gpxpy.gpx
from streamlit_folium import folium_static
import os # Wird benötigt, um Dateipfade zu handhaben

st.title("Dein Trainings-Tagebuch 🏋️‍♂️")

# --- Initialisiere Beispiel-Trainingsdaten im Session State ---
if 'trainings' not in st.session_state:
    st.session_state.trainings = [
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
            "image": "https://placehold.co/300x200/aabbcc/ffffff?text=Laufbild",
            # !!! Hier werden die lokalen Dateinamen verwendet !!!
            "gpx_file": "../data/UM_28_5__Elgen.gpx",
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
            "image": "https://placehold.co/300x200/ccbbaa/ffffff?text=Krafttraining",
            "gpx_file": "-", # Kein GPX für Krafttraining
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
            "image": "https://placehold.co/300x200/cbbdaa/ffffff?text=Radfahren",
            # !!! Hier wird ein lokaler Dateiname verwendet !!!
            "gpx_file": "radtour_seeufer.gpx",
            "ekg_file": "-"
        }
    ]

st.markdown("---") # Visueller Trenner

# --- Funktion zum Parsen und Anzeigen der GPX-Datei (angepasst für lokale Dateien) ---
def display_gpx_on_map(gpx_filename):
    # Erstelle den vollständigen Pfad zur GPX-Datei
    # os.path.join ist gut, um plattformunabhängige Pfade zu erstellen
    file_path = os.path.join(os.path.dirname(__file__), gpx_filename)

    try:
        with open(file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        if not gpx.tracks:
            st.warning("Die GPX-Datei enthält keine Tracks zum Anzeigen.")
            return

        # Finde den Mittelpunkt des ersten Tracks, um die Karte zu zentrieren
        first_point = gpx.tracks[0].segments[0].points[0]
        m = folium.Map(location=[first_point.latitude, first_point.longitude], zoom_start=13)

        for track in gpx.tracks:
            for segment in track.segments:
                points = []
                for point in segment.points:
                    points.append((point.latitude, point.longitude))
                folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(m)

        # Passe den Zoom der Karte an
        bounds = gpx.get_bounds()
        if bounds:
            m.fit_bounds([[bounds.min_latitude, bounds.min_longitude], [bounds.max_latitude, bounds.max_longitude]])

        folium_static(m)

    except FileNotFoundError:
        st.error(f"Fehler: Die Datei '{gpx_filename}' wurde nicht gefunden. Stelle sicher, dass sie im selben Ordner wie dein Skript liegt.")
    except gpxpy.gpx.GPXException as e:
        st.error(f"Fehler beim Parsen der GPX-Datei '{gpx_filename}': {e}. Stelle sicher, dass es eine gültige GPX-Datei ist.")
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")



# --- Liste der Trainings mit Expandern ---
st.subheader("Deine Trainingsübersicht")

if st.session_state.trainings:
    sorted_trainings = sorted(
        st.session_state.trainings,
        key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"),
        reverse=True
    )

    for training in sorted_trainings:
        expander_title = f"**{training['name']}** - {training['date']} ({training['sportart']})"
        with st.expander(expander_title):
            st.markdown(f"**Datum:** {training['date']}")
            st.markdown(f"**Sportart:** {training['sportart']}")
            st.markdown(f"**Dauer:** {training['dauer']}")
            st.markdown(f"**Distanz:** {training['distanz']}")
            st.markdown(f"**Puls:** {training['puls']}")
            st.markdown(f"**Kalorien:** {training['kalorien']}")
            st.markdown(f"**Anstrengung:** {training['anstrengung']}/10")
            st.markdown(f"**Bewertung:** {'⭐' * training['star_rating']}")

            st.markdown(f"**Beschreibung:**")
            if training['description']:
                st.info(training['description'])
            else:
                st.markdown("Keine Beschreibung vorhanden.")

            if training['image'] and training['image'].startswith('http'):
                st.image(training['image'], caption=f"Bild für {training['name']}", use_column_width=True)

            st.markdown("**Verlinkte Dateien:**")
            # GPX-Karte anzeigen 
            if training['gpx_file'] and training['gpx_file'] != "-":
                #if st.button(f"GPX-Karte anzeigen für {training['name']}", key=f"show_map_{training['id']}"):
                display_gpx_on_map(training['gpx_file'])
            else:
                st.markdown("Keine GPX-Datei verlinkt.")

            # --- NEU: EKG-Datei anzeigen/laden (angepasst für lokale Dateien) ---
            # Für EKG-Dateien können wir den Inhalt direkt anzeigen
            if training['ekg_file'] and training['ekg_file'] != "-":
                # Erstelle den vollständigen Pfad zur EKG-Datei
                ekg_file_path = os.path.join(os.path.dirname(__file__), training['ekg_file'])
                try:
                    with open(ekg_file_path, 'r') as f:
                        ekg_content = f.read()
                    st.markdown(f"- **EKG-Datei ({training['ekg_file']}):**")
                    st.code(ekg_content, language='text') # Zeigt den Inhalt als Code/Text an
                except FileNotFoundError:
                    st.error(f"Fehler: EKG-Datei '{training['ekg_file']}' wurde nicht gefunden.")
                except Exception as e:
                    st.error(f"Fehler beim Lesen der EKG-Datei '{training['ekg_file']}': {e}")
            else:
                if not (training['gpx_file'] and training['gpx_file'] != "-"):
                    st.markdown("Keine Dateien verlinkt.")


            st.markdown("---")

            col_edit, col_delete, col_spacer = st.columns([0.15, 0.15, 0.7])
            with col_delete:
                if st.button("Löschen 🗑️", key=f"delete_btn_{training['id']}"):
                    st.session_state.trainings = [t for t in st.session_state.trainings if t['id'] != training['id']]
                    st.success(f"Training '{training['name']}' vom {training['date']} wurde gelöscht.")
                    st.experimental_rerun()

else:
    st.info("Es sind noch keine Trainings vorhanden. Füge Trainings hinzu, damit sie hier angezeigt werden! 👆")