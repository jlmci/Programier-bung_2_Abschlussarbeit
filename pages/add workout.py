import streamlit as st
from datetime import datetime


'''add workouts to the database'''
st.title("Workout hinzufügen")
st.write("Hier kannst du dein Workout hinzufügen.")

'''einzugeben sind Sportart, Dauer, Distanz, Puls, Kalorien'''
'''zudem wird exaustung abgefragt und mit 3 smilys auszuwählen sein'''
'''es gibt auch ein allgemeines star_rating des workouts mit 5 sternen und sternen als bildern'''
'''es können außerdem eine beschreibung mit description hinzugefügt werden und ein bild mit image hochgeladen werden'''
''' es gibt auch noch ein feld um GPX daten hochzuladen und ein feld um EKG daten hochzuladen'''
date = st.date_input("Datum", value=datetime.now().date())
sportart = st.text_input("Sportart")
dauer = st.number_input("Dauer (in Minuten)", min_value=0, step=1)
distanz = st.number_input("Distanz (in km)", min_value=0.0, step=0.1)
puls = st.number_input("Puls (in bpm)", min_value=0, step=1)
kalorien = st.number_input("Kalorien (in kcal)", min_value=0, step=1)
anstrengung = st.select_slider(
    "Exhausting",
    options=["😐", "😅", "😩"],
    value="😐",
    format_func=lambda x: x,  # Display the emoji directly
)
star_rating = st.select_slider(
    "Star Rating",
    options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
    value="⭐⭐⭐⭐⭐",
    format_func=lambda x: x,  # Display the star directly
)
description = st.text_area("Beschreibung")
image = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"])
gpx_file = st.file_uploader("GPX Datei hochladen", type=["gpx"])
ekg_file = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"])
if st.button("Workout hinzufügen"):
    # Hier kannst du den Code zum Speichern des Workouts in der Datenbank einfügen
    
    st.success("Workout erfolgreich hinzugefügt!")
    # Beispiel: print(f"Workout added: {date}, {sportart}, {dauer}, {distanz}, {puls}, {kalorien}, {anstrengung}, {star_rating}, {description}")


