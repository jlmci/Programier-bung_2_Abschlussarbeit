import streamlit as st
from datetime import datetime
from tinydb import TinyDB, Query
import os
import sys

# Stelle sicher, dass das Verzeichnis mit hilfsfunktionenedittraining.py im sys.path ist
script_dir = os.path.dirname(os.path.abspath(__file__))
# Gehe ein Verzeichnis hoch, um den Ordner zu finden, in dem hilfsfunktionenedittraining.py liegt
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importiere die Funktionen aus der neuen Datei
# parse_fit_data, parse_gpx_data, save_uploaded_file wurden in hilfsfunktionenedittraining.py angepasst
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
            if doc_id not in current_ekg_tests:
                current_ekg_tests.append(doc_id)
                dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_id)])
                st.success(f"Training erfolgreich mit Person {person_id} verknüpft.")
            else:
                st.info(f"Training mit ID {doc_id} war bereits für Person {person_id} registriert.")
        else:
            st.warning(f"Person mit ID {person_id} nicht gefunden. Training wurde hinzugefügt, aber nicht verknüpft.")
        return True
    except Exception as e:
        st.error(f"Fehler beim Hinzufügen des Trainings: {e}")
        return False

def update_training_in_db(training_data, training_doc_id):
    """Aktualisiert ein bestehendes Training in der dbtests-Datenbank."""
    try:
        db.update(training_data, doc_ids=[training_doc_id])
        st.success(f"Training mit ID {training_doc_id} erfolgreich aktualisiert!")
        return True
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren des Trainings mit ID {training_doc_id}: {e}")
        return False

# --- Hauptlogik der Seite ---
def add_workout_page():
    st.title("Workout hinzufügen oder bearbeiten")

    current_user_id = st.session_state.get("person_doc_id")
    if not current_user_id:
        st.warning("Bitte melden Sie sich an, um Workouts hinzuzufügen oder zu bearbeiten.")
        return

    editing_training_id = st.session_state.get('editing_training_id')

    if editing_training_id:
        st.subheader(f"Workout bearbeiten (ID: {editing_training_id})")
        
        # Lade die Daten des zu bearbeitenden Trainings
        training_to_edit = db.get(doc_id=editing_training_id)

        if training_to_edit:
            submitted_data = display_workout_form(initial_data=training_to_edit, form_key_suffix="edit")
            
            if submitted_data == "CANCEL":
                st.session_state.editing_training_id = None # End edit mode
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
        # Zeige das Formular im Hinzufügen-Modus
        submitted_data = display_workout_form(form_key_suffix="add")

        if submitted_data:
            if add_training_to_db(submitted_data, current_user_id):
                st.success("Workout erfolgreich hinzugefügt!")
                # Optional: Felder zurücksetzen oder zur Trainingsliste wechseln
                st.session_state.initial_expand_done = False # Reset for trainingsliste
                st.switch_page("pages/trainingsliste.py") # Wechsel zur Trainingsliste

# Dies ist, wie Streamlit die Seite ausführt, wenn sie ausgewählt wird
if __name__ == "__main__":
    add_workout_page()
