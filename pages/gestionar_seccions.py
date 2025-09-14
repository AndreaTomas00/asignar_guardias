import streamlit as st
import pandas as pd
import sys
import os
import time
from datetime import datetime
import calendar
from datetime import datetime, date, timedelta
import logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Add the parent directory to the path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sections import Section
from navigation import make_sidebar
from utils.db import get_db

# Check if user is logged in
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("login.py")

# Initialize database connection
db = get_db()

make_sidebar()

# Translations for day names
day_translation = {
    "monday": "dilluns",
    "tuesday": "dimarts",
    "wednesday": "dimecres",
    "thursday": "dijous",
    "friday": "divendres",
    "saturday": "dissabte",
    "sunday": "diumenge",
    "festivo": "festiu"
}

day_translation_reverse = {
    "dilluns": "monday",
    "dimarts": "tuesday",
    "dimecres": "wednesday",
    "dijous": "thursday",
    "divendres": "friday",
    "dissabte": "saturday",
    "diumenge": "sunday",
    "festiu": "festivo"
}

# Add this import at the top of your file


# Add this function to create a calendar view
def display_dates_calendar(dates_list, year=None, month=None):
    """
    Display a calendar with highlighted dates from dates_list
    
    Args:
        dates_list: List of date strings in format 'YYYY-MM-DD'
        year: Optional year to display (defaults to current year)
        month: Optional month to display (defaults to current month)
    """
    if not year:
        # Use the year of the first date or current year
        year = int(dates_list[0].split('-')[0]) if dates_list else datetime.now().year
    
    if not month:
        # Use the month of the first date or current month
        month = int(dates_list[0].split('-')[1]) if dates_list else datetime.now().month
    
    # Convert string dates to datetime objects for easier comparison
    highlight_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in dates_list]
    
    # Get month calendar for each month
    all_months = {}
    for m in range(1, 13):
        all_months[m] = calendar.monthcalendar(year, m)
    
    # Create a 3x4 grid for all months
    for row in range(4):
        cols = st.columns(3)
        for col in range(3):
            month_num = row * 3 + col + 1
            if month_num > 12:
                break
                
            with cols[col]:
                # Translate month names to Catalan
                catalan_months = {
                    1: "Gener", 2: "Febrer", 3: "Març", 4: "Abril", 
                    5: "Maig", 6: "Juny", 7: "Juliol", 8: "Agost",
                    9: "Setembre", 10: "Octubre", 11: "Novembre", 12: "Desembre"
                }
                st.markdown(f"#### {catalan_months[month_num]}", unsafe_allow_html=True)
                
                # Create calendar HTML for this month
                cal = all_months[month_num]
                
                html = """
                <style>
                .calendar-small {
                    width: 100%;
                    border-collapse: collapse;
                    text-align: center;
                    font-size: 0.85em;
                }
                .calendar-small th, .calendar-small td {
                    padding: 5px;
                    border: 1px solid #ddd;
                }
                .calendar-small th {
                    background-color: #f0f0f0;
                    font-weight: bold;
                }
                .highlight {
                    background-color: #8fd3e8;
                    color: #000;
                    font-weight: bold;
                }
                .today {
                    border: 2px solid #ff5722;
                }
                .other-month {
                    color: #aaa;
                }
                </style>
                <table class="calendar-small">
                    <tr>
                        <th>Dl</th>
                        <th>Dm</th>
                        <th>Dc</th>
                        <th>Dj</th>
                        <th>Dv</th>
                        <th>Ds</th>
                        <th>Dg</th>
                    </tr>
                """
                
                today = date.today()
                
                # Add calendar rows
                for week in cal:
                    html += "<tr>"
                    for day in week:
                        if day == 0:
                            # Empty cell for days not in this month
                            html += '<td class="other-month"></td>'
                        else:
                            # Create date object for this day
                            current_date = date(year, month_num, day)
                            
                            # Check if this date should be highlighted
                            classes = []
                            if current_date in highlight_dates:
                                classes.append("highlight")
                            if current_date == today:
                                classes.append("today")
                            
                            class_str = f' class="{" ".join(classes)}"' if classes else ''
                            html += f'<td{class_str}>{day}</td>'
                    
                    html += "</tr>"
                
                html += "</table>"
                
                # Display the calendar
                st.markdown(html, unsafe_allow_html=True)
    

def save_section(section, is_new=False):
    """Save changes to a section or add a new one using the database"""
    logger.info("Llega a save_section")
    try:
        if is_new:
            # Check if section already exists
            existing_section = db.get_section(section.nombre)
            if existing_section:
                st.warning("La secció ja existeix. Si voleu modificar-la, feu-ho a la pestanya 'Modificar secció'.")
                return False
            
            # Create new section in database
            result = db.create_section(section)
            if result:
                st.success(f"Nova secció {section.nombre} desada correctament!")
                return True
            else:
                st.error("No s'ha pogut crear la secció.")
                return False
        else:
            logger.info(f"Updating section: {section._to_dict()}")
            # Update existing section in database
            result = db.update_section(section)
            if result:
                return True
            else:
                st.error("No s'ha pogut actualitzar la secció.")
                return False
    except Exception as e:
        st.error(f"Error al desar la secció: {str(e)}")
        return False

def section_to_dict(section):
    """Convert a section object to a dictionary for display"""
    return {
        "Nom": section.nombre,
        "Hores": section.horas_turno,
        "Dies": ", ".join(section.dias),
        "Personal": section.personal if hasattr(section, 'personal') else 1,
        "Lliura": "Sí" if section.libra else "No",
    }

def display_sections(sections_list):
    """Display a table of all sections with filtering options"""
    st.subheader("Seccions existents")
    
    # Create a dataframe from sections
    sections_data = [section_to_dict(section) for section in sections_list]
    df = pd.DataFrame(sections_data)
    
    # Replace day names in English with Catalan
    if not df.empty and "Dies" in df.columns:
        df["Dies"] = df["Dies"].apply(
            lambda x: ", ".join(day_translation.get(d.strip(), d.strip()) for d in x.split(", ")) if isinstance(x, str) else ""
        )
    
    # Display table
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hi ha seccions que coincideixin amb els filtres seleccionats.")

def modify_section(sections_list):
    """Form for modifying an existing section"""
    st.subheader("⚙️ Modificar una secció existent")
    
    # Create a dictionary of section names to objects for easy lookup
    section_dict = {section.nombre: section for section in sections_list}
    
    if not section_dict:
        st.warning("No hi ha seccions disponibles per modificar.")
        return
    
    # Select section to modify
    section_name = st.selectbox(
        "Seleccioneu una secció per modificar",
        options=list(section_dict.keys())
    )
    
    if section_name:
        selected_section = section_dict[section_name]
        # First, show the option to choose between editing details or adding specific dates
        modification_type = st.radio(
            "Què voleu modificar?",
            options=["Editar detalls de la secció", "Afegir dates específiques"],
            horizontal=True
        )
        
        # Based on the selection, show the appropriate form
        if modification_type == "Editar detalls de la secció":
            # FORM FOR EDITING SECTION DETAILS
            with st.form("edit_section_form"):
                st.write("### Editar detalls de la secció")
                
                nombre = st.text_input("Nom", value=selected_section.nombre)
                
                col1, col2 = st.columns(2)
                with col1:
                    horas = st.number_input(
                        "Hores de torn", 
                        value=float(selected_section.horas_turno), 
                        min_value=1.0, 
                        max_value=24.0
                    )
                with col2:
                    personal = st.number_input(
                        "Nombre de treballadors", 
                        value=selected_section.personal if hasattr(selected_section, 'personal') else 1, 
                        min_value=1, 
                        max_value=10
                    )
                
                # Day options in Catalan
                day_options_catalan = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge", "festiu"]
                
                # Get current days in Catalan
                current_days_catalan = [day_translation.get(d, d) for d in selected_section.dias]
                
                dias = st.multiselect(
                    "Dies aplicables",
                    options=day_options_catalan,
                    default=current_days_catalan
                )
                
                # Translate selected days to English for saving
                dias_english = [day_translation_reverse.get(day, day) for day in dias]
                
                libra = st.checkbox("Requereix dia lliure després", value=selected_section.libra)

                submitted = st.form_submit_button("Desar canvis")
                
                if submitted:
                    logger.info("Submitting section modifications")
                    # Update section with new values
                    updated_section = Section(
                        nombre=nombre,
                        dias=dias_english,
                        horas_turno=horas,
                        personal=personal,
                        libra=libra,
                        fechas=selected_section.fechas)
                    
                    # Save changes
                    if save_section(updated_section):
                        st.success(f"Secció {updated_section.nombre} actualitzada correctament!")
                        time.sleep(2)
                        st.rerun()
        
        else:  # "Afegir dates específiques"
            # FORM FOR MANAGING SPECIFIC DATES
            st.write("### Afegir dates específiques")

            date_input_type = st.radio(
                    "Seleccioneu el tipus d'entrada de dates",
                    options=["Període (inici i fi)", "Dates específiques"],         
                    horizontal=True
                )
            if date_input_type == "Període (inici i fi)":
                with st.form("specific_dates_form"):
                    new_dates = []
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input("Data d'inici", value=None)
                    with col2:
                        end_date = st.date_input("Data de fi", value=None)
                    
                    if start_date and end_date:
                        if start_date > end_date:
                            st.error("La data d'inici no pot ser posterior a la data de fi.")
                        else:
                            new_dates = [d.strftime("%Y-%m-%d") for d in pd.date_range(start=start_date, end=end_date)]

                    # Add option to clear all dates
                    clear_dates = st.checkbox("Esborrar totes les dates", value=False)
                    if clear_dates:
                        st.warning("Les dates actuals s'esborraran en desar els canvis.")

                    submitted = st.form_submit_button("Actualitzar dates")
                
                    if submitted and new_dates:
                        if clear_dates:
                            selected_section.fechas = []
                        # Determine the final dates list
                        if hasattr(selected_section, 'fechas') and selected_section.fechas:
                            # Merge existing and new dates, avoiding duplicates
                            all_dates = list(set(selected_section.fechas) | set(new_dates))
                        else:
                            # Only use new dates (either no existing dates or user chose to clear them)
                            all_dates = new_dates
                        
                        # Update section with new dates
                        updated_section = Section(
                            nombre=selected_section.nombre,
                            dias=selected_section.dias,
                            horas_turno=selected_section.horas_turno,
                            personal=selected_section.personal if hasattr(selected_section, 'personal') else 1,
                            libra=selected_section.libra,
                            fechas=all_dates
                        )
                        
                        if save_section(updated_section):
                            st.success(f"Dates actualitzades per a la secció {updated_section.nombre}!")
                            time.sleep(2)
                            st.rerun()

                    elif submitted and not new_dates and 'clear_dates' in locals() and clear_dates:
                        # User only wants to clear dates without adding new ones
                        updated_section = Section(
                            nombre=selected_section.nombre,
                            dias=selected_section.dias,
                            horas_turno=selected_section.horas_turno,
                            personal=selected_section.personal if hasattr(selected_section, 'personal') else 1,
                            libra=selected_section.libra,
                            fechas=[]
                        )
                        
                        if save_section(updated_section):
                            st.success(f"Totes les dates han estat esborrades per a la secció {updated_section.nombre}!")
                            time.sleep(2)
                            st.rerun()

            else:  # "Dates específiques"
                with st.form("Dates_especifiques_form"):
                    specific_dates = st.multiselect(
                        "Seleccioneu dates específiques",
                        options=pd.date_range(start=datetime.now(), periods=365).to_list(),
                        format_func=lambda x: x.strftime("%Y-%m-%d")
                    )
                    new_dates = [d.strftime("%Y-%m-%d") for d in specific_dates]

                    # Show current specific dates if they exist
                    if hasattr(selected_section, 'fechas') and selected_section.fechas:

                        # Add option to clear all dates
                        clear_dates = st.checkbox("Esborrar totes les dates", value=False)
                        if clear_dates:
                            st.warning("Les dates actuals s'esborraran en desar els canvis.")

                    submitted = st.form_submit_button("Actualitzar dates")
                
                    if submitted and new_dates:
                        if clear_dates:
                            selected_section.fechas = []
                        # Determine the final dates list
                        if hasattr(selected_section, 'fechas') and selected_section.fechas:
                            # Merge existing and new dates, avoiding duplicates
                            all_dates = list(set(selected_section.fechas) | set(new_dates))
                        else:
                            # Only use new dates (either no existing dates or user chose to clear them)
                            all_dates = new_dates
                        
                        # Update section with new dates
                        updated_section = Section(
                            nombre=selected_section.nombre,
                            dias=selected_section.dias,
                            horas_turno=selected_section.horas_turno,
                            personal=selected_section.personal if hasattr(selected_section, 'personal') else 1,
                            libra=selected_section.libra,
                            fechas=all_dates
                        )
                        
                        if save_section(updated_section):
                            st.success(f"Dates actualitzades per a la secció {updated_section.nombre}!")
                            time.sleep(2)
                            st.rerun()

                    elif submitted and not new_dates and 'clear_dates' in locals() and clear_dates:
                        # User only wants to clear dates without adding new ones
                        updated_section = Section(
                            nombre=selected_section.nombre,
                            dias=selected_section.dias,
                            horas_turno=selected_section.horas_turno,
                            personal=selected_section.personal if hasattr(selected_section, 'personal') else 1,
                            libra=selected_section.libra,
                            fechas=[]
                        )
                        
                        if save_section(updated_section):
                            st.success(f"Totes les dates han estat esborrades per a la secció {updated_section.nombre}!")
                            time.sleep(2)
                            st.rerun()

                            # Show current specific dates if they exist
            if len(selected_section.fechas) > 1:
                st.write("#### Veure dates actuals ⬇️")
                # Add year selector for the calendar display
                years = sorted(set([int(d.split('-')[0]) for d in selected_section.fechas]))
                current_year = datetime.now().year
                default_year = current_year if current_year in years else years[0] if years else datetime.now().year
                selected_year = st.selectbox(
                    "Seleccioneu any per visualitzar:", 
                    options=years,
                    index=years.index(default_year) if default_year in years else 0,
                    key="calendar_year_display"
                )
                # Display dates in a calendar view
                display_dates_calendar(selected_section.fechas, selected_year)


def add_new_section():
    """Form for adding a new section"""
    st.subheader("➕ Afegir nova secció")
    
    if "has_specific_dates" not in st.session_state:
        st.session_state.has_specific_dates = False
    
    col1, col2 = st.columns(2)
    with col1:
        # Put checkbox OUTSIDE the form
        has_specific_dates = st.checkbox(
            "Té dates específiques?", 
            value=st.session_state.has_specific_dates,
            key="has_specific_dates"
        )
    with col2:
        date_input_type = st.selectbox(
            "Si té dates específiques, seleccioneu el tipus d'entrada de dates",
            options=["Període (inici i fi)", "Dates específiques"]
        )

    with st.form("new_section_form"):
        nombre = st.text_input("Nom")
        col1, col2 = st.columns(2)
        with col1:
            horas = st.number_input("Hores de torn", value=12.0, min_value=1.0, max_value=24.0)
        with col2:  
            personal = st.number_input("Nombre de treballadors", value=1, min_value=1, max_value=10)
        
        # Day type options
        day_options = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge", "festiu"]
        dias = st.multiselect(
            "Dies aplicables",
            options=day_options,
            default=[]
        )
        
        # Translate selected days to English for saving
        dias_english = [day_translation_reverse.get(day, day) for day in dias]
        
        libra = st.checkbox("Requereix dia lliure després", value=False)

        fechas = []
        if has_specific_dates:
            st.write("Seleccioneu dates específiques per a aquesta secció")
            
            if date_input_type == "Període (inici i fi)":
                start_date = st.date_input("Data d'inici")
                end_date = st.date_input("Data de fi")
                
                if start_date and end_date:
                    if start_date > end_date:
                        st.error("La data d'inici no pot ser posterior a la data de fi.")
                    else:
                        fechas = [d.strftime("%Y-%m-%d") for d in pd.date_range(start=start_date, end=end_date)]
            elif date_input_type == "Dates específiques":
                specific_dates = st.multiselect(
                    "Seleccioneu dates específiques",
                    options=pd.date_range(start=datetime.now(), periods=365).to_list(),
                    format_func=lambda x: x.strftime("%Y-%m-%d")
                )
                fechas = [d.strftime("%Y-%m-%d") for d in specific_dates]
        
        submitted = st.form_submit_button("Crear secció")
        
        if submitted:
            if not nombre:
                st.error("El nom de la secció és obligatori.")
                return
                
            try:
                # Create new section
                new_section = Section(
                    nombre=nombre,
                    dias=dias_english,
                    horas_turno=horas,
                    personal=personal,
                    libra=libra,
                    fechas=fechas if has_specific_dates else []
                )
                logger.info(f"Creating new section: {new_section._to_dict()}")
                # Save new section
                if save_section(new_section, is_new=True):
                    st.experimental_rerun()
                    
            except Exception as e:
                st.error(f"Error en crear la secció: {str(e)}")

def delete_section(sections_list):
    """Allow user to delete an existing section"""
    st.subheader("🗑️ Eliminar secció")
    
    # Create a dictionary of section names to objects for easy lookup
    section_dict = {section.nombre: section for section in sections_list}
    
    if not section_dict:
        st.warning("No hi ha seccions disponibles per eliminar.")
        return
    
    # Select section to delete
    section_name = st.selectbox(
        "Seleccioneu una secció per eliminar",
        options=list(section_dict.keys()),
        key="delete_section_select"
    )
    
    if section_name:
        selected_section = section_dict[section_name]
        
        # Show section details
        st.write(f"### Detalls de la secció a eliminar")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nom:** {selected_section.nombre}")
            st.write(f"**Hores de torn:** {selected_section.horas_turno}")
            st.write(f"**Nombre de treballadors:** {selected_section.personal if hasattr(selected_section, 'personal') else 1}")
        
        with col2:
            current_days_catalan = [day_translation.get(d, d) for d in selected_section.dias]
            st.write(f"**Dies aplicables:** {', '.join(current_days_catalan)}")
            st.write(f"**Requereix dia lliure després:** {'Sí' if selected_section.libra else 'No'}")
            
        # Warning and confirmation
        st.warning("⚠️ Aquesta acció no es pot desfer. Totes les dades d'aquesta secció seran eliminades permanentment.")
        
        # Use a form to require explicit submission
        with st.form("delete_section_form"):
            confirm_delete = st.checkbox("Confirmo que vull eliminar aquesta secció", value=False)
            submitted = st.form_submit_button("Eliminar secció")
            
            if submitted:
                if confirm_delete:
                    try:
                        # Delete the section from the database
                        result = db.delete_section(selected_section.nombre)
                        if result:
                            st.success(f"Secció {selected_section.nombre} eliminada amb èxit!")
                            time.sleep(2)  # Give user time to see the message
                            st.rerun()  # Refresh the page
                        else:
                            st.error("No s'ha pogut eliminar la secció.")
                    except Exception as e:
                        st.error(f"Error en eliminar la secció: {str(e)}")
                else:
                    st.error("Has de confirmar l'eliminació marcant la casella.")

def main():
    st.title("🗂️ Gestionar seccions")
    
    # Load all sections from database
    try:
        all_sections = db.get_sections()
    except Exception as e:
        st.error(f"Error al carregar les seccions: {str(e)}")
        all_sections = []
    
    # Create tabs for different functions
    tab1, tab2, tab3, tab4 = st.tabs(["Veure seccions", "Modificar secció", "Afegir nova secció", "Eliminar secció"])
    
    with tab1:
        display_sections(all_sections)
        
    with tab2:
        modify_section(all_sections)
        
    with tab3:
        add_new_section()
    
    with tab4:
        delete_section(all_sections)

if __name__ == "__main__":
    main()