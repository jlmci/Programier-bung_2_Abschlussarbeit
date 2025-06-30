'''
import streamlit as st
from datetime import datetime
from tinydb import TinyDB, Query
import os
import sys

# Pfad zu workout_form_utils.py hinzufügen, falls es nicht im selben Verzeichnis ist
# Dies ist wichtig, wenn workout_form_utils.py in einem Unterordner liegt.
# Angenommen, es liegt im selben Verzeichnis wie add workout.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Importiere die Funktion aus der neuen Datei
from hilfsfunktionenedittraining import display_workout_form, save_uploaded_file, parse_gpx_data, format_duration

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen für die Datenbank-Interaktion ---
def add_training_to_db(training_data, person_id):
    """Fügt ein neues Training zur dbtests-Datenbank hinzu und verknüpft es mit einer Person."""
    try:
        # Füge das Training zu dbtests hinzu
        doc_id = db.insert(training_data)
        st.success(f"Training '{training_data['name']}' erfolgreich hinzugefügt mit ID: {doc_id}")

        # Verknüpfe die Training-ID mit der Person in dbperson
        person_doc = dp.get(doc_id=int(person_id))
        if person_doc:
            current_ekg_tests = person_doc.get('ekg_tests', [])
            current_ekg_tests.append(doc_id)
            dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_id)])
            st.success(f"Training erfolgreich mit Person {person_id} verknüpft.")
        else:
            st.error(f"Fehler: Person mit ID {person_id} nicht in der Personendatenbank gefunden.")
        return True
    except Exception as e:
        st.error(f"Fehler beim Hinzufügen des Trainings: {e}")
        return False

def update_training_in_db(updated_training_data, training_doc_id):
    """Aktualisiert ein Training in der TinyDB."""
    try:
        db.update(updated_training_data, doc_ids=[training_doc_id])
        st.success(f"Training '{updated_training_data['name']}' erfolgreich aktualisiert.")
        return True
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren des Trainings: {e}")
        return False

def get_training_by_id(training_id):
    """Ruft ein Training anhand seiner Doc ID ab."""
    return db.get(doc_id=training_id)

# --- Hauptanwendung ---
def main():
    st.title("Workout hinzufügen / bearbeiten 🏃‍♀️")
    st.markdown("---")

    if "current_user_id" not in st.session_state:
        st.warning("Bitte wähle im Dashboard zuerst eine Person aus.")
        st.stop() # Stoppt die Ausführung der Seite

    current_user_id = st.session_state.current_user_id

    # Prüfen, ob ein Training zum Bearbeiten ausgewählt wurde
    editing_training_id = st.session_state.get('editing_training_id')
    
    if editing_training_id:
        st.subheader("Training bearbeiten")
        training_to_edit = get_training_by_id(editing_training_id)
        if training_to_edit:
            # Zeige das Formular im Bearbeitungsmodus an
            submitted_data = display_workout_form(initial_data=training_to_edit, form_key_suffix="edit")
            
            if submitted_data == "CANCEL":
                st.session_state.editing_training_id = None
                st.session_state.last_editing_id = None # Wichtig: Reset für workout_form_utils
                st.session_state.initial_expand_done = False # Wichtig: Reset für trainingsliste
                st.switch_page("pages/trainingsliste.py") # Zurück zur Liste
            elif submitted_data:
                if update_training_in_db(submitted_data, editing_training_id):
                    st.session_state.editing_training_id = None # Bearbeitungsmodus beenden
                    st.session_state.last_editing_id = None # Wichtig: Reset für workout_form_utils
                    st.session_state.initial_expand_done = False # Wichtig: Reset für trainingsliste
                    st.switch_page("pages/trainingsliste.py") # Zurück zur Liste
        else:
            st.error("Training zum Bearbeiten nicht gefunden.")
            st.session_state.editing_training_id = None # Bearbeitungsmodus beenden
            st.session_state.last_editing_id = None # Wichtig: Reset für workout_form_utils
            st.session_state.initial_expand_done = False # Wichtig: Reset für trainingsliste
            st.switch_page("pages/trainingsliste.py") # Zurück zur Liste, um Fehler zu beheben
    else:
        st.subheader("Neues Workout hinzufügen")
        # Zeige das Formular im Hinzufügen-Modus an
        submitted_data = display_workout_form(form_key_suffix="add")

        if submitted_data:
            if add_training_to_db(submitted_data, current_user_id):
                st.success("Workout erfolgreich hinzugefügt!")
                # Optional: Felder zurücksetzen oder zur Trainingsliste wechseln
                st.session_state.initial_expand_done = False # Wichtig: Reset für trainingsliste
                st.switch_page("pages/trainingsliste.py")


if __name__ == "__main__":
    main()
    '''

import streamlit as st
from datetime import datetime
from tinydb import TinyDB, Query
import os
import sys

# Ensure the directory containing hilfsfunktionenedittraining.py is in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import the functions from the new file
# Make sure parse_fit_data is included in this import list
from hilfsfunktionenedittraining import display_workout_form, save_uploaded_file, parse_gpx_data, parse_fit_data, format_duration

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen für die Datenbank-Interaktion ---
def add_training_to_db(training_data, person_id):
    """Fügt ein neues Training zur dbtests-Datenbank hinzu und verknüpft es mit einer Person."""
    try:
        # Füge das Training zu dbtests hinzu
        doc_id = db.insert(training_data)
        st.success(f"Training '{training_data['name']}' erfolgreich hinzugefügt mit ID: {doc_id}")

        # Verknüpfe die Training-ID mit der Person in dbperson
        person_doc = dp.get(doc_id=int(person_id))
        if person_doc:
            current_ekg_tests = person_doc.get('ekg_tests', [])
            current_ekg_tests.append(doc_id)
            dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_id)])
            st.success(f"Training erfolgreich mit Person {person_id} verknüpft.")
        else:
            st.error(f"Fehler: Person mit ID {person_id} nicht in der Personendatenbank gefunden.")
        return True
    except Exception as e:
        st.error(f"Fehler beim Hinzufügen des Trainings: {e}")
        return False

def update_training_in_db(updated_training_data, training_doc_id):
    """Aktualisiert ein Training in der TinyDB."""
    try:
        db.update(updated_training_data, doc_ids=[training_doc_id])
        st.success(f"Training '{updated_training_data['name']}' erfolgreich aktualisiert.")
        return True
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren des Trainings: {e}")
        return False

def get_training_by_id(training_id):
    """Ruft ein Training anhand seiner Doc ID ab."""
    return db.get(doc_id=training_id)

# --- Hauptanwendung ---
def main():
    st.title("Workout hinzufügen / bearbeiten 🏃‍♀️")
    st.markdown("---")

    if "current_user_id" not in st.session_state:
        st.warning("Bitte wähle im Dashboard zuerst eine Person aus.")
        st.stop() # Stoppt die Ausführung der Seite

    current_user_id = st.session_state.current_user_id

    # Prüfen, ob ein Training zum Bearbeiten ausgewählt wurde
    editing_training_id = st.session_state.get('editing_training_id')
    
    if editing_training_id:
        st.subheader("Training bearbeiten")
        training_to_edit = get_training_by_id(editing_training_id)
        if training_to_edit:
            # Zeige das Formular im Bearbeitungsmodus an
            submitted_data = display_workout_form(initial_data=training_to_edit, form_key_suffix="edit")
            
            if submitted_data == "CANCEL":
                st.session_state.editing_training_id = None
                st.session_state.last_loaded_id_check = None # Reset for workout_form_utils (important!)
                st.session_state.initial_expand_done = False # Reset for trainingsliste
                st.switch_page("pages/trainingsliste.py") # Go back to the list
            elif submitted_data:
                if update_training_in_db(submitted_data, editing_training_id):
                    st.session_state.editing_training_id = None # End edit mode
                    st.session_state.last_loaded_id_check = None # Reset for workout_form_utils (important!)
                    st.session_state.initial_expand_done = False # Reset for trainingsliste
                    st.switch_page("pages/trainingsliste.py") # Go back to the list
        else:
            st.error("Training zum Bearbeiten nicht gefunden.")
            st.session_state.editing_training_id = None # End edit mode
            st.session_state.last_loaded_id_check = None # Reset for workout_form_utils (important!)
            st.session_state.initial_expand_done = False # Reset for trainingsliste
            st.switch_page("pages/trainingsliste.py") # Go back to the list to fix error
    else:
        st.subheader("Neues Workout hinzufügen")
        # Show the form in add mode
        submitted_data = display_workout_form(form_key_suffix="add")

        if submitted_data:
            if add_training_to_db(submitted_data, current_user_id):
                st.success("Workout erfolgreich hinzugefügt!")
                # Optional: Reset fields or switch to the training list
                st.session_state.initial_expand_done = False # Reset for trainingsliste
                st.switch_page("pages/trainingsliste.py")


if __name__ == "__main__":
    main()