import streamlit as st
from time import sleep
from navigation import make_sidebar

st.set_page_config(
    page_title = "Log in",
    layout = "wide"
)

make_sidebar()


st.write("# Assignador de guàrdies 🏥")
st.write("Inicia sessió")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Log in", type="primary"):
    if username == "pediatria_tauli" and password == "1234":
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/shift_assigner_page.py")
    else:
        st.error("Usuari o contrasenya incorrectes")
