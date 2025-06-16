import streamlit as st
import time


#st.title("Trainingstagebuch")


pg = st.navigation(["pages/Profil.py", "pages/dashboard.py", "pages/add workout.py", "pages/Test 1.py"], position = "sidebar", expanded=True)
pg.run()