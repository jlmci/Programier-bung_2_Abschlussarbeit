import streamlit as st
import time


#st.title("Trainingstagebuch")


pg = st.navigation(["pages/home.py","pages/add workout.py", "pages/Test 1.py"], position = "sidebar", expanded=True)
pg.run()