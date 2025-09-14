import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx

from pathlib import Path


def get_current_page_name():
    ctx = get_script_run_ctx()

    # we can local info like timezone froom ctx object.
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    page_name = Path(ctx.main_script_path).stem
    # logger.info(f"Current page name: {page_name}")

    return page_name


def make_sidebar():
    with st.sidebar:
        st.title("Assignador de guàrdies 🏥")
        st.write("")
        st.write("")

        if st.session_state.get("logged_in", False):
            pages = {
                "Assignar Guàrdies": "./pages/shift_assigner_page.py",
                "Visualitzar Calendari": "./pages/vis_streamlit.py",
                "Gestionar Treballadors": "./pages/gestionar_treballadors.py",
                "Gestionar Seccions": "./pages/gestionar_seccions.py",
                # "Configuració": "./pages/configuracio.py"
                "Visualitzar Backtracking": "./pages/vis_backtrack.py",
            }

            selected_page = st.selectbox("Canvia la pàgina:", list(pages.keys()), index=None, placeholder="Selecciona una pàgina...")
            if st.button("Tancar sessió"):
                logout()
            if selected_page is not None and selected_page != get_current_page_name():
                st.write("")
                st.switch_page(pages[selected_page])
                
            # # Add application info at the bottom of sidebar
            # st.markdown("---")
            # st.markdown("### Informació")
            # st.markdown("Sistema d'assignació automàtica de guàrdies")
            # st.markdown("v1.0.0 • © 2025")

        elif get_current_page_name() != "login":
            # If anyone tries to access a page without being logged in,
            # redirect them to the login page
            st.switch_page("login.py")

def logout():
    st.session_state.logged_in = False
    st.info("Sessió tancada amb èxit!")
    sleep(0.5)
    st.switch_page("login.py")