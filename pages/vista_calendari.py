import streamlit as st
import datetime
import calendar
import pandas as pd
from navigation import make_sidebar
from utils.sections import festivos
from pages.monthly_calendar import show_monthly_calendar
from pages.monthly_list import show_monthly_list
from pages.shift_statistics import show_shift_statistics
from pages.assignments import show_assignments

# Check if user is logged in
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("login.py")

# Set page config
st.set_page_config(page_title="Doctor Shift Calendar", layout="wide")

# Add sidebar navigation
make_sidebar()

def main():
    st.title("Doctor Shifts Calendar 2025")
    
    # Sidebar with month selector
    st.sidebar.title("Options")
    view_option = st.sidebar.radio(
        "Select view:", 
        ["Calendari mensual", "Mes - llista", "Estadístiques de les assignmcions", "Assignacions"]
    )
    
    global month_names
    month_names = list(calendar.month_name)[1:]
    selected_month = st.sidebar.selectbox("Select month:", month_names)
    
    year = 2025
    
    # Explanation of shift categories
    with st.sidebar.expander("Shift Categories"):
        st.markdown("""
        - **HEMS** (Blue): Helicopter Emergency Medical Service
        - **Coordis** (Green): Coordination shifts
        - **UCI** (Yellow): Intensive Care Unit
        - **Urgencias** (Red): Emergency Department
        """)
    
    # Route to the appropriate page based on the selection
    if view_option == "Monthly Calendar":
        show_monthly_calendar(selected_month, year, month_names)
    elif view_option == "Monthly List":
        show_monthly_list(selected_month, year, month_names)
    elif view_option == "Shift Statistics":
        show_shift_statistics(selected_month, year, month_names)
    elif view_option == "Assignments":
        show_assignments(selected_month, year, month_names)

if __name__ == "__main__":
    main()