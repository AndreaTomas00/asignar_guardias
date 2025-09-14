import datetime
import calendar
import pandas as pd
from utils.sections import sections, festivos

def get_day_label(date_obj, festivos_list):
    """Converts a date to day label (monday, tuesday, etc.)"""
    if date_obj in festivos_list:
        return "festivo"
    
    weekday = date_obj.weekday()
    day_map = {
        0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
        4: "friday", 5: "saturday", 6: "sunday",
    }
    return day_map[weekday]

def day_matches_section(date_obj, section_obj, festivos_list):
    """
    Returns True if section applies to the given date.
    Critical logic:
    1. Day of week must match section's days or be marked as festivo
    2. If section has specific fechas (dates), the date must be in that list
       (HEMS and Coordis have specific dates they operate)
    """
    day_label = get_day_label(date_obj, festivos_list)
    
    # First check if day matches section's days
    if day_label not in section_obj.dias:
        return False
    
    # Then check if section has specific dates
    if hasattr(section_obj, 'fechas') and section_obj.fechas:
        return date_obj in section_obj.fechas
        
    # If no specific dates defined, it applies to all days matching the weekday
    return True

def get_shifts_data(year, month=None):
    """Get shifts data for visualization"""
    data = []
    
    # If month is specified, only get data for that month
    if month:
        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1)
        else:
            end_date = datetime.date(year, month + 1, 1)
    else:
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year + 1, 1, 1)
    
    current_date = start_date
    while current_date < end_date:
        for sec in sections:
            if day_matches_section(current_date, sec, festivos):
                data.append({
                    "date": current_date,
                    "day": current_date.day,
                    "month": current_date.month,
                    "weekday": get_day_label(current_date, festivos),
                    "shift_name": sec.nombre,
                    "hours": sec.horas_turno,
                    "personnel": sec.personal,
                    "libra": sec.libra,
                    "is_festivo": current_date in festivos
                })
        current_date += datetime.timedelta(days=1)
    
    return pd.DataFrame(data)

def get_shift_color(shift_name):
    """Return color based on shift category"""
    if "HEMS" in shift_name:
        return "#4285F4"  # Blue
    elif "Coordis" in shift_name:
        return "#34A853"  # Green
    elif "UCI" in shift_name:
        return "#FBBC05"  # Yellow/Orange
    elif "Urg" in shift_name:
        return "#EA4335"  # Red
    else:
        return "#9AA0A6"  # Gray

def draw_month_calendar(df_month, month_name, year, month_names):
    """Draw a calendar for a specific month using Streamlit"""
    import streamlit as st
    
    # Calculate the first day of week for this month and the number of days
    if df_month.empty:
        first_day = datetime.date(year, month_names.index(month_name) + 1, 1)
    else:
        first_day = datetime.date(df_month['date'].min().year, df_month['date'].min().month, 1)
    
    first_weekday = first_day.weekday()  # 0 for Monday, 6 for Sunday
    days_in_month = calendar.monthrange(first_day.year, first_day.month)[1]
    
    # Create a 7x6 grid (7 days x max 6 weeks)
    weeks = 6
    
    # Display day headers (Mon, Tue, etc.)
    cols = st.columns(7)
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, col in enumerate(cols):
        col.markdown(f"<div style='text-align: center; font-weight: bold;'>{weekday_names[i]}</div>", unsafe_allow_html=True)
    
    # Create a 2D list to hold all cells
    day_num = 1 - first_weekday
    
    for w in range(weeks):
        cols = st.columns(7)
        for d in range(7):
            current_day = day_num
            day_num += 1
            
            # Skip days outside the month
            if current_day < 1 or current_day > days_in_month:
                cols[d].markdown("<div style='background-color: #eaeaea; border: 1px solid #ddd; padding: 5px; min-height: 80px; border-radius: 5px;'>&nbsp;</div>", unsafe_allow_html=True)
                continue
            
            # Create date object for current day
            day_date = datetime.date(first_day.year, first_day.month, current_day)
            
            # Get shifts for this day
            if df_month.empty:
                day_shifts = pd.DataFrame()
            else:
                day_shifts = df_month[df_month['date'] == day_date]
            
            # Construct cell content with all shifts
            cell_content = f"<div style='text-align: right; font-weight: bold; margin-bottom: 5px;'>{current_day}</div>"
            
            for _, shift in day_shifts.iterrows():
                color = get_shift_color(shift['shift_name'])
                cell_content += f"<div style='background-color: {color}; color: white; padding: 2px 4px; margin: 2px 0; border-radius: 3px; font-size: 0.8em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{shift['shift_name']}</div>"
            
            # Style for the cell
            is_festivo = day_date in festivos
            if is_festivo:
                cell_style = "background-color: #ffcccc; border: 1px solid #ddd; padding: 5px; min-height: 80px; border-radius: 5px;"
            else:
                cell_style = "background-color: #f9f9f9; border: 1px solid #ddd; padding: 5px; min-height: 80px; border-radius: 5px;"
            
            # Render the cell
            cols[d].markdown(f'<div style="{cell_style}">{cell_content}</div>', unsafe_allow_html=True)
            
        # Break if we've displayed all days in the month
        if day_num > days_in_month:
            break

def draw_assignment_calendar(df_month, assignments_df, month_name, year, month_names):
    """Draw a calendar with shift assignments for a specific month"""
    import streamlit as st
    
    # Calculate the first day of week for this month and the number of days
    if df_month.empty:
        first_day = datetime.date(year, month_names.index(month_name) + 1, 1)
    else:
        first_day = datetime.date(df_month['date'].min().year, df_month['date'].min().month, 1)
    
    first_weekday = first_day.weekday()  # 0 for Monday, 6 for Sunday
    days_in_month = calendar.monthrange(first_day.year, first_day.month)[1]
    
    # Create a 7x6 grid (7 days x max 6 weeks)
    weeks = 6
    
    # Display day headers (Mon, Tue, etc.)
    cols = st.columns(7)
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, col in enumerate(cols):
        col.markdown(f"<div style='text-align: center; font-weight: bold;'>{weekday_names[i]}</div>", unsafe_allow_html=True)
    
    # Create a 2D list to hold all cells
    day_num = 1 - first_weekday
    
    for w in range(weeks):
        cols = st.columns(7)
        for d in range(7):
            current_day = day_num
            day_num += 1
            
            # Skip days outside the month
            if current_day < 1 or current_day > days_in_month:
                cols[d].markdown("<div style='background-color: #eaeaea; border: 1px solid #ddd; padding: 5px; min-height: 80px; border-radius: 5px;'>&nbsp;</div>", unsafe_allow_html=True)
                continue
            
            # Create date object for current day
            day_date = datetime.date(first_day.year, first_day.month, current_day)
            
            # Get shifts for this day
            if df_month.empty:
                day_shifts = pd.DataFrame()
            else:
                day_shifts = df_month[df_month['date'] == day_date]
            
            # Get assignments for this day
            if assignments_df.empty:
                day_assignments = pd.DataFrame()
            else:
                day_assignments = assignments_df[assignments_df['date'].dt.date == day_date]
            
            # Construct cell content with the day number
            cell_content = f"<div style='text-align: right; font-weight: bold; margin-bottom: 5px;'>{current_day}</div>"
            
            # Add shifts with assignments
            for _, shift in day_shifts.iterrows():
                color = get_shift_color(shift['shift_name'])
                
                # Check if this shift has been assigned
                assigned_worker = ""
                matching_assignments = day_assignments[day_assignments['section_name'] == shift['shift_name']]
                if not matching_assignments.empty:
                    assigned_worker = f": {matching_assignments.iloc[0]['worker_name']}"
                
                cell_content += f"<div style='background-color: {color}; color: white; padding: 2px 4px; margin: 2px 0; border-radius: 3px; font-size: 0.8em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>{shift['shift_name']}{assigned_worker}</div>"
            
            # Style for the cell
            is_festivo = day_date in festivos
            if is_festivo:
                cell_style = "background-color: #ffcccc; border: 1px solid #ddd; padding: 5px; min-height: 80px; border-radius: 5px;"
            else:
                cell_style = "background-color: #f9f9f9; border: 1px solid #ddd; padding: 5px; min-height: 80px; border-radius: 5px;"
            
            # Render the cell
            cols[d].markdown(f'<div style="{cell_style}">{cell_content}</div>', unsafe_allow_html=True)
            
        # Break if we've displayed all days in the month
        if day_num > days_in_month:
            break