import streamlit as st
import yaml
from yaml.loader import SafeLoader
from tinydb import TinyDB, Query

# --- Initial Page Setup (before any other Streamlit commands) ---
# Sidebar standardmäßig einklappen
st.set_page_config(page_title="Trainingstagebuch", page_icon="💪", layout="wide", initial_sidebar_state="collapsed")

#db = TinyDB('dbperson.json')

# Initialize the session state for login status and user details.
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "name" not in st.session_state:
    st.session_state["name"] = None
if "person_doc_id" not in st.session_state:
    st.session_state["person_doc_id"] = None
if "admin" not in st.session_state:
    st.session_state["admin"] = False
if "person_id" not in st.session_state:
    st.session_state["person_id"] = None
# Neu: Session State für die aktuell ausgewählte Seite
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Login"
if "profile_to_see_name" not in st.session_state:
    st.session_state["profile_to_see_name"] = None



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
                stored_password_plaintext = user_data_from_config.get("password")

                if stored_password_plaintext and input_password == stored_password_plaintext:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = input_username
                    st.session_state["name"] = user_data_from_config.get("name", input_username)
                    
                    
                    current_person_doc_id = user_data_from_config.get("person_doc_id")
                    st.session_state["person_doc_id"] = current_person_doc_id

                    current_person_id = user_data_from_config.get("person_doc_id")
                    st.session_state["person_id"] = current_person_id
               

                    if current_person_doc_id is not None and current_person_doc_id in ADD_PROFILE_WHITELIST:
                        st.session_state["admin"] = True
                    else:
                        st.session_state["admin"] = False

                    if st.session_state["person_doc_id"] is None:
                        st.warning(f"Keine 'person_doc_id' für Benutzer '{input_username}' in 'config.yaml' gefunden. "
                                   "Bitte fügen Sie eine hinzu, um auf die Datenbank zuzugreifen. Sie sind dennoch eingeloggt.")
                    
                    st.success(f"Willkommen, {st.session_state['name']}!")
                    
                    # Nach erfolgreichem Login zur Dashboard-Seite weiterleiten
                    st.session_state["current_page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("Falsches Passwort.")
            else:
                st.error("Benutzername nicht gefunden.")

else: # Benutzer ist eingeloggt
    # Sidebar erweitern, sobald der Benutzer eingeloggt ist
    # HINWEIS: st.set_page_config kann nur einmal ganz am Anfang der App aufgerufen werden.
    # Wir können den initial_sidebar_state hier nicht ändern. Die Sidebar bleibt expandiert,
    # sobald sie einmal durch Inhalt oder st.Page() "aktiviert" wurde.
    # Da wir nun die Sidebar manuell befüllen, wird sie nur angezeigt, wenn dieser Else-Block läuft.
    
    st.sidebar.markdown(
    f"**Willkommen, <span style='font-size: 20px;'>{st.session_state['name']}</span>!**",
    unsafe_allow_html=True
    )

    if st.session_state.get("person_doc_id") != st.session_state.get("person_id"):
        nameto_see = st.session_state.get("profile_to_see_name", "Unbekanntes Profil") # Sicherstellen, dass der Key existiert
        st.sidebar.markdown(
            f"**Du siehst das Profil von,<br><span style='font-size: 20px;'>{nameto_see}</span>!**",
            unsafe_allow_html=True
    )
    
    # Optionen für die Sidebar-Navigation
    sidebar_options = ["Dashboard", "Profil", "Workout hinzufügen", "Testseite", "Person anschauen"]
    if st.session_state["admin"]:
        sidebar_options.append("Profil hinzufügen")
    
    
    # Logout-Button in der Sidebar
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["name"] = None
        st.session_state["person_doc_id"] = None
        st.session_state["admin"] = False
        st.session_state["current_page"] = "Login" # Zurück zur Login-Seite
        st.info("Sie wurden abgemeldet.")
        st.rerun()

    # Inhalt der Hauptseite basierend auf der Auswahl laden
    # Dies ersetzt die pg.run() Logik
    sidebar_pages = [
        st.Page("pages/dashboard.py", title="Lesitungsübersicht", icon="📊"),
        st.Page("pages/Trainingsliste.py", title="Trainingstagebuch", icon="🧪"),
        st.Page("pages/add workout.py", title="Workout hinzufügen", icon="🏋️"),
        st.Page("pages/Profil.py", title="Profil", icon="👤")
        
    ]

    if st.session_state["admin"]:
        sidebar_pages.append(st.Page("pages/add_profile.py", title="Profil hinzufügen", icon="➕"))
        sidebar_pages.append(st.Page("pages/person_anschauen.py", title="Nutzer als Admin betrachten", icon="👀"))


    pg = st.navigation(sidebar_pages, position="sidebar", expanded=True)
    pg.run()