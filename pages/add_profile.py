
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

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


from Module.utils import normalize_path_slashes




db = TinyDB('dbperson.json')



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


def write_to_config_yaml(new_username, new_user_details, add_to_whitelist=False, new_doc_id=None):
    """
    Schreibt neue Benutzerinformationen in die Konfigurations-YAML-Datei.
    Fügt optional die Dokumenten-ID des neuen Benutzers zur Admin-Whitelist hinzu,
    die steuert, welche Profile neue Benutzerkonten hinzufügen dürfen.

    Args:
        new_username (str): Der **neue Benutzername** (Login-Name) für das Benutzerkonto.
                            Dieser wird als Schlüssel unter `credentials.usernames` in der YAML-Datei verwendet.
        new_user_details (dict): Ein Dictionary, das die **Details des neuen Benutzers** enthält.
                                 Es sollte folgende Schlüssel haben:
                                 - 'name' (str): Der vollständige Anzeigename des Benutzers.
                                 - 'password' (str): Das initiale Passwort des Benutzers (im Klartext).
                                 - 'person_doc_id' (int): Die Dokumenten-ID der zugehörigen Person aus der TinyDB.
        add_to_whitelist (bool, optional): Wenn `True`, wird die `new_doc_id` zur Liste
                                            `permissions.can_add_profile_doc_ids` hinzugefügt.
                                            Profile in dieser Liste haben die Berechtigung, neue Benutzerkonten zu erstellen.
                                            Standardwert ist `False`.
        new_doc_id (int, optional): Die **Dokumenten-ID der neu erstellten Person** aus der 'dbperson'-Datenbank.
                                    Dieser Parameter ist **erforderlich**, wenn `add_to_whitelist` auf `True` gesetzt ist,
                                    da diese ID der Whitelist hinzugefügt wird. Standardwert ist `None`.

    Returns:
        bool: `True`, wenn das Schreiben in die Konfigurationsdatei erfolgreich war.
              `False`, wenn ein Fehler aufgetreten ist (z.B. Dateizugriffsfehler).
    """
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = yaml.load(f, Loader=SafeLoader)
        
        if 'credentials' not in config_data:
            config_data['credentials'] = {}
        if 'usernames' not in config_data['credentials']:
            config_data['credentials']['usernames'] = {}
            
        config_data['credentials']['usernames'][new_username] = new_user_details

        if add_to_whitelist and new_doc_id is not None:
            if 'permissions' not in config_data:
                config_data['permissions'] = {}
            if 'can_add_profile_doc_ids' not in config_data['permissions']:
                config_data['permissions']['can_add_profile_doc_ids'] = []
            
            
            if new_doc_id not in config_data['permissions']['can_add_profile_doc_ids']:
                config_data['permissions']['can_add_profile_doc_ids'].append(new_doc_id)
                
                config_data['permissions']['can_add_profile_doc_ids'].sort()
        
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config_data, f, Dumper=Dumper, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"Fehler beim Schreiben in die '{CONFIG_FILE}': {e}")
        return False

# --- Streamlit Page Setup ---



# --- Sicherheitscheck: Ist der Benutzer eingeloggt und berechtigt? ---
if not st.session_state.get("logged_in", False):
    st.warning("Bitte loggen Sie sich zuerst in der Hauptanwendung ein.")
    st.stop()

admin = st.session_state.get("admin")
if not admin :
    st.error("Sie haben keine Berechtigung, neue Profile hinzuzufügen. Ihre ID ist nicht auf der Whitelist.")
    st.stop()


st.title("Neues Benutzerkonto erstellen")

with st.form("add_profile_form"):
    st.subheader("Profildaten")
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
    
    calculated_default_maxhr = 220 - (current_year - new_date_of_birth)
    new_maximalpuls = st.number_input(
        "Maximalpuls:",
        min_value=100,
        max_value=220,
        value=calculated_default_maxhr,
        step=1,
        key="add_maxhr"
    )
    st.subheader("Profilbild")
    uploaded_file = st.file_uploader("Wählen Sie ein Profilbild für das neue Profil", type=["jpg", "jpeg", "png"], key="add_profile_picture_uploader")
    
    picture_path_to_save = "data/pictures/default.jpg" # Standardbild, falls keins hochgeladen wird

    if uploaded_file is not None:
        upload_dir = "uploaded_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = uploaded_file.name.split('.')[-1]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{new_firstname.lower()}_{new_lastname.lower()}_{timestamp}.{file_extension}"
        
        new_picture_path_full = os.path.join(upload_dir, unique_filename)
        
        try:
            with open(new_picture_path_full, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Bild erfolgreich hochgeladen: {unique_filename}")
            picture_path_to_save = normalize_path_slashes(new_picture_path_full) 
            st.image(picture_path_to_save, caption="Vorschau hochgeladenes Bild", use_container_width=True)
        except Exception as e:
            st.error(f"Fehler beim Speichern des Bildes: {e}")
            st.warning("Es wird ein Standardbild verwendet.")
            picture_path_to_save = normalize_path_slashes("data/pictures/default.jpg")


    st.markdown("---")
    st.subheader("Login-Daten")
    new_username = st.text_input("Neuer Benutzername (für Login):", key="new_login_username")
    new_password = st.text_input("Initiales Passwort:", type="password", key="new_login_password")
    confirm_password = st.text_input("Passwort bestätigen:", type="password", key="confirm_login_password")

    add_to_admin_whitelist = st.checkbox("Person zur Admin-Whitelist hinzufügen", key="add_to_admin_whitelist_checkbox")

    submit_button = st.form_submit_button("Profil & Benutzerkonto erstellen")

    if submit_button:
        
        if not new_firstname or not new_lastname or not new_username or not new_password or not confirm_password:
            st.error("Bitte füllen Sie alle erforderlichen Felder aus (Vorname, Nachname, Benutzername, Passwort).")
        elif new_password != confirm_password:
            st.error("Passwörter stimmen nicht überein.")
        elif new_username in USER_CREDENTIALS:
            st.error(f"Der Benutzername '{new_username}' existiert bereits. Bitte wählen Sie einen anderen.")
        else:
            try:
                
                ekg_tests_list = []
                
                new_profile_data = {
                    "firstname": new_firstname,
                    "lastname": new_lastname,
                    "date_of_birth": new_date_of_birth,
                    "gender": new_gender,
                    "picture_path": picture_path_to_save,
                    "ekg_tests": ekg_tests_list,
                    "maximalpuls": new_maximalpuls
                }

                
                new_doc_id = db.insert(new_profile_data)
                
                
                initial_password_plaintext = new_password

                
                new_user_details = {
                    "name": f"{new_firstname} {new_lastname}",
                    "password": initial_password_plaintext,
                    "person_doc_id": new_doc_id 
                }

                
                if write_to_config_yaml(new_username, new_user_details, add_to_admin_whitelist, new_doc_id):
                    st.success(f"Neues Profil für **{new_firstname} {new_lastname}** erfolgreich erstellt! ")
                    if add_to_admin_whitelist:
                        st.info(f"Person mit ID **{new_doc_id}** wurde zur Admin-Whitelist hinzugefügt.")
                    st.warning("Hinweis: Nach der Erstellung muss die App neu gestartet werden, damit der neue Benutzer in der Login-Maske sichtbar wird und Berechtigungen greifen.")
                    
                    
                else:
                    st.error("Fehler beim Speichern der Benutzerdaten in der config.yaml.")
            except Exception as e:
                st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        