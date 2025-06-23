import streamlit as st
import os
import sys
import inspect
from tinydb import TinyDB, Query

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

from Person.Personenklasse import Person
df = TinyDB('dbperson.json')


#code für sessionstate id
id = "3"

data = df.get(doc_ids=id)
print(data)
firstname_value = data[0]["firstname"]
lastname_value = data[0]["lastname"]
date_of_birth_value = data[0]["date_of_birth"]
picture_path_value = data[0]["picture_path"]
gender_value = data[0]["gender"]
ekg_tests_value = data[0]["ekg_tests"]

Nutzer = Person(id, date_of_birth_value, firstname_value, lastname_value, picture_path_value, gender_value,ekg_tests_value) 


bild, personendaten = st.columns([1,2], gap="small")
with bild:
    st.markdown("<div style='padding-top: 23px; font-size: 32px;'>Personendaten</div>", unsafe_allow_html=True)
    st.image(Nutzer.picture_path)  # Verwende das Bild aus der Person-Instanz
with personendaten:
    st.markdown("<br><br>", unsafe_allow_html=True) # Leerer Platzhalter, um den Abstand zu vergrößern
    st.write("ID:", Nutzer.doc_id)
    st.write("Vorname: ", Nutzer.firstname)
    st.write("Nachname: ", Nutzer.lastname)
    #st.markdown(f"<span style='color:white; font-size:16px;'>id: {id_value}</span>", unsafe_allow_html=True)
    #st.markdown(f"<span style='color:white; font-size:16px;'>id: {birthdate_value}</span>", unsafe_allow_html=True)
    st.write("Geschlecht: ", Nutzer.gender)
    st.write("Geburtsdatum: ", Nutzer.date_of_birth)
    Nutzer.nuter_age()
    st.write("Alter: ", Nutzer.age)

