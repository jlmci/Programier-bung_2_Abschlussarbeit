import streamlit as st
from datetime import datetime


st.title("Workout hinzufügen")
st.write("Hier kannst du dein Workout hinzufügen.")

#einzugeben sind Sportart, Dauer, Distanz, Puls, Kalorien'''
#es soll auc hdie anstrengung abgefragt werden indem auf 3 smilys geklickt werden kann mit buttons die nebeneinader sind die die anstrengung darstellen'''
#es soll eine richtiege sternebewertung wie z.b auf amaton  mit 1 bis 5 sternen die richtig als bilder und nicht als slider oder auswahlboxd sind'''
#es können außerdem eine beschreibung mit description hinzugefügt werden und ein bild mit image hochgeladen werden'''
#es gibt auch noch ein feld um GPX daten hochzuladen und ein feld um EKG daten hochzuladen'''
name = st.text_input("Name des Workouts", placeholder="Test 1")
date = st.date_input("Datum", value=datetime.now().date())
sportart = st.text_input("Sportart", placeholder="z.B. Laufen, Radfahren, Schwimmen")
dauer = st.number_input("Dauer (in Minuten)", min_value=0, step=1)
distanz = st.number_input("Distanz (in km)", min_value=0.0, step=0.1)
puls = st.number_input("Puls (in bpm)", min_value=0, step=1)
kalorien = st.number_input("Kalorien (in kcal)", min_value=0, step=1)

smily_mapping = ["good", "ok", "neutral", "axceptable", "bad"]
selected_smily = st.feedback("faces")
if selected_smily is not None:
    antrengung = smily_mapping[selected_smily]

star_mapping = ["one", "two", "three", "four", "five"]
selected_smily = st.feedback("stars")
if selected_smily is not None:
    star_rating = star_mapping[selected_smily]

description = st.text_area("Beschreibung")
image = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"], help="Optional: Füge ein Bild deines Workouts hinzu.")
gpx_file = st.file_uploader("GPX Datei hochladen", type=["gpx"], help="Optional: Füge eine GPX-Datei deines Workouts hinzu. max. größe = 200MB")
ekg_file = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"], help="Optional: Füge eine EKG-Datei deines Workouts hinzu. max. größe = 200MB")


if st.button("Workout hinzufügen"):
    # Hier kannst du den Code zum Speichern des Workouts in der Datenbank einfügen
    if name == None or name == "":
        st.error("Bitte gib einen Namen für das Workout ein.")
    else:
        st.success(f"Workout '{name}' erfolgreich hinzugefügt!")
        link_gpx = f"data/{name}.gpx"
        if gpx_file is not None:
            with open(link_gpx, "wb") as f:
                f.write(gpx_file)
        else:
            st.warning("Keine GPX-Datei hochgeladen.")

        if ekg_file is not None:
            ekg_file_type = ekg_file.name
            link_txt = f"data/{name}.{ekg_file_type}"
            with open(link_txt, "wb") as f:
                f.write(ekg_file)
        else:
            st.warning("Keine EKG-Datei hochgeladen.")



