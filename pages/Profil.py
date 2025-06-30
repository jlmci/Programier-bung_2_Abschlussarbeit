
import streamlit as st
import os
import sys
import inspect
from tinydb import TinyDB, Query
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
from yaml.dumper import Dumper # For saving YAML

# --- Path setup (assuming this is correct for your project) ---
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# --- Import your Person class ---
from Person.Personenklasse import Person

# --- Initialize TinyDB ---
# Wichtig: Stelle sicher, dass dies der korrekte Pfad zu deiner Personendatenbank ist.
# Basierend auf dem, was in main.py angedeutet wurde, ist 'db/persons.json' wahrscheinlicher.
# Wenn deine Datei 'dbperson.json' im Hauptverzeichnis ist, ändere es hier.
db = TinyDB('dbperson.json') 

# --- YAML Configuration Loading (similar to main.py) ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    USER_CREDENTIALS = config.get('credentials', {}).get('usernames', {})
    
except FileNotFoundError:
    st.error("Die Datei 'config.yaml' wurde nicht gefunden. Bitte erstellen Sie sie und füllen Sie die Benutzerdaten aus.")
    st.stop()
except yaml.YAMLError as exc:
    st.error(f"Fehler beim Parsen der 'config.yaml' Datei: {exc}. Bitte überprüfen Sie die Syntax.")
    st.stop()


# --- Function to save config.yaml ---
def save_config(config_data):
    try:
        with open('config.yaml', 'w') as file:
            yaml.dump(config_data, file, default_flow_style=False, Dumper=Dumper)
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern der 'config.yaml' Datei: {e}")
        return False

# --- Streamlit App starts here ---

# Session State for the current user's ID
# Ensure current_user_id is properly set from main.py's login
if "person_doc_id" not in st.session_state or st.session_state["person_doc_id"] is None:
    st.error("Bitte warten")
    st.stop()

st.session_state.current_user_id = str(st.session_state["person_doc_id"])

# --- Retrieve User Data ---
try:
    user_data = db.get(doc_id=int(st.session_state.current_user_id))
    if user_data is None:
        st.error(f"Nutzer mit ID {st.session_state.current_user_id} nicht gefunden in der Personendatenbank. Stellen Sie sicher, dass die Person existiert.")
        st.stop()
except ValueError:
    st.error("Ungültige Nutzer-ID im Session State. Bitte wählen Sie eine gültige ID.")
    st.stop()

# --- Create Person object ---
Nutzer = Person(
    doc_id=int(st.session_state.current_user_id),
    date_of_birth=user_data["date_of_birth"],
    firstname=user_data["firstname"],
    lastname=user_data["lastname"],
    picture_path=user_data.get("picture_path", "pictures/default.jpg"), # Default image if not set
    gender=user_data["gender"],
    ekg_test_ids=user_data.get("ekg_tests", []), # Use .get with default for missing key
    maximal_hr=user_data.get("maximalpuls", 200)
)

# --- Streamlit Layout ---
st.title("Nutzerprofil Bearbeiten")

bild_col, personendaten_col = st.columns([1,2], gap="small")

with bild_col:
    st.markdown("<div style='padding-top: 23px; font-size: 32px;'>Profilbild</div>", unsafe_allow_html=True)
    if Nutzer.picture_path and os.path.exists(Nutzer.picture_path):
        st.image(Nutzer.picture_path, caption="Aktuelles Profilbild", use_container_width=True)
    else:
        st.image("https://via.placeholder.com/150", caption="Kein Bild gefunden", use_container_width=True)

    st.subheader("Bild hochladen")
    uploaded_file = st.file_uploader("Wählen Sie ein neues Profilbild", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        upload_dir = "uploaded_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        new_picture_path = os.path.join(upload_dir, uploaded_file.name)
        
        with open(new_picture_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        Nutzer.picture_path = new_picture_path
        st.success("Bild erfolgreich hochgeladen und gesetzt!")
        st.experimental_rerun() # Rerun to display the new image immediately


with personendaten_col:
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader("Personen-Informationen (Datenbank)")

    # Find the current user's entry in USER_CREDENTIALS by person_doc_id
    current_username_in_config = None
    user_config_entry = None
    for uname, udata in USER_CREDENTIALS.items():
        if udata.get("person_doc_id") == int(st.session_state.current_user_id):
            current_username_in_config = uname
            user_config_entry = udata
            break

    st.write(f"**ID:** {st.session_state.current_user_id}")
    # Moved the username display here
    if current_username_in_config:
        st.write(f"**Benutzername:** `{current_username_in_config}`")
    else:
        st.warning("Kein zugehöriger Benutzername in config.yaml gefunden.")
    
    new_firstname = st.text_input("Vorname:", Nutzer.firstname)
    new_lastname = st.text_input("Nachname:", Nutzer.lastname)
    
    new_date_of_birth = st.number_input(
        "Geburtsjahr:",
        min_value=1900,
        max_value=datetime.now().year,
        value=Nutzer.date_of_birth,
        step=1
    )
    
    new_gender = st.selectbox("Geschlecht:", ["male", "female", "other"], index=["male", "female", "other"].index(Nutzer.gender))
    
    st.write("Alter:", Nutzer.age)
    
    current_maximalpuls = Nutzer.maximal_hr
    min_puls = 100
    max_puls = 220

    slider_value = max(min_puls, min(max_puls, current_maximalpuls)) # Ensure value is within bounds
    new_maximalpuls = st.slider(
        "Maximalpuls:",
        min_value=min_puls,
        max_value=max_puls,
        value=slider_value,
        step=1
    )
    st.write(f"Anzahl Trainings: {len(Nutzer.ekg_test_ids)}")

    if st.button("Allgemeine Änderungen speichern"):
        try:
            # Update TinyDB
            db.update(
                {
                    "firstname": new_firstname,
                    "lastname": new_lastname,
                    "date_of_birth": new_date_of_birth,
                    "gender": new_gender,
                    "picture_path": Nutzer.picture_path,
                    "maximalpuls": new_maximalpuls,
                },
                doc_ids=[int(st.session_state.current_user_id)]
            )

            # --- Update config.yaml with new name ---
            # Re-fetch current_username_in_config and user_config_entry just in case
            current_username_in_config_for_name_update = None
            user_config_entry_for_name_update = None
            for uname, udata in USER_CREDENTIALS.items():
                if udata.get("person_doc_id") == int(st.session_state.current_user_id):
                    current_username_in_config_for_name_update = uname
                    user_config_entry_for_name_update = udata
                    break
            
            if current_username_in_config_for_name_update:
                # Make a copy to modify
                updated_config_for_name = config.copy()
                updated_usernames_for_name = updated_config_for_name.get('credentials', {}).get('usernames', {}).copy()

                # Update the 'name' field for the specific user
                updated_usernames_for_name[current_username_in_config_for_name_update]['name'] = f"{new_firstname} {new_lastname}"
                
                # Update the config dictionary
                updated_config_for_name['credentials']['usernames'] = updated_usernames_for_name

                if save_config(updated_config_for_name):
                    st.success("Allgemeine Personen-Informationen und Name in config.yaml erfolgreich gespeichert!")
                else:
                    st.error("Fehler beim Speichern des Namens in config.yaml.")
            else:
                st.warning("Kein Login-Eintrag für diesen Nutzer in 'config.yaml' gefunden. Name in config.yaml wurde nicht aktualisiert.")
            # --- ENDE NAMEN FUNKTIONALITÄT ---

            st.rerun() # Rerun to reflect changes
        except Exception as e:
            st.error(f"Ein unerwarteter Fehler beim Speichern der allgemeinen Informationen ist aufgetreten: {e}")

    # The password display and login change form remain in this section.
    # We already found current_username_in_config and user_config_entry above
    # so we can reuse them here.
    if current_username_in_config:
        st.markdown("---") # Keep the separator before the form
        st.write("### Benutzername oder Passwort ändern")

        with st.form("change_login_form"):
            st.write("Um Benutzername oder Passwort zu ändern, bestätigen Sie bitte Ihr aktuelles Passwort.")
            
            # --- MODIFIZIERTE LOGIK HIER: Vorbefüllen des Passwortfeldes für Admins ---
            initial_password_value = ""
            if st.session_state["admin"]:
                initial_password_value = user_config_entry.get('password', '')
                st.info("Das aktuelle Passwort wurde automatisch eingefügt, weil du Admin bist.") # Added a hint
            
            confirm_current_password = st.text_input(
                "Aktuelles Passwort bestätigen:",
                type="password",
                value=initial_password_value # Set the initial value
            )
            # --- ENDE MODIFIZIERTER LOGIK ---

            new_username = st.text_input("Neuer Benutzername (optional):", value=current_username_in_config)
            new_password = st.text_input("Neues Passwort (optional, leer lassen für keine Änderung):", type="password")
            new_password_confirm = st.text_input("Neues Passwort bestätigen:", type="password")
            
            submit_login_change = st.form_submit_button("Login-Informationen ändern")

            if submit_login_change:
                # Validate current password
                if confirm_current_password != user_config_entry.get('password'):
                    st.error("Das eingegebene aktuelle Passwort ist falsch.")
                else:
                    # Check for username change
                    username_changed = False
                    if new_username != current_username_in_config:
                        if new_username in USER_CREDENTIALS and new_username != current_username_in_config:
                            st.error(f"Der Benutzername '{new_username}' existiert bereits. Bitte wählen Sie einen anderen.")
                            username_changed = False # Reset if name exists
                        elif not new_username:
                            st.error("Der neue Benutzername darf nicht leer sein.")
                            username_changed = False
                        else:
                            username_changed = True
                            
                    # Check for password change
                    password_changed = False
                    if new_password: # Only proceed if new password is not empty
                        if new_password != new_password_confirm:
                            st.error("Neues Passwort und Bestätigung stimmen nicht überein.")
                        else:
                            password_changed = True
                    
                    if not username_changed and not password_changed:
                        st.warning("Keine Änderungen an Benutzername oder Passwort vorgenommen.")
                    elif (username_changed or password_changed): # If at least one change is intended
                        # Make a copy to modify
                        updated_config = config.copy() 
                        updated_usernames = updated_config.get('credentials', {}).get('usernames', {}).copy()

                        # Handle username change
                        if username_changed:
                            # Create new entry, delete old one
                            updated_usernames[new_username] = user_config_entry.copy() # Copy old data
                            # Ensure name is carried over, potentially updated with latest from DB save
                            updated_usernames[new_username]['name'] = f"{new_firstname} {new_lastname}" 
                            
                            # Update password in the new entry if changed
                            if password_changed:
                                updated_usernames[new_username]['password'] = new_password
                            
                            del updated_usernames[current_username_in_config] # Delete old username entry
                            
                            st.session_state["username"] = new_username # Update session state immediately
                            st.session_state["name"] = updated_usernames[new_username].get("name", new_username) # Update display name if it changed
                            
                        elif password_changed: # Only password changed, username is the same
                            updated_usernames[current_username_in_config]['password'] = new_password
                            # Ensure the name is the latest from DB, even if only password changed
                            updated_usernames[current_username_in_config]['name'] = f"{new_firstname} {new_lastname}"

                        # Update the config dictionary
                        updated_config['credentials']['usernames'] = updated_usernames

                        if save_config(updated_config):
                            st.success("Login-Informationen erfolgreich aktualisiert!")
                            # Important: Rerun to reload the config from the updated file
                            # and reflect changes like new username in sidebar.
                            st.rerun()
                        else:
                            st.error("Fehler beim Speichern der Konfiguration.")

    else:
        st.warning("Kein Login-Eintrag für diesen Nutzer in 'config.yaml' gefunden. Benutzername und Passwort können nicht geändert werden.")

# This is how Streamlit will run the page when it's selected
if __name__ == "__main__":
    #st.error("Diese Seite sollte über die Hauptanwendung aufgerufen werden, nicht direkt.")
    st.stop()