import streamlit as st
from Person.Personenklasse import Person

st.title("Profil")

# hier später person die eingeloggt /ausgewählt ist laden
Nuter = Person.get_by_id(1)  # Beispiel: ID 1 für den eingeloggten Nutzer
print(Nuter.get_full_name())  # Ausgabe des vollständigen Namens


'''Personendaten aus datenbank laden'''


'''
bild, personendaten = st.columns([1,2], gap="small")
with bild:
    st.markdown("<div style='padding-top: 23px; font-size: 32px;'>Personendaten</div>", unsafe_allow_html=True)
    st.image(image)
with personendaten:
    st.markdown("<br><br>", unsafe_allow_html=True) # Leerer Platzhalter, um den Abstand zu vergrößern
    st.write("ID:", person.Person.find_person_data_by_name(st.session_state.current_user)["id"])
    st.write("Vorname: ", person.Person.find_person_data_by_name(st.session_state.current_user)["firstname"])
    st.write("Nachname: ", person.Person.find_person_data_by_name(st.session_state.current_user)["lastname"])
    #st.markdown(f"<span style='color:white; font-size:16px;'>id: {id_value}</span>", unsafe_allow_html=True)
    #st.markdown(f"<span style='color:white; font-size:16px;'>id: {birthdate_value}</span>", unsafe_allow_html=True)
    st.write("Geschlecht: ", person.Person.find_person_data_by_name(st.session_state.current_user)["gender"])
    st.write("Geburtsdatum: ", person.Person.find_person_data_by_name(st.session_state.current_user)["date_of_birth"])
    st.write("Alter: ", person.Person.calc_age(st.session_state.current_user))


#Leistunskurve über mehere Workouts anzeigen
path2 = "data/activities/activity.csv"
df2 = create_power_curve.read_csv(path2)
power_curve_df = create_power_curve.create_power_curve(df2)
fig2 = create_power_curve.plot_power_curve(power_curve_df)
st.plotly_chart(fig2)  # Zeige den Plot in der Streamlit-App an
'''

