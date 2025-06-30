import streamlit as st
from tinydb import TinyDB, Query
import os

# Initialize TinyDB
db = TinyDB('dbperson.json')

Person = Query()

def person_anschauen_page():
    st.title("Personen ansehen und Ansicht wechseln")

    # Only allow admins to access this page
    if not st.session_state.get("admin"):
        st.warning("Sie haben keine Berechtigung, auf diese Seite zuzugreifen.")
        st.stop()

    st.write("Als Administrator können Sie hier die Ansicht auf andere Personen wechseln, um deren Trainingsdaten zu sehen.")

    # Fetch all persons from the database
    all_persons = db.all()

    if not all_persons:
        st.info("Es sind noch keine Personen in der Datenbank vorhanden.")
        return

    # Create a list of display names for the dropdown, mapping to their doc_ids
    person_options = {f"{p.get('firstname', '')} {p.get('lastname', '')} (ID: {p.doc_id})": p.doc_id for p in all_persons}
    
    # Add a "Yourself" option
    current_user_name = st.session_state.get("name", "Unbekannt")
    current_user_doc_id = st.session_state.get("person_doc_id")
    current_user_id = st.session_state.get("person_id")
    person_options[f"Mich selbst"] = current_user_id 

    # Sort the options alphabetically, but keep "Yourself" at the top if present
    sorted_options_display = sorted([key for key in person_options.keys() if "Mich selbst" not in key])
    if "Mich selbst" in person_options:
        sorted_options_display.insert(0, "Mich selbst")


    # --- Neue Funktion: Suchen nach ID oder Name ---
    st.markdown("---")
    st.subheader("Suchen Sie eine Person nach ID oder Name:")
    search_query = st.text_input("Geben Sie eine ID oder einen Namen ein, um zu suchen:", key="search_input")
    
    found_persons = [] # Liste zum Speichern aller gefundenen Personen

    if search_query:
        # Versuch, als ID zu interpretieren
        try:
            search_id = int(search_query)
            person_by_id = db.get(doc_id=search_id)
            if person_by_id:
                found_persons.append(person_by_id) # Eine Person gefunden über ID
        except ValueError:
            # Wenn keine ID, dann Suche nach Name (Groß-/Kleinschreibung ignorierend, Teiltreffer)
            search_query_lower = search_query.lower()
            for p in all_persons:
                full_name = f"{p.get('firstname', '')} {p.get('lastname', '')}".lower()
                if search_query_lower in full_name:
                    found_persons.append(p) # Füge alle passenden Personen hinzu
            
        if found_persons:
            st.write("Mehrere Personen gefunden:")
            # Erstelle Optionen für das Radio-Button-Widget
            radio_options = {}
            for p in found_persons:
                display_name = f"{p.get('firstname', '')} {p.get('lastname', '')} (ID: {p.doc_id})"
                radio_options[display_name] = p.doc_id

            selected_radio_display = st.radio(
                "Wählen Sie die gewünschte Person aus:",
                options=list(radio_options.keys()),
                key="found_person_selection"
            )

            if selected_radio_display:
                selected_doc_id_from_search = radio_options[selected_radio_display]
                selected_person_name_from_search = selected_radio_display.split(' (ID:')[0]

                if st.button(f"Als '{selected_person_name_from_search}' ansehen"):
                    if selected_doc_id_from_search == st.session_state["person_doc_id"]:
                        st.info("Sie sehen bereits die Daten dieser Person an.")
                    else:
                        st.session_state["person_doc_id"] = selected_doc_id_from_search
                        st.session_state["profile_to_see_name"] = selected_person_name_from_search
                        
                        # Update the displayed name
                        selected_person_data = db.get(doc_id=selected_doc_id_from_search)
                        #if selected_person_data:
                            #st.session_state["name"] = f"{selected_person_data.get('firstname', '')} {selected_person_data.get('lastname', '')}"
                        
                        st.success(f"Sie sehen nun die Daten von '{st.session_state['name']}' an.")
                        st.info("Navigieren Sie zum Dashboard oder anderen Seiten, um die aktualisierten Daten zu sehen.")
                        st.switch_page("pages/Profil.py")
                        st.rerun()
        else:
            st.warning("Keine Person mit der angegebenen ID oder dem Namen gefunden.")
    # --- Ende der neuen Suchfunktion ---

    st.markdown("---")

    # --- Vorhandene Dropdown-Auswahl ---
    selected_person_display = st.selectbox(
        "Oder wählen Sie eine Person aus der Liste:",
        options=sorted_options_display,
        key="dropdown_selection"
    )

    selected_doc_id_from_dropdown = None
    if selected_person_display:
        selected_doc_id_from_dropdown = person_options[selected_person_display]

    if selected_doc_id_from_dropdown:
        if st.button(f"Als '{selected_person_display.split(' (ID:')[0]}' ansehen"):
            if selected_doc_id_from_dropdown == st.session_state["person_doc_id"]:
                st.info("Sie sehen bereits die Daten dieser Person an.")
                st.switch_page("pages/Profil.py")
            else:
                st.session_state["person_doc_id"] = selected_doc_id_from_dropdown
                person_data = db.get(doc_id=selected_doc_id_from_dropdown)
                name = f"{person_data.get('firstname', '')} {person_data.get('lastname', '')}" if person_data else "Unbekannt"
                st.session_state["profile_to_see_name"] = name
                
                # Update the displayed name
                if selected_doc_id_from_dropdown != current_user_doc_id:
                    selected_person_data = db.get(doc_id=selected_doc_id_from_dropdown)
                    #if selected_person_data:
                    #    st.session_state["name"] = selected_person_data.get("firstname", "") + " " + selected_person_data.get("lastname", "")
                else:
                    # Revert to original name if switching back to self
                    original_username = st.session_state.get("username")
                    #if original_username and "USER_CREDENTIALS" in st.session_state and original_username in st.session_state["USER_CREDENTIALS"]:
                    #     st.session_state["name"] = st.session_state["USER_CREDENTIALS"][original_username].get("name", original_username)

                st.success(f"Sie sehen nun die Daten von '{selected_person_display.split(' (ID:')[0]}' an.")

                st.info("Navigieren Sie zum Dashboard oder anderen Seiten, um die aktualisierten Daten zu sehen.")
                st.switch_page("pages/Profil.py")
                st.rerun()

# This is how Streamlit will run the page when it's selected
if __name__ == "__main__":
    person_anschauen_page()