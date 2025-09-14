import streamlit as st
import calendar
import datetime
from utils.calendar_utils import get_shifts_data, draw_month_calendar

def show_monthly_calendar(selected_month, year, month_names):
    """Display the monthly calendar view"""
    st.header(f"Calendari {selected_month} {year}")
    
    # Get the month number from the month name
    selected_month_num = month_names.index(selected_month) + 1
    
    # Get data for the selected month
    df = get_shifts_data(year, selected_month_num)
    
    # Draw the calendar
    draw_month_calendar(df, selected_month, year, month_names)
    
    with st.expander("Detalls del Calendari"):
        st.write("""
        Aquest calendari mostra tots els torns que cal cobrir cada dia:
        - **Torns HEMS**: Només tenen lloc en setmanes específiques (vegeu sections.py)
        - **Torns Coordis**: Només en dates específiques definides al codi
        - **Altres torns**: Segueixen patrons regulars segons el dia de la setmana
        
        Els dies festius estan destacats amb un fons de color rosa.
        """)