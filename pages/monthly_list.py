import streamlit as st
from utils.calendar_utils import get_shifts_data, get_shift_color
from utils.sections import festivos

def show_monthly_list(selected_month, year, month_names):
    """Display the monthly list view of shifts"""
    st.header(f"Torns {selected_month} {year}")
    
    # Get the month number from the month name
    selected_month_num = month_names.index(selected_month) + 1
    
    # Get data for the selected month
    df = get_shifts_data(year, selected_month_num)
    
    # Group by date to see shifts per day
    if not df.empty:
        dates = sorted(df['date'].unique())
        
        for date in dates:
            day_shifts = df[df['date'] == date]
            weekday = day_shifts.iloc[0]['weekday']
            is_festivo = date in festivos
            
            date_str = date.strftime("%Y-%m-%d")
            if is_festivo:
                st.markdown(f"### 📅 {date_str} - {weekday.capitalize()} (Festivo)")
            else:
                st.markdown(f"### 📅 {date_str} - {weekday.capitalize()}")
            
            # Display shifts for this day
            for _, shift in day_shifts.iterrows():
                if shift['libra']:
                    libra_text = "Requereix temps de descans després"
                else:
                    libra_text = "No es lliura"
                
                st.markdown(
                    f"<div style='background-color: {get_shift_color(shift['shift_name'])}; color: white; padding: 10px; border-radius: 5px;'>"
                    f"<b>{shift['shift_name']}</b>: {shift['hours']} hours, {shift['personnel']} personnel needed. {libra_text}.</div>", 
                    unsafe_allow_html=True
                )
            
            st.markdown("---")
    else:
        st.info(f"No shifts found for {selected_month} {year}")