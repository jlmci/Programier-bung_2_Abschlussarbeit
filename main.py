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