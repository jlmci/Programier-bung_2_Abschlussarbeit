'''
import streamlit as st
from datetime import datetime
import addtrainingtodict


st.title("Workout hinzufügen")
st.write("Hier kannst du dein Workout hinzufügen.")

#einzugeben sind Sportart, Dauer, Distanz, Puls, Kalorien
#es soll auc hdie anstrengung abgefragt werden indem auf 3 smilys geklickt werden kann mit buttons die nebeneinader sind die die anstrengung darstellen
#es soll eine richtiege sternebewertung wie z.b auf amaton  mit 1 bis 5 sternen die richtig als bilder und nicht als slider oder auswahlboxd sind
#es können außerdem eine beschreibung mit description hinzugefügt werden und ein bild mit image hochgeladen werden
#es gibt auch noch ein feld um GPX daten hochzuladen und ein feld um EKG daten hochzuladen
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
'''
import streamlit as st
from datetime import datetime
from tinydb import TinyDB, Query
import os

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')

# --- Konfiguration & Konstanten ---
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Standardwerte für die Formularfelder im Session State initialisieren
if "workout_name_input" not in st.session_state:
    st.session_state["workout_name_input"] = ""
if "workout_date_input" not in st.session_state:
    st.session_state["workout_date_input"] = datetime.now().date()
if "workout_sportart_input" not in st.session_state:
    st.session_state["workout_sportart_input"] = ""
if "workout_dauer_input" not in st.session_state:
    st.session_state["workout_dauer_input"] = 0
if "workout_distanz_input" not in st.session_state:
    st.session_state["workout_distanz_input"] = 0.0
if "workout_puls_input" not in st.session_state:
    st.session_state["workout_puls_input"] = 0
if "workout_kalorien_input" not in st.session_state:
    st.session_state["workout_kalorien_input"] = 0
if "workout_description_input" not in st.session_state:
    st.session_state["workout_description_input"] = ""
if "selected_antrengung" not in st.session_state:
    st.session_state["selected_antrengung"] = None
if "selected_star_rating" not in st.session_state:
    st.session_state["selected_star_rating"] = None


# --- Hilfsfunktion zum Speichern des Workouts und Aktualisieren der Personendatenbank ---
def add_workout_to_db(person_id, name, date, sportart, dauer, distanz, puls, kalorien,
                      anstrengung, star_rating, description, image_path=None,
                      gpx_file_path=None, ekg_file_path=None, fit_file_path=None):
    """
    Fügt ein neues Training zur Trainingsdatenbank hinzu und aktualisiert die Personendatenbank.
    Gibt True bei Erfolg, False bei Fehler zurück.
    """
    try:
        new_test_id = db.insert({
            "name": name,
            "date": date,
            "sportart": sportart,
            "dauer": dauer,
            "distanz": distanz,
            "puls": puls,
            "kalorien": kalorien,
            "anstrengung": anstrengung,
            "star_rating": star_rating,
            "description": description,
            "image": image_path,
            "gpx_file": gpx_file_path,
            "ekg_file": ekg_file_path,
            "fit_file": fit_file_path
        })

        Person = Query()
        person_doc = dp.get(doc_id=int(person_id))

        if person_doc:
            current_ekg_tests = person_doc.get('ekg_tests', [])
            if new_test_id not in current_ekg_tests:
                current_ekg_tests.append(new_test_id)
                dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_id)])
                st.success(f"Workout '{name}' erfolgreich hinzugefügt und Person {person_id} aktualisiert (ID: {new_test_id}).")
                return True
            else:
                st.warning(f"Workout-ID {new_test_id} war bereits für Person {person_id} registriert. Datenbank nicht aktualisiert.")
                return False
        else:
            st.error(f"Fehler: Person mit ID {person_id} nicht in der Personendatenbank gefunden.")
            return False

    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
        return False

# Funktion zum Speichern von Dateien
def save_uploaded_file(uploaded_file, file_prefix, workout_name):
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = uploaded_file.name.split(".")[-1]
        safe_name = workout_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        unique_filename = f"{safe_name}_{file_prefix}_{timestamp}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

# --- Streamlit UI ---
st.title("Workout hinzufügen")
st.write("Hier kannst du dein Workout hinzufügen.")

# Die person_doc_id aus dem Session State holen
if "person_doc_id" not in st.session_state:
    st.error("Bitte wähle zuerst eine Person aus, um ein Workout hinzuzufügen!")
    st.stop()

person_doc_id = str(st.session_state["person_doc_id"])

# --- Eingabefelder mit Werten aus dem Session State ---
name = st.text_input("Name des Workouts", placeholder="Test 1", value=st.session_state["workout_name_input"], key="workout_name")
date = st.date_input("Datum", value=st.session_state["workout_date_input"], key="workout_date")
sportart = st.text_input("Sportart", placeholder="z.B. Laufen, Radfahren, Schwimmen", value=st.session_state["workout_sportart_input"], key="workout_sportart")

# --- Anstrengung (Smiley-Buttons) ---
st.write("Wie anstrengend war das Training?")
col1, col2, col3, col4, col5 = st.columns(5)
antrengung_value = st.session_state["selected_antrengung"]

# Logik für Smiley-Buttons: Ähnlich wie Sterne, Button wird zu Text bei Auswahl
with col1:
    if antrengung_value == "good":
        st.markdown("### 😃 Sehr leicht") # Highlighted
    elif st.button("😃 Sehr leicht", key="smiley_good"):
        st.session_state["selected_antrengung"] = "good"
        st.rerun()
with col2:
    if antrengung_value == "ok":
        st.markdown("### 🙂 leicht") # Highlighted
    elif st.button("🙂 leicht", key="smiley_ok"):
        st.session_state["selected_antrengung"] = "ok"
        st.rerun()
with col3:
    if antrengung_value == "neutral":
        st.markdown("### 😐 Neutral") # Highlighted
    elif st.button("😐 Neutral", key="smiley_neutral"):
        st.session_state["selected_antrengung"] = "neutral"
        st.rerun()
with col4:
    if antrengung_value == "acceptable":
        st.markdown("### 😟 anstrengend") # Highlighted
    elif st.button("😟 anstrengend", key="smiley_acceptable"):
        st.session_state["selected_antrengung"] = "acceptable"
        st.rerun()
with col5:
    if antrengung_value == "bad":
        st.markdown("### 🥵 sehr anstrengend") # Highlighted
    elif st.button("🥵 sehr anstrengend", key="smiley_bad"):
        st.session_state["selected_antrengung"] = "bad"
        st.rerun()


# --- Sternebewertung (Highlighting Implementierung) ---
st.write("Wie würdest du dieses Workout bewerten?")
star_rating_value = st.session_state["selected_star_rating"]

cols_stars = st.columns(5)
for i in range(1, 6):
    with cols_stars[i-1]:
        # Wenn der aktuelle Stern der ausgewählte ist, zeige ihn als fettgedruckten Text
        if star_rating_value == i:
            st.markdown(f"**{'⭐' * i}**") # Verwende Markdown für fette Sterne
        # Andernfalls zeige den Button an
        elif st.button("⭐" * i, key=f"star_button_{i}"):
            st.session_state["selected_star_rating"] = i
            st.rerun() # Führt einen Rerun aus, um den "gehighlighteten" Zustand zu zeigen


# --- Uploads und Beschreibung ---
image_file = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"], help="Optional: Füge ein Bild deines Workouts hinzu.", key="image_uploader")
gpx_file = st.file_uploader("GPX Datei hochladen", type=["gpx"], help="Optional: Füge eine GPX-Datei deines Workouts hinzu. Max. Größe = 200MB", key="gpx_uploader")
ekg_file = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"], help="Optional: Füge eine EKG-Datei deines Workouts hinzu. Max. Größe = 200MB", key="ekg_uploader")
fit_file = st.file_uploader("FIT Datei hochladen", type=["fit"], help="Optional: Füge eine FIT-Datei deines Workouts hinzu. Max. Größe = 200MB", key="fit_uploader")

description = st.text_area("Beschreibung", value=st.session_state["workout_description_input"], key="workout_description")

st.write("---")

st.write("Kerninformationen zum Workout (falls nicht in Uploads enthalten):")
dauer = st.number_input("Dauer (in Minuten)", min_value=0, step=1, value=st.session_state["workout_dauer_input"], key="workout_dauer")
distanz = st.number_input("Distanz (in km)", min_value=0.0, step=0.1, value=st.session_state["workout_distanz_input"], key="workout_distanz")
puls = st.number_input("Puls (in bpm)", min_value=0, step=1, value=st.session_state["workout_puls_input"], key="workout_puls")
kalorien = st.number_input("Kalorien (in kcal)", min_value=0, step=1, value=st.session_state["workout_kalorien_input"], key="workout_kalorien")


# --- Workout hinzufügen Button ---
if st.button("Workout hinzufügen", key="add_workout_button_final"):
    # Validierung
    if not name:
        st.error("Bitte gib einen Namen für das Workout ein.")
    elif not sportart:
        st.error("Bitte gib eine Sportart ein.")
    elif st.session_state["selected_antrengung"] is None:
        st.error("Bitte bewerte die Anstrengung des Trainings.")
    elif st.session_state["selected_star_rating"] is None:
        st.error("Bitte gib eine Sternebewertung ab.")
    else:
        link_image = save_uploaded_file(image_file, "img", name)
        link_gpx = save_uploaded_file(gpx_file, "gpx", name)
        link_ekg = save_uploaded_file(ekg_file, "ekg", name)
        link_fit = save_uploaded_file(fit_file, "fit", name)

        success = add_workout_to_db(
            person_id=person_doc_id,
            name=name,
            date=date.strftime("%Y-%m-%d"),
            sportart=sportart,
            dauer=dauer,
            distanz=distanz,
            puls=puls,
            kalorien=kalorien,
            anstrengung=st.session_state["selected_antrengung"],
            star_rating=st.session_state["selected_star_rating"],
            description=description,
            image_path=link_image,
            gpx_file_path=link_gpx,
            ekg_file_path=link_ekg,
            fit_file_path=link_fit
        )

        if success:
            # ALLE Session State Variablen, die Felder steuern, zurücksetzen
            st.session_state["workout_name_input"] = ""
            st.session_state["workout_date_input"] = datetime.now().date()
            st.session_state["workout_sportart_input"] = ""
            st.session_state["workout_dauer_input"] = 0
            st.session_state["workout_distanz_input"] = 0.0
            st.session_state["workout_puls_input"] = 0
            st.session_state["workout_kalorien_input"] = 0
            st.session_state["workout_description_input"] = ""
            st.session_state["selected_antrengung"] = None
            st.session_state["selected_star_rating"] = None
            
            # Seite komplett neu laden, um alle Felder zu clearen
            st.switch_page("pages/dashboard.py")