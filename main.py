'''
import streamlit as st
import bcrypt
import yaml
from yaml.loader import SafeLoader

# --- Initial Page Setup (before any other Streamlit commands) ---
st.set_page_config(page_title="Trainingstagebuch", page_icon="💪", layout= "wide")


# Initialize the session state for login status and user details.
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None

# --- Benutzerdaten aus config.yaml laden ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    USER_CREDENTIALS = config.get('credentials', {}).get('usernames', {})
    if not USER_CREDENTIALS:
        st.error("Keine Benutzeranmeldeinformationen in 'config.yaml' gefunden. Bitte prüfen Sie die Datei.")
        st.stop()
except FileNotFoundError:
    st.error("Die Datei 'config.yaml' wurde nicht gefunden. Bitte erstellen Sie sie und füllen Sie die Benutzerdaten aus.")
    st.stop()
except yaml.YAMLError as exc:
    st.error(f"Fehler beim Parsen der 'config.yaml' Datei: {exc}. Bitte überprüfen Sie die Syntax.")
    st.stop()


# --- Funktion zum Hashen von Passwörtern--- noch nicht verbunden mit dem rest
def generate_password_hash(password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return hashed_password

# --- Streamlit App---

# --- Login-Formular ---
if not st.session_state["logged_in"]:
    st.title("Login zum Trainingstagebuch")

    with st.form("login_form"):
        input_username = st.text_input("Benutzername")
        input_password = st.text_input("Passwort", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if input_username in USER_CREDENTIALS:
                user_data = USER_CREDENTIALS[input_username]
                stored_hash = user_data.get("password")

                if stored_hash and isinstance(stored_hash, str):
                    try:
                        if bcrypt.checkpw(input_password.encode('utf-8'), stored_hash.encode('utf-8')):
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = input_username
                            st.session_state["name"] = user_data.get("name", input_username)
                            st.success(f"Willkommen, {st.session_state['name']}!")
                            st.rerun()
                        else:
                            st.error("Falsches Passwort.")
                    except ValueError as e:
                        st.error(f"Fehler bei der Passwortüberprüfung (Hash-Format?). Kontaktieren Sie den Support. Details: {e}")
                else:
                    st.error("Interner Fehler: Gehashtes Passwort für diesen Benutzer ist ungültig oder fehlt.")
            else:
                st.error("Benutzername nicht gefunden.")

else: # Benutzer ist eingeloggt
    st.sidebar.markdown(f"**Willkommen, {st.session_state['name']}!**")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["name"] = None
        st.info("Sie wurden abgemeldet.")
        st.rerun()
        

    # --- Navigation für eingeloggte Benutzer ---
    pg = st.navigation([
        st.Page("pages/Profil.py", title="Profil", icon="👤"),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/add workout.py", title="Workout hinzufügen", icon="🏋️"),
        st.Page("pages/Test 1.py", title="Testseite", icon="🧪")
    ], position="sidebar", expanded=True)
    pg.run()
    '''

# main_app.py
import streamlit as st
import yaml
from yaml.loader import SafeLoader
# bcrypt wird nicht mehr benötigt, wenn keine Hashes verwendet werden

# --- Initial Page Setup (before any other Streamlit commands) ---
st.set_page_config(page_title="Trainingstagebuch", page_icon="💪", layout="wide")


# Initialize the session state for login status and user details.
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None
if "person_doc_id" not in st.session_state:
    st.session_state["person_doc_id"] = None
if "allowed_to_add_profile" not in st.session_state:
    st.session_state["allowed_to_add_profile"] = False


# --- Benutzerdaten aus config.yaml laden ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    USER_CREDENTIALS = config.get('credentials', {}).get('usernames', {})
    PERMISSIONS = config.get('permissions', {})
    ADD_PROFILE_WHITELIST = PERMISSIONS.get('can_add_profile_doc_ids', [])

    if not USER_CREDENTIALS:
        st.error("Keine Benutzeranmeldeinformationen in 'config.yaml' gefunden. Bitte prüfen Sie die Datei.")
        st.stop()
except FileNotFoundError:
    st.error("Die Datei 'config.yaml' wurde nicht gefunden. Bitte erstellen Sie sie und füllen Sie die Benutzerdaten aus.")
    st.stop()
except yaml.YAMLError as exc:
    st.error(f"Fehler beim Parsen der 'config.yaml' Datei: {exc}. Bitte überprüfen Sie die Syntax.")
    st.stop()


# --- Die Funktion zum Hashen von Passwörtern wird nicht mehr benötigt/entfernt ---
# def generate_password_hash(password):
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
#     return hashed_password

# --- Streamlit App---

# --- Login-Formular ---
if not st.session_state["logged_in"]:
    st.title("Login zum Trainingstagebuch")

    with st.form("login_form"):
        input_username = st.text_input("Benutzername")
        input_password = st.text_input("Passwort", type="password") # Hier bleibt 'type="password"', um die Eingabe zu verstecken
        submit_button = st.form_submit_button("Login")

        if submit_button:
            if input_username in USER_CREDENTIALS:
                user_data_from_config = USER_CREDENTIALS[input_username]
                stored_password_plaintext = user_data_from_config.get("password") # <-- Hier holen wir das Klartext-Passwort

                # --- NEU: Direkter Vergleich der Passwörter ---
                if stored_password_plaintext and input_password == stored_password_plaintext:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = input_username
                    st.session_state["name"] = user_data_from_config.get("name", input_username)
                    
                    current_person_doc_id = user_data_from_config.get("person_doc_id")
                    st.session_state["person_doc_id"] = current_person_doc_id

                    if current_person_doc_id is not None and current_person_doc_id in ADD_PROFILE_WHITELIST:
                        st.session_state["allowed_to_add_profile"] = True
                    else:
                        st.session_state["allowed_to_add_profile"] = False

                    if st.session_state["person_doc_id"] is None:
                        st.warning(f"Keine 'person_doc_id' für Benutzer '{input_username}' in 'config.yaml' gefunden. "
                                   "Bitte fügen Sie eine hinzu, um auf die Datenbank zuzugreifen. Sie sind dennoch eingeloggt.")
                    
                    st.success(f"Willkommen, {st.session_state['name']}!")
                    st.rerun()
                else:
                    st.error("Falsches Passwort.")
            else:
                st.error("Benutzername nicht gefunden.")

else: # Benutzer ist eingeloggt
    st.sidebar.markdown(f"**Willkommen, {st.session_state['name']}!**")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["name"] = None
        st.session_state["person_doc_id"] = None
        st.session_state["allowed_to_add_profile"] = False
        st.info("Sie wurden abgemeldet.")
        st.rerun()

    # --- Navigation für eingeloggte Benutzer ---
    sidebar_pages = [
        st.Page("pages/Profil.py", title="Profil", icon="👤"),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/add workout.py", title="Workout hinzufügen", icon="🏋️"),
        st.Page("pages/Trainingsliste.py", title="Testseite", icon="🧪")
    ]

    if st.session_state["allowed_to_add_profile"]:
        sidebar_pages.append(st.Page("pages/add_profile.py", title="Profil hinzufügen", icon="➕"))


    pg = st.navigation(sidebar_pages, position="sidebar", expanded=True)
    pg.run()