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
'''
import streamlit as st
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
import os
import gpxpy
import gpxpy.gpx

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
if "uploaded_image_file" not in st.session_state:
    st.session_state["uploaded_image_file"] = None
if "uploaded_gpx_file" not in st.session_state:
    st.session_state["uploaded_gpx_file"] = None
if "uploaded_ekg_file" not in st.session_state:
    st.session_state["uploaded_ekg_file"] = None
if "uploaded_fit_file" not in st.session_state:
    st.session_state["uploaded_fit_file"] = None


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

# --- Funktion zum Parsen von GPX-Dateien ---
def parse_gpx_data(gpx_file_path):
    duration_minutes = 0
    total_distance_km = 0.0
    min_time = None
    max_time = None

    try:
        with open(gpx_file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        # Calculate duration by iterating through all track points
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    if point.time:
                        if min_time is None or point.time < min_time:
                            min_time = point.time
                        if max_time is None or point.time > max_time:
                            max_time = point.time
        
        if min_time and max_time:
            time_difference = max_time - min_time
            duration_minutes = int(time_difference.total_seconds() / 60)
        
        # Calculate distance
        total_distance_meters = gpx.length_2d()
        total_distance_km = total_distance_meters / 1000.0

        return duration_minutes, total_distance_km
    except Exception as e:
        st.error(f"Fehler beim Parsen der GPX-Datei: {e}")
        return 0, 0.0

# --- Hilfsfunktion zur Formatierung der Dauer ---
def format_duration(total_minutes):
    if total_minutes < 60:
        return f"{total_minutes} Minuten"
    else:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if minutes == 0:
            return f"{hours} Stunden"
        else:
            return f"{hours} Stunden und {minutes} Minuten"

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
# Use st.session_state to persist uploaded files
st.session_state["uploaded_image_file"] = st.file_uploader("Bild hochladen", type=["jpg", "jpeg", "png"], help="Optional: Füge ein Bild deines Workouts hinzu.", key="image_uploader")
st.session_state["uploaded_gpx_file"] = st.file_uploader("GPX Datei hochladen", type=["gpx"], help="Optional: Füge eine GPX-Datei deines Workouts hinzu. Max. Größe = 200MB", key="gpx_uploader")
st.session_state["uploaded_ekg_file"] = st.file_uploader("EKG Datei hochladen", type=["csv", "txt"], help="Optional: Füge eine EKG-Datei deines Workouts hinzu. Max. Größe = 200MB", key="ekg_uploader")
st.session_state["uploaded_fit_file"] = st.file_uploader("FIT Datei hochladen", type=["fit"], help="Optional: Füge eine FIT-Datei deines Workouts hinzu. Max. Größe = 200MB", key="fit_uploader")

description = st.text_area("Beschreibung", value=st.session_state["workout_description_input"], key="workout_description")

st.write("---")

# --- "Dateien hochladen" Button ---
if st.button("Dateien hochladen und GPX auswerten", key="upload_files_button"):
    temp_gpx_path = None
    if st.session_state["uploaded_gpx_file"]:
        # Save the GPX file temporarily to read it
        temp_gpx_path = os.path.join(UPLOAD_DIR, "temp_gpx_file.gpx")
        with open(temp_gpx_path, "wb") as f:
            f.write(st.session_state["uploaded_gpx_file"].getbuffer())
        
        duration_minutes, distance_km = parse_gpx_data(temp_gpx_path)
        
        if duration_minutes > 0:
            st.session_state["workout_dauer_input"] = duration_minutes
            st.success(f"Dauer aus GPX-Datei erkannt: {format_duration(duration_minutes)}.")
        if distance_km > 0.0:
            st.session_state["workout_distanz_input"] = round(distance_km, 2)
            st.success(f"Distanz aus GPX-Datei erkannt: {round(distance_km, 2)} km.")
        
        # Clean up the temporary file
        if os.path.exists(temp_gpx_path):
            os.remove(temp_gpx_path)
            
    st.rerun() # Rerun to update input fields with parsed data


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
        # Save files AFTER the "Dateien hochladen" button has been clicked and potentially parsed
        link_image = save_uploaded_file(st.session_state["uploaded_image_file"], "img", name)
        link_gpx = save_uploaded_file(st.session_state["uploaded_gpx_file"], "gpx", name)
        link_ekg = save_uploaded_file(st.session_state["uploaded_ekg_file"], "ekg", name)
        link_fit = save_uploaded_file(st.session_state["uploaded_fit_file"], "fit", name)

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
            st.session_state["uploaded_image_file"] = None
            st.session_state["uploaded_gpx_file"] = None
            st.session_state["uploaded_ekg_file"] = None
            st.session_state["uploaded_fit_file"] = None
            
            # Seite komplett neu laden, um alle Felder zu clearen
            st.switch_page("pages/dashboard.py")