
import streamlit as st
import os
import sys
import inspect
from tinydb import TinyDB, Query
from datetime import datetime
import yaml
from yaml.loader import SafeLoader
from yaml.dumper import Dumper

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

#from Module.utils import normalize_path_slashes
#from Module.Personenklasse import Person


from utils import normalize_path_slashes
# --- Import your Person class ---
from Person.Personenklasse import Person


db = TinyDB('dbperson.json')

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



def save_config(config_data):
    """
    Speichert die gegebenen Konfigurationsdaten in der 'config.yaml'-Datei.

    Args:
        config_data (dict): Ein Dictionary, das die zu speichernden Konfigurationsdaten enthält.
                            Dieses Dictionary wird im YAML-Format in die Datei geschrieben.

    Returns:
        bool: True, wenn die Konfigurationsdaten erfolgreich gespeichert wurden.
              False, wenn ein Fehler beim Speichern aufgetreten ist.
    """
    try:
        with open('config.yaml', 'w') as file:
            yaml.dump(config_data, file, default_flow_style=False, Dumper=Dumper)
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern der 'config.yaml' Datei: {e}")
        return False



# --- Streamlit App starts here ---

if "person_doc_id" not in st.session_state or st.session_state["person_doc_id"] is None:
    st.error("Bitte warten")
    st.stop()

st.session_state.current_user_id = str(st.session_state["person_doc_id"])


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
    picture_path=normalize_path_slashes(user_data.get("picture_path", "pictures/default.jpg")),
    gender=user_data["gender"],
    ekg_test_ids=user_data.get("ekg_tests", []),
    maximal_hr=user_data.get("maximalpuls", 200)
)

# --- Streamlit Layout ---
bild_col, personendaten_col, daten_ändern = st.columns([1,1,1], gap="small")

with bild_col:
    if Nutzer.picture_path and os.path.exists(Nutzer.picture_path):
        st.image(Nutzer.picture_path, caption="Aktuelles Profilbild", use_container_width=True)
    else:
        default_image_path = os.path.join(parentdir, "data", "pictures", "default.jpg")
        if os.path.exists(default_image_path):
            st.image(default_image_path, caption="Kein Bild gefunden", use_container_width=True)
        else:
            st.warning(f"Standardbild '{default_image_path}' nicht gefunden. Bitte überprüfen Sie den Pfad.")
            st.image("https://via.placeholder.com/150", caption="Kein Bild verfügbar", use_container_width=True)

    uploaded_file = st.file_uploader("Profilbild ändern", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        upload_dir = "uploaded_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        new_picture_path = os.path.join(upload_dir, uploaded_file.name)
        
        with open(new_picture_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        Nutzer.picture_path = normalize_path_slashes(new_picture_path) 
        
        
        db.update({"picture_path": Nutzer.picture_path}, doc_ids=[int(st.session_state.current_user_id)]) # <--- NEU: Füge diese Zeile hinzu!
        
        st.success("Bild erfolgreich hochgeladen und gesetzt!")
        st.rerun()


with personendaten_col:
    st.markdown(
    f"<span style='font-size: 42px; font-weight: bold;'>{Nutzer.firstname} {Nutzer.lastname}</span>",
    unsafe_allow_html=True
)

    current_username_in_config = None
    user_config_entry = None
    for uname, udata in USER_CREDENTIALS.items():
        if udata.get("person_doc_id") == int(st.session_state.current_user_id):
            current_username_in_config = uname
            user_config_entry = udata
            break

    st.markdown(f"**Benutzername:** `{current_username_in_config}`" if current_username_in_config else "Kein Benutzername gefunden.")
    st.markdown(f"**ID:** {st.session_state.current_user_id}")

    
    
    # Initialisiere admin_mode
    admin_mode = st.session_state.get("toggle_admin_edit_mode", False)

    if admin_mode:
        st.markdown("---")
        
        with st.container(border=True): 
            st.write("Admin-Modus Nutzerdaten ändern.")
            new_firstname = st.text_input("Vorname:", Nutzer.firstname, key="admin_firstname")
            new_lastname = st.text_input("Nachname:", Nutzer.lastname, key="admin_lastname")
            
            new_date_of_birth = st.number_input(
                "Geburtsjahr:",
                min_value=1900,
                max_value=datetime.now().year,
                value=Nutzer.date_of_birth,
                step=1,
                key="admin_dob"
            )
            
            new_gender = st.selectbox(
                "Geschlecht", 
                ["male", "female", "other"], 
                index=["male", "female", "other"].index(Nutzer.gender),
                key="admin_gender"
            )

            if st.button("Nutzer Daten speichern", key="save_admin_general_data"):
                try:
                    db.update(
                        {
                            "firstname": new_firstname,
                            "lastname": new_lastname,
                            "date_of_birth": new_date_of_birth,
                            "gender": new_gender,
                            "picture_path": Nutzer.picture_path,
                            "maximalpuls": Nutzer.maximal_hr,
                        },
                        doc_ids=[int(st.session_state.current_user_id)]
                    )

                    if current_username_in_config:
                        updated_config_for_name = config.copy()
                        updated_usernames_for_name = updated_config_for_name.get('credentials', {}).get('usernames', {}).copy()
                        updated_usernames_for_name[current_username_in_config]['name'] = f"{new_firstname} {new_lastname}"
                        updated_config_for_name['credentials']['usernames'] = updated_usernames_for_name

                        if save_config(updated_config_for_name):
                            st.success("Allgemeine Personen-Informationen und Name in config.yaml erfolgreich gespeichert!")
                        else:
                            st.error("Fehler beim Speichern des Namens in config.yaml.")
                    else:
                        st.warning("Kein Login-Eintrag für diesen Nutzer in 'config.yaml' gefunden. Name in config.yaml wurde nicht aktualisiert.")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Ein unerwarteter Fehler beim Speichern der allgemeinen Informationen ist aufgetreten: {e}")
        st.markdown("---")
    else:
        # Standard User View (Read-Only)
        st.markdown(f"**⚧️** {Nutzer.gender.capitalize()}")
        st.markdown(f"🎂  {Nutzer.age} ({Nutzer.date_of_birth})")
        st.markdown(f"🏃‍♂️  {len(Nutzer.ekg_test_ids)} trainings absolviert")

    with st.container(border=True): 
        st.write("Maximalpuls anpassen:")
        current_maximalpuls = Nutzer.maximal_hr
        min_puls = 100
        max_puls = 220

        slider_value = max(min_puls, min(max_puls, current_maximalpuls))
        new_maximalpuls = st.slider(
            "Maximalpuls:",
            min_value=min_puls,
            max_value=max_puls,
            value=slider_value,
            step=1,
            key="user_maximalpuls_slider"
        )

        if st.button("Maximalpuls speichern", key="save_maximalpuls"):
            try:
                db.update(
                    {"maximalpuls": new_maximalpuls},
                    doc_ids=[int(st.session_state.current_user_id)]
                )
                st.success("Maximalpuls erfolgreich gespeichert!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Speichern des Maximalpulses: {e}")
    admin_button_placeholder = st.empty()
    # Admin-Button am Ende der Spalte
    if st.session_state.get("admin", False):
        button_label = "Admin-Modus deaktivieren" if admin_mode else "Admin-Modus: Allgemeine Daten bearbeiten"
        if admin_button_placeholder.button(button_label, key="toggle_admin_edit_mode_button"):
            st.session_state.toggle_admin_edit_mode = not st.session_state.get("toggle_admin_edit_mode", False)
            st.rerun()


with daten_ändern:
    if current_username_in_config:
        st.markdown(
        f"<span style='font-size: 30px; font-weight: bold;'>Login Informationen ändern</span>",
        unsafe_allow_html=True
    )

        with st.form("change_login_form"):
            
            initial_password_value = ""
            if st.session_state.get("admin", False):
                initial_password_value = user_config_entry.get('password', '')
                
            
            confirm_current_password = st.text_input(
                "Identität bestätigen  \n Aktuelles Passwort:",
                type="password",
                value=initial_password_value
            )
            if st.session_state.get("admin", False):
                st.write("Das aktuelle Passwort wurde automatisch eingefügt, weil du Admin bist.")
            new_username = st.text_input("Neuer Benutzername (optional):", value=current_username_in_config)
            new_password = st.text_input("Neues Passwort (optional):", type="password")
            new_password_confirm = st.text_input("Neues Passwort bestätigen:", type="password")
            
            submit_login_change = st.form_submit_button("Login-Informationen ändern")

            if submit_login_change:
                if confirm_current_password != user_config_entry.get('password'):
                    st.error("Das eingegebene aktuelle Passwort ist falsch.")
                else:
                    username_changed = False
                    if new_username != current_username_in_config:
                        if new_username in USER_CREDENTIALS and new_username != current_username_in_config:
                            st.error(f"Der Benutzername '{new_username}' existiert bereits. Bitte wählen Sie einen anderen.")
                            username_changed = False
                        elif not new_username:
                            st.error("Der neue Benutzername darf nicht leer sein.")
                            username_changed = False
                        else:
                            username_changed = True
                            
                    password_changed = False
                    if new_password:
                        if new_password != new_password_confirm:
                            st.error("Neues Passwort und Bestätigung stimmen nicht überein.")
                        else:
                            password_changed = True
                            
                    if not username_changed and not password_changed:
                        st.warning("Keine Änderungen an Benutzername oder Passwort vorgenommen.")
                    elif (username_changed or password_changed):
                        updated_config = config.copy() 
                        updated_usernames = updated_config.get('credentials', {}).get('usernames', {}).copy()

                        if username_changed:
                            updated_usernames[new_username] = user_config_entry.copy()
                            updated_usernames[new_username]['name'] = f"{Nutzer.firstname} {Nutzer.lastname}"
                            
                            if password_changed:
                                updated_usernames[new_username]['password'] = new_password
                            
                            del updated_usernames[current_username_in_config]
                            
                            st.session_state["username"] = new_username
                            st.session_state["name"] = updated_usernames[new_username].get("name", new_username)
                            
                        elif password_changed:
                            updated_usernames[current_username_in_config]['password'] = new_password
                            updated_usernames[current_username_in_config]['name'] = f"{Nutzer.firstname} {Nutzer.lastname}"

                        updated_config['credentials']['usernames'] = updated_usernames

                        if save_config(updated_config):
                            st.success("Login-Informationen erfolgreich aktualisiert!")
                            st.rerun()
                        else:
                            st.error("Fehler beim Speichern der Konfiguration.")
    else:
        st.warning("Kein Login-Eintrag für diesen Nutzer in 'config.yaml' gefunden. Benutzername und Passwort können nicht geändert werden.")

if __name__ == "__main__":
    st.stop()