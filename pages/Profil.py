
import streamlit as st
import os
import sys
import inspect
from tinydb import TinyDB, Query
from datetime import datetime # Import datetime for age calculation

# --- Path setup (assuming this is correct for your project) ---
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

# --- Import your Person class (ensure it handles 'age' property correctly) ---
# Assuming Person.Personenklasse.Person has a property or method to calculate age
from Person.Personenklasse import Person

# --- Initialize TinyDB ---
db = TinyDB('dbperson.json') # Changed df to db for consistency with TinyDB examples


# --- Streamlit App ---
#st.set_page_config(layout="wide") # Use wide layout for better spacing

# --- Session State for the current user's ID ---
# This is crucial for maintaining the selected user across Streamlit reruns


###ggf wichtig für anderes

st.session_state.current_user_id = str(st.session_state["person_doc_id"])


#if 'current_user_id' not in st.session_state:
#    st.session_state.current_user_id = "2" # Default to user ID "3"
#else:
#    st.session_state.current_user_id = str(st.session_state["person_doc_id"]) # Ensure it's a string

    ###ggf wichtig für anderes

# --- User Selection (Optional: if you want to switch between users) ---
# You can get all doc_ids from your DB to populate a selectbox
#all_user_ids = [str(doc.doc_id) for doc in db.all()]
#selected_id = st.selectbox("Wähle einen Nutzer:", all_user_ids, index=all_user_ids.index(st.session_state.current_user_id))
#st.session_state.current_user_id = selected_id # Update session state

# --- Retrieve User Data ---
# Ensure the ID is converted to int for TinyDB's doc_id
try:
    user_data = db.get(doc_id=int(st.session_state.current_user_id))
    if user_data is None:
        st.error(f"Nutzer mit ID {st.session_state.current_user_id} nicht gefunden.")
        st.stop() # Stop execution if user not found
except ValueError:
    st.error("Ungültige Nutzer-ID. Bitte wähle eine gültige ID.")
    st.stop()


# --- Create Person object (assuming your Person class can handle this) ---
# Note: Your Person class expects 'id', 'date_of_birth', 'firstname', etc.
# We'll pass the retrieved data to it.
# Make sure your Person class has an 'age' property/method, or we'll add it here.
# Assuming 'ekg_tests' can be None or an empty list if not present, handle default
#nutzer_ekg_tests = user_data.get("ekg_tests", [])

Nutzer = Person(
    doc_id=int(st.session_state.current_user_id), # Ensure doc_id is int
    date_of_birth=user_data["date_of_birth"],
    firstname=user_data["firstname"],
    lastname=user_data["lastname"],
    picture_path=user_data.get("picture_path", "data/pictures/default.jpg"), # Default image if not set
    gender=user_data["gender"],
    ekg_test_ids=user_data["ekg_tests"]
)

# Set the age for display
#Nutzer.age = (Nutzer.date_of_birth) # Assign calculated age
# --- Streamlit Layout ---
st.title("Nutzerprofil Bearbeiten")

bild_col, personendaten_col = st.columns([1,2], gap="small")

with bild_col:
    st.markdown("<div style='padding-top: 23px; font-size: 32px;'>Profilbild</div>", unsafe_allow_html=True)
    if Nutzer.picture_path and os.path.exists(Nutzer.picture_path):
        st.image(Nutzer.picture_path, caption="Aktuelles Profilbild", use_container_width=True)
    else:
        st.image("https://via.placeholder.com/150", caption="Kein Bild gefunden", use_container_width=True) # Placeholder for missing image

    st.subheader("Bild hochladen")
    uploaded_file = st.file_uploader("Wählen Sie ein neues Profilbild", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        # Create a directory to save uploaded images if it doesn't exist
        upload_dir = "uploaded_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Define the path to save the new image
        new_picture_path = os.path.join(upload_dir, uploaded_file.name)
        
        # Save the uploaded file
        with open(new_picture_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        #st.success(f"Bild gespeichert unter: {new_picture_path}")
        Nutzer.picture_path = new_picture_path # Update the Person object's picture_path
        #st.image(Nutzer.picture_path, caption="Neues Bild", use_container_width=True)


with personendaten_col:
    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader("Personen-Informationen")

    # Editable fields
    # TinyDB stores IDs as integers, so we display the original string from selectbox
    st.write(f"**ID:** {st.session_state.current_user_id}")
    
    new_firstname = st.text_input("Vorname:", Nutzer.firstname)
    new_lastname = st.text_input("Nachname:", Nutzer.lastname)
    
    # For date_of_birth, using number_input for simplicity as your DB only has year
    new_date_of_birth = st.number_input(
        "Geburtsjahr:",
        min_value=1900,
        max_value=datetime.now().year,
        value=Nutzer.date_of_birth,
        step=1
    )
    
    new_gender = st.selectbox("Geschlecht:", ["male", "female", "other"], index=["male", "female", "other"].index(Nutzer.gender))
    
    # Display calculated age
    current_maximalpuls = Nutzer.max_hr()  # Assuming max_hr() returns the maximum heart rate based on age
    min_puls = 100
    max_puls = 220

    st.write("Alter: ", Nutzer.age)
    #st.write("Maximale Herzfrequenz: ", Nutzer.max_hr())
    slider_value = max(min_puls, min(max_puls, current_maximalpuls))

    new_maximalpuls = st.slider(
        "Maximalpuls:",
        min_value=min_puls,
        max_value=max_puls,
        value=slider_value,
        step=1
    )
    st.write(f"Anzahl Trainings: {len(Nutzer.ekg_test_ids)}")


    # EKG Tests (display as comma-separated string, allow editing)
    # Convert list of ints to string for editing, then back to list of ints
    #ekg_tests_str = ", ".join(map(str, Nutzer.ekg_tests))
    #new_ekg_tests_str = st.text_input("EKG Tests (kommagetrennt):", ekg_tests_str)


    # --- Save Changes Button ---
    if st.button("Änderungen speichern"):
        # Update the database
        try:
            # Convert EKG tests string back to a list of integers
            #new_ekg_tests_list = []
            #if new_ekg_tests_str.strip(): # Only process if string is not empty
            #    new_ekg_tests_list = [int(item.strip()) for item in new_ekg_tests_str.split(',') if item.strip().isdigit()]

            db.update(
                {
                    "firstname": new_firstname,
                    "lastname": new_lastname,
                    "date_of_birth": new_date_of_birth,
                    "gender": new_gender,
                    "picture_path": Nutzer.picture_path, # Use the updated path from file_uploader
                    "maximalpuls": new_maximalpuls,
                    #"ekg_tests": new_ekg_tests_list
                },
                doc_ids=[int(st.session_state.current_user_id)] # Update the specific document
            )
            st.success("Änderungen erfolgreich gespeichert!")
            # Rerun the app to show updated data
            st.rerun()
            #st.experimental_rerun()
        except ValueError as e:
            st.error(f"Fehler beim Speichern der EKG-Tests. Bitte geben Sie nur Zahlen und Kommas ein: {e}")
        except Exception as e:
            st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")