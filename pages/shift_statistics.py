import streamlit as st
import pandas as pd
import altair as alt
from utils.calendar_utils import get_shifts_data

def show_shift_statistics(selected_month, year, month_names):
    """Display statistics about the shifts"""
    st.header(f"Estadístiques de torns per {selected_month} {year}")
    
    # Get the month number from the month name
    selected_month_num = month_names.index(selected_month) + 1
    
    # Get data for the selected month
    df = get_shifts_data(year, selected_month_num)
    
    if not df.empty:
        # Basic statistics
        total_shifts = len(df)
        total_hours = df['hours'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Torns", total_shifts)
        col2.metric("Total d'hores", f"{total_hours:.1f}")
        
        # Shift distribution by type
        st.subheader("Distribució de torns per tipus")
        shift_counts = df['shift_name'].value_counts().reset_index()
        shift_counts.columns = ['Tipus de Torn', 'Quantitat']
        
        # Create a bar chart
        shift_chart = alt.Chart(shift_counts).mark_bar().encode(
            x=alt.X('Tipus de Torn:N', sort='-y'),
            y='Quantitat:Q',
            color='Tipus de Torn:N'
        ).properties(
            width=600
        )
        
        st.altair_chart(shift_chart, use_container_width=True)
        
        # Distribution by day of week
        st.subheader("Torns per dia de la setmana")
        day_order = ["Dilluns", "Dimarts", "Dimecres", "Dijous", "Divendres", "Dissabte", "Diumenge", "Festiu"]
        day_counts = df['weekday'].value_counts().reindex(day_order).fillna(0).reset_index()
        day_counts.columns = ['Dia de la Setmana', 'Quantitat']
        
        # Create a bar chart for days
        day_chart = alt.Chart(day_counts).mark_bar().encode(
            x=alt.X('Dia de la Setmana:N', sort=day_order),
            y='Quantitat:Q',
            color=alt.Color('Dia de la Setmana:N')
        ).properties(
            width=600
        )
        
        st.altair_chart(day_chart, use_container_width=True)
        
        # Hours distribution
        st.subheader("Total d'hores per tipus de torn")
        hours_by_shift = df.groupby('shift_name')['hours'].sum().reset_index()
        hours_by_shift.columns = ['Tipus de Torn', 'Total d\'hores']
        
        hours_chart = alt.Chart(hours_by_shift).mark_bar().encode(
            x=alt.X('Tipus de Torn:N', sort='-y'),
            y='Total d\'hores:Q',
            color='Tipus de Torn:N'
        ).properties(
            width=600
        )
        
        st.altair_chart(hours_chart, use_container_width=True)
    else:
        st.info(f"No s'han trobat torns per {selected_month} {year}")