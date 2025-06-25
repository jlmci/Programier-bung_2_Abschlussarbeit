# pages/add_profile.py
import streamlit as st
import os
import sys
import inspect
import yaml
from tinydb import TinyDB
from datetime import datetime
from yaml.loader import SafeLoader
from yaml import Dumper

# --- Pfad-Setup für die Person-Klasse (falls benötigt, aber hier nicht direkt verwendet) ---
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# Importiere deine Person-Klasse, auch wenn sie hier nicht instanziiert wird,
# um die Datenstruktur zu verstehen und zu validieren.
# from Person.Personenklasse import Person


# --- TinyDB Initialisierung ---
db = TinyDB('dbperson.json')

# --- Konfigurationsdatei laden (für Berechtigungen und zum Schreiben) ---
CONFIG_FILE = 'config.yaml'
try:
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.load(f, Loader=SafeLoader)
    USER_CREDENTIALS = config.get('credentials', {}).get('usernames', {})
    PERMISSIONS = config.get('permissions', {})
    ADD_PROFILE_WHITELIST = PERMISSIONS.get('can_add_profile_doc_ids', [])
except FileNotFoundError:
    st.error(f"Die Datei '{CONFIG_FILE}' wurde nicht gefunden. Stellen Sie sicher, dass sie im Hauptverzeichnis liegt.")
    st.stop()
except yaml.YAMLError as exc:
    st.error(f"Fehler beim Parsen der '{CONFIG_FILE}' Datei: {exc}. Bitte überprüfen Sie die Syntax.")
    st.stop()

# --- Funktion zum Schreiben in die config.yaml ---
def write_to_config_yaml(new_username, new_user_details):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = yaml.load(f, Loader=SafeLoader)
        
        if 'credentials' not in config_data:
            config_data['credentials'] = {}
        if 'usernames' not in config_data['credentials']:
            config_data['credentials']['usernames'] = {}
            
        config_data['credentials']['usernames'][new_username] = new_user_details
        
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config_data, f, Dumper=Dumper, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"Fehler beim Schreiben in die '{CONFIG_FILE}': {e}")
        return False

# --- Streamlit Page Setup ---
#st.set_page_config(page_title="Neues Profil hinzufügen", page_icon="➕", layout="wide")


# --- Sicherheitscheck: Ist der Benutzer eingeloggt und berechtigt? ---
if not st.session_state.get("logged_in", False):
    st.warning("Bitte loggen Sie sich zuerst in der Hauptanwendung ein.")
    st.stop()

current_user_doc_id = st.session_state.get("person_doc_id")
if current_user_doc_id is None or current_user_doc_id not in ADD_PROFILE_WHITELIST:
    st.error("Sie haben keine Berechtigung, neue Profile hinzuzufügen. Ihre ID ist nicht auf der Whitelist.")
    st.info(f"Ihre ID: {current_user_doc_id}. Erlaubte IDs: {ADD_PROFILE_WHITELIST}")
    st.stop()


st.title("Neues Profil hinzufügen & Benutzerkonto erstellen")
st.write("Füllen Sie die Felder aus, um ein neues Personenprofil zu erstellen und gleichzeitig ein Login-Konto zu verknüpfen.")

with st.form("add_profile_form"):
    st.subheader("Profildaten (für die Datenbank)")
    new_firstname = st.text_input("Vorname:", key="add_firstname")
    new_lastname = st.text_input("Nachname:", key="add_lastname")
    
    current_year = datetime.now().year
    new_date_of_birth = st.number_input(
        "Geburtsjahr:",
        min_value=1900,
        max_value=current_year,
        value=current_year - 30, # Standard: 30 Jahre alt
        step=1,
        key="add_dob"
    )
    
    new_gender = st.selectbox("Geschlecht:", ["male", "female", "other"], key="add_gender")
    
    # --- NEU: Bild-Upload-Option ---
    st.subheader("Profilbild")
    uploaded_file = st.file_uploader("Wählen Sie ein Profilbild für das neue Profil", type=["jpg", "jpeg", "png"], key="add_profile_picture_uploader")
    
    # Pfad für das Bild initialisieren. Wird aktualisiert, wenn ein Bild hochgeladen wird.
    picture_path_to_save = "data/pictures/default.jpg" # Standardbild, falls keins hochgeladen wird

    if uploaded_file is not None:
        upload_dir = "uploaded_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Sicherstellen, dass der Dateiname eindeutig ist, um Überschreiben zu vermeiden
        file_extension = uploaded_file.name.split('.')[-1]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{new_firstname.lower()}_{new_lastname.lower()}_{timestamp}.{file_extension}"
        
        new_picture_path_full = os.path.join(upload_dir, unique_filename)
        
        try:
            with open(new_picture_path_full, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Bild erfolgreich hochgeladen: {unique_filename}")
            picture_path_to_save = new_picture_path_full # Der Pfad, der in die DB gespeichert wird
            st.image(picture_path_to_save, caption="Vorschau hochgeladenes Bild", use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Speichern des Bildes: {e}")
            st.warning("Es wird ein Standardbild verwendet.")
            picture_path_to_save = "data/pictures/default.jpg" # Fallback auf Standardbild

    # Der alte Text-Input für den Bildpfad ist nun optional oder kann entfernt werden,
    # da der Uploader die Hauptmethode ist. Ich lasse ihn als Referenz, falls du manuelle Pfade erlauben willst.
    # new_picture_path_manual = st.text_input("Manuelle Eingabe Bildpfad (überschreibt Upload, optional):", value=picture_path_to_save, key="add_pic_path")
    # if new_picture_path_manual: # Wenn manueller Pfad eingegeben, diesen verwenden
    #     picture_path_to_save = new_picture_path_manual


    new_ekg_tests_str = st.text_input("EKG Test IDs (optional, kommagetrennt, z.B. 1,5,10):", value="", key="add_ekg_tests")

    calculated_default_maxhr = 220 - (current_year - new_date_of_birth)
    new_maximalpuls = st.number_input(
        "Maximalpuls (Optional, 220 - Alter Standard):",
        min_value=100,
        max_value=220,
        value=calculated_default_maxhr,
        step=1,
        key="add_maxhr"
    )

    st.markdown("---")
    st.subheader("Login-Daten (für die config.yaml)")
    new_username = st.text_input("Neuer Benutzername (für Login):", key="new_login_username")
    new_password = st.text_input("Initiales Passwort:", type="password", key="new_login_password")
    confirm_password = st.text_input("Passwort bestätigen:", type="password", key="confirm_login_password")

    submit_button = st.form_submit_button("Profil & Benutzerkonto erstellen")

    if submit_button:
        # --- Validierungen ---
        if not new_firstname or not new_lastname or not new_username or not new_password or not confirm_password:
            st.error("Bitte füllen Sie alle erforderlichen Felder aus (Vorname, Nachname, Benutzername, Passwort).")
        elif new_password != confirm_password:
            st.error("Passwörter stimmen nicht überein.")
        elif new_username in USER_CREDENTIALS:
            st.error(f"Der Benutzername '{new_username}' existiert bereits. Bitte wählen Sie einen anderen.")
        else:
            try:
                # 1. Daten für TinyDB vorbereiten
                ekg_tests_list = []
                if new_ekg_tests_str.strip():
                    try:
                        ekg_tests_list = [int(item.strip()) for item in new_ekg_tests_str.split(',') if item.strip()]
                    except ValueError:
                        st.error("Ungültiges Format für EKG Test IDs. Bitte verwenden Sie nur Zahlen, getrennt durch Kommas.")
                        st.stop()

                new_profile_data = {
                    "firstname": new_firstname,
                    "lastname": new_lastname,
                    "date_of_birth": new_date_of_birth,
                    "gender": new_gender,
                    "picture_path": picture_path_to_save, # <-- NEU: Hier den Pfad vom Uploader/Standard verwenden
                    "ekg_tests": ekg_tests_list,
                    "maximalpuls": new_maximalpuls
                }

                # 2. Profil in TinyDB einfügen und doc_id erhalten
                new_doc_id = db.insert(new_profile_data)
                
                # Das initiale Passwort wird NICHT gehasht, sondern direkt verwendet (wie gewünscht)
                initial_password_plaintext = new_password

                # 3. Daten für config.yaml vorbereiten
                new_user_details = {
                    "name": f"{new_firstname} {new_lastname}",
                    "password": initial_password_plaintext,
                    "person_doc_id": new_doc_id # Die aus der DB erhaltene ID
                }

                # 4. Daten in config.yaml schreiben
                if write_to_config_yaml(new_username, new_user_details):
                    st.success(f"Neues Profil für **{new_firstname} {new_lastname}** erfolgreich erstellt! ")
                    #st.info(f"Zugeordnete Personen-ID (TinyDB): **{new_doc_id}**")
                    #st.info(f"Neuer Login-Benutzername: **{new_username}**")
                    st.warning("Hinweis: Nach der Erstellung muss die App neu gestartet werden, damit der neue Benutzer in der Login-Maske sichtbar wird.")
                    
                    # Optional: Formularfelder zurücksetzen, indem die App neu gerendert wird
                    # (Achtung: Dies würde auch die Erfolgsmeldung entfernen, daher oft manuelles Leeren besser)
                    # st.experimental_rerun() # Oder st.rerun() in neueren Streamlit-Versionen
                else:
                    st.error("Fehler beim Speichern der Benutzerdaten in der config.yaml.")
            except Exception as e:
                st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")