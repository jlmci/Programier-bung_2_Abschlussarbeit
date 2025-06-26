import streamlit as st
from datetime import datetime
import addtrainingtodict


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
else:
    antrengung = None # Setzt Anstrengung auf None, wenn kein Smiley ausgewählt wurde

star_mapping = ["one", "two", "three", "four", "five"]
selected_stars = st.feedback("stars") # Habe den Variablennamen von selected_smily zu selected_stars geändert, um Verwechslungen zu vermeiden
if selected_stars is not None:
    star_rating = star_mapping[selected_stars]
else:
    star_rating = None # Setzt Star-Bewertung auf None, wenn keine Sterne ausgewählt wurden

description = st.text_area("Beschreibung")
image = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"], help="Optional: Füge ein Bild deines Workouts hinzu.")
gpx_file = st.file_uploader("GPX Datei hochladen", type=["gpx"], help="Optional: Füge eine GPX-Datei deines Workouts hinzu. max. größe = 200MB")
ekg_file = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"], help="Optional: Füge eine EKG-Datei deines Workouts hinzu. max. größe = 200MB")
fit_file = st.file_uploader("FIT Datei hochladen", type=["fit"], help="Optional: Füge eine FIT-Datei deines Workouts hinzu. max. größe = 200MB") # Hinzugefügte Zeile für FIT-Dateien


if st.button("Workout hinzufügen"):
    # Hier kannst du den Code zum Speichern des Workouts in der Datenbank einfügen
    if name is None or name == "":
        st.error("Bitte gib einen Namen für das Workout ein.")
    else:
        st.success(f"Workout '{name}' erfolgreich hinzugefügt!")
        
        # Initialisiere Dateipfade als None
        link_gpx = None
        link_txt = None
        link_fit = None

        if gpx_file is not None:
            link_gpx = f"data/{name}.gpx"
            with open(link_gpx, "wb") as f:
                f.write(gpx_file.getbuffer()) # Verwende getbuffer() für BytesIO-Objekte
        else:
            st.warning("Keine GPX-Datei hochgeladen.")

        if ekg_file is not None:
            ekg_file_type = ekg_file.name.split(".")[-1] # Extrahieren der Dateiendung
            link_txt = f"data/{name}.{ekg_file_type}"
            with open(link_txt, "wb") as f:
                f.write(ekg_file.getbuffer()) # Verwende getbuffer()
        else:
            st.warning("Keine EKG-Datei hochgeladen.")

        if fit_file is not None:
            link_fit = f"data/{name}.fit"
            with open(link_fit, "wb") as f:
                f.write(fit_file.getbuffer()) # Verwende getbuffer()
        else:
            st.warning("Keine FIT-Datei hochgeladen.")
        
        addtrainingtodict.add_training_to_dict(
            name=name,
            date=date,
            sportart=sportart,
            dauer=dauer,
            distanz=distanz,
            puls=puls,
            kalorien=kalorien,
            antrengung=antrengung,
            star_rating=star_rating,
            description=description,
            image=image, # image ist hier das BytesIO-Objekt, handle es entsprechend in addtrainingtodict
            gpx_file=link_gpx,
            ekg_file=link_txt,
            fit_file=link_fit # Übergabe des FIT-Dateipfads
        )