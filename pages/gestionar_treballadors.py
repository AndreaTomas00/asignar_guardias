import streamlit as st
import pandas as pd
import os
from navigation import make_sidebar
import sys
import json
from datetime import datetime, timedelta
sys.path.append("../")  # Add parent directory to path
from utils.worker import Worker  # Import the Worker class
from utils.db import get_db

# Check if user is logged in
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("login.py")

# Set page config
st.set_page_config(
    page_title="Gestionar Treballadors",
    layout="wide"
)

# Add sidebar navigation
make_sidebar()

# Page title
st.title("🧑‍⚕️ Gestionar Treballadors")

# Load section-to-category mapping
def get_section_category_map():
    return {
        "HEMS_tarde": "HEMS",
        "HEMS_festivo": "HEMS",
        "Coordis_diurno": "Coordis", 
        "Coordis_nocturno": "Coordis",
        "Coordis_festivo": "Coordis",
        "UCI_G_lab": "Guardia_UCI",
        "UCI_G_festivo": "Guardia_UCI",
        "UCI_G_nocturno": "Guardia_UCI",
        "Urg_G_diurna": "Guardia_Urg",
        "Urg_G_festivo": "Guardia_Urg",
        "Urg_G_nocturno": "Guardia_Urg",
        "Urg_G_refuerzo_fyf": "Guardia_Urg",
    }

# Helper function to get readable day names
def get_day_name(index_or_name):
    day_names = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge", "festiu"]
    day_indices = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6, "festivo": 7}
    
    if isinstance(index_or_name, int):
        # If it's an integer index
        if 0 <= index_or_name < len(day_names):
            return day_names[index_or_name]
        return "desconegut"
    elif isinstance(index_or_name, str):
        # If it's a string name like "monday"
        return day_names[day_indices.get(index_or_name.lower(), 0)]
    
    return "desconegut"

# Get database manager
db = get_db()

# Get all workers (using the database now)
all_workers = db.get_workers()

# Sort workers alphabetically by name
all_workers.sort(key=lambda worker: worker.name.lower())
# Create tabs for different operations
tab1, tab2, tab3, tab4 = st.tabs(["Veure Treballadors", "Modificar Treballador", "Afegir Treballador", "Eliminar Treballador"])

with tab1:
    
    # Initialize data
    try:
        section_category_map = get_section_category_map()
        all_sections = list(section_category_map.keys())
    except Exception as e:
        st.error(f"Error loading data: {e}")
        section_category_map = {}
        all_sections = []

    # Group sections by category for better organization
    section_categories = {
        "HEMS": [name for name in all_sections if name.startswith("HEMS")],
        "Coordis": [name for name in all_sections if name.startswith("Coordis")],
        "UCI": [name for name in all_sections if name.startswith("UCI")],
        "Urgencias": [name for name in all_sections if name.startswith("Urg")],
    }

    # Filter and display workers
    st.subheader("Treballadors")

    filtered_workers = []
    display_data = []  # Initialize display_data as an empty list
    areas = st.multiselect(
        "Filtra per àrees:",
        options=["HEMS", "Coordis", "Guardia_UCI", "Guardia_Urg", "Guardia_Hosp"],
        default=["HEMS", "Coordis", "Guardia_UCI", "Guardia_Urg", "Guardia_Hosp"]
    )
    for worker in all_workers:
        # If showing all workers or if worker can work in any of the selected sections
            # Get assigned days for relevant categories
        assigned_days_info = {}
        relevant_categories = set(section_category_map.values())

        
        # Create row for this worker
        worker_row = {
            "Nom": worker.name,
            "Estat": worker.state if hasattr(worker, 'state') else "Alta",
            "Categoria": worker.category if hasattr(worker, 'category') else "",
        }
            
        # Add areas the worker can work in
        if hasattr(worker, 'areas'):
            worker_row["Àrees"] = ", ".join(worker.areas) if isinstance(worker.areas, list) else ""
        
        if any(area in worker.areas for area in areas if hasattr(worker, 'areas')):    
            display_data.append(worker_row)
    
    # Create and display the DataFrame
    df = pd.DataFrame(display_data)
    # Sort the dataframe alphabetically by name
    # Define a function to style the DataFrame rows based on 'Estat' value
    def highlight_estat(row):
        if row['Estat'] == 'Alta':
            return ['background-color: #defae3'] * len(row)  # Light green for 'Alta'
        elif row['Estat'] == 'Baja':
            return ['background-color: #ffd7dc'] * len(row)  # Light red for 'Baixa'
        else:
            return [''] * len(row)  # Default style for other states
    
    # Apply the styling function and display the dataframe
    styled_df = df.style.apply(highlight_estat, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
        # Export option
    # Create a CSV download button
    csv = df.to_csv(index=False)
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"treballadors_{current_date}.csv"
    
    st.download_button(
        label="📥 Descarregar CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
    )

    # # Information about the workers available
    # st.subheader("Informació dels treballadors")
    # st.info(f"Total de treballadors disponibles: {len(all_workers)}")

    # states = {}
    # for worker in all_workers:
    #     state = worker.state if hasattr(worker, 'state') else "Alta"
    #     states[state] = states.get(state, 0) + 1
    
    # # Count workers by category
    # categories = {}
    # for worker in all_workers:
    #     if hasattr(worker, 'category'):
    #         categories[worker.category] = categories.get(worker.category, 0) + 1
    
    # # Count workers by areas
    # areas_count = {}
    # for worker in all_workers:
    #     if hasattr(worker, 'areas'):
    #         for area in worker.areas:
    #             areas_count[area] = areas_count.get(area, 0) + 1
    
    # # Display statistics
    # col1, col2, col3 = st.columns(3)
    
    # with col1:
    #     st.write("**Estat dels treballadors**")
    #     for state, count in states.items():
    #         st.write(f"- {state}: {count}")
    
    # with col2:
    #     st.write("**Categories**")
    #     for category, count in categories.items():
    #         st.write(f"- {category}: {count}")
    
    # with col3:
    #     st.write("**Àrees**")
    #     for area, count in areas_count.items():
    #         st.write(f"- {area}: {count}")

with tab2:
    st.subheader("Modificar Treballador")
    
    # Select worker to edit
    worker_names = [worker.name for worker in all_workers]
    selected_worker_name = st.selectbox("Selecciona treballador per modificar:", worker_names)
    
    # Find the selected worker
    selected_worker = next((w for w in all_workers if w.name == selected_worker_name), None)
    
    if selected_worker:
        st.write(f"Editant informació per: **{selected_worker_name}**")
        
        # Create form for editing
        with st.form("edit_worker_form"):
            # Basic information
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Nom complet:", selected_worker.name)
                initials = st.text_input("Inicials:", selected_worker.initials if hasattr(selected_worker, 'initials') else "")
                birth_year = st.number_input("Any de naixement:", min_value=1940, max_value=2010, value=selected_worker.birth_year if hasattr(selected_worker, 'birth_year') else 1990)
            
            with col2:
                categories = ["Planta", "Urgencias", "Uci_pediátrica", "Uci_neonatal", "extra"]
                category = st.selectbox("Categoria:", options=categories, index=categories.index(selected_worker.category) if hasattr(selected_worker, 'category') and selected_worker.category in categories else 0)
                states = ["Alta", "Baixa", "Permís", "Reducció"]
                state = st.selectbox("Estat:", options=states, index=states.index(selected_worker.state) if hasattr(selected_worker, 'state') and selected_worker.state in states else 0)
            
            # Areas the worker can work in
            st.subheader("Àrees disponibles")
            available_areas = ["HEMS", "Coordis", "Guardia_UCI", "Guardia_Urg", "Guardia_Hosp"]

            # Get current areas or default to empty list
            current_areas = selected_worker.areas if hasattr(selected_worker, 'areas') else []
            
            areas = st.multiselect(
                "Àrees on pot treballar:",
                options=available_areas,
                default=current_areas
            )
            
            # Days assigned to each area
            st.subheader("Dies assignats per àrea")
            
            days_assigned = {}
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            
            # For each selected area, show day selection
            for area in areas:
                st.write(f"**{area}**")
                # Get current days for this area or default to empty list
                current_days = selected_worker.days_assigned.get(area, []) if hasattr(selected_worker, 'days_assigned') else []
                
                area_days = st.multiselect(
                    f"Dies assignats per {area}:",
                    options=weekdays,
                    default=current_days,
                    format_func=lambda x: get_day_name(x),
                    key=f"days_{area}"
                )
                
                if area_days:  # Only add if days are selected
                    days_assigned[area] = area_days
            
            st.subheader("Dies no disponibles")
            current_ooo_days = []
            if hasattr(selected_worker, 'ooo_days') and selected_worker.ooo_days:
                current_ooo_days = [day.strip() for day in selected_worker.ooo_days.split(",")]
                st.write("Dies d'absència actuals:")
                for date in current_ooo_days:
                    st.write(f"- {date}")

            # Date range selector for adding new OOO days
            st.write("Afegir nou període d'absència:")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Data d'inici", value=None)
            with col2:
                end_date = st.date_input("Data de finalització", value=None)

            # Add a checkbox for single day selection
            single_day = st.checkbox("Només un dia", value=False)

            # Remove existing OOO days
            if current_ooo_days:
                st.write("Eliminar dies d'absència:")
                days_to_remove = st.multiselect(
                    "Selecciona els dies a eliminar:",
                    options=current_ooo_days,
                    format_func=lambda x: x
                )

            # Hours availability
            st.subheader("Disponibilitat d'hores")
            available_work_hours = st.number_input(
                "Hores totals disponibles:",
                min_value=0,
                value=selected_worker.available_work_hours if hasattr(selected_worker, 'available_work_hours') else 1688
            )
            
            available_guard_hours = st.number_input(
                "Hores de guàrdies disponibles:",
                min_value=0,
                value=selected_worker.available_guard_hours if hasattr(selected_worker, 'available_guard_hours') else 499
            )
            
            # Submit button
            submitted = st.form_submit_button("Actualitzar Treballador")
            
            if submitted:
                # Update worker with new information
                selected_worker.name = name
                selected_worker.initials = initials
                selected_worker.birth_year = birth_year
                selected_worker.category = category
                selected_worker.state = state
                selected_worker.areas = ", ".join(selected_worker.areas) if isinstance(selected_worker.areas, list) else ""
                selected_worker.days_assigned = json.dumps(days_assigned)                
                selected_worker.available_work_hours = available_work_hours
                selected_worker.available_guard_hours = available_guard_hours
                if not hasattr(selected_worker, 'ooo_days'):
                    selected_worker.ooo_days = []
                    
                # Remove selected days
                if 'days_to_remove' in locals() and days_to_remove:
                    for day in days_to_remove:
                        if day in selected_worker.ooo_days:
                            selected_worker.ooo_days.remove(day)
                            
                # Add new OOO days
                if start_date and (single_day or end_date):
                    # If only one day is needed
                    if single_day:
                        date_str = start_date.strftime('%Y-%m-%d')
                        if date_str not in selected_worker.ooo_days:
                            selected_worker.ooo_days.append(date_str)
                    else:
                        # Add all days in the range
                        if end_date >= start_date:
                            current_date = start_date
                            while current_date <= end_date:
                                date_str = current_date.strftime('%Y-%m-%d')
                                if date_str not in selected_worker.ooo_days:
                                    selected_worker.ooo_days.append(date_str)
                                current_date = current_date + timedelta(days=1)
                        else:
                            st.error("La data de finalització ha de ser posterior o igual a la data d'inici.")
                
                # Save changes to database
                try:
                    updated_worker = db.update_worker(selected_worker)
                    if updated_worker:
                        st.success(f"Treballador {name} actualitzat amb èxit!")
                        all_workers = db.get_workers()  # Refresh the workers list
                    else:
                        st.error("No s'ha pogut actualitzar el treballador.")
                except Exception as e:
                    st.error(f"Error al actualitzar el treballador: {e}")

    else:
        st.warning("No s'ha seleccionat cap treballador.")

with tab3:
    st.subheader("Afegir Nou Treballador")
    
    # Create form for adding new worker
    with st.form("add_worker_form"):
        st.write("Introdueix les dades del nou treballador:")
        
        # Basic information
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nom complet:")
            initials = st.text_input("Inicials:")
            birth_year = st.number_input("Any de naixement:", min_value=1940, max_value=2010, value=1990)
        
        with col2:
            category = st.selectbox("Categoria:", ["Planta", "Urgencias", "Uci_pediátrica", "Uci_neonatal", "extra"])
            state = st.selectbox("Estat:", ["Alta", "Baixa", "Permís", "Reducció"], index=0)
        
        # Areas the worker can work in
        st.subheader("Àrees disponibles")
        available_areas = ["HEMS", "Coordis", "Guardia_UCI", "Guardia_Urg", "Guardia_Hosp"]
        
        areas = st.multiselect(
            "Àrees on pot treballar:",
            options=available_areas
        )
        
        # Days assigned to each area
        st.subheader("Dies assignats per àrea")
        
        days_assigned = {}
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        # For each selected area, show day selection
        for area in ["HEMS", "Coordis", "Guardia_UCI", "Guardia_Urg"]:
            st.write(f"**{area}**")
            area_days = st.multiselect(
                f"Dies assignats per {area}:",
                options=weekdays,
                format_func=lambda x: get_day_name(x),
                key=f"new_days_{area}"
            )
            
            if area_days:  # Only add if days are selected
                days_assigned[area] = area_days
        
        # Hours availability
        st.subheader("Disponibilitat d'hores")
        available_work_hours = st.number_input(
            "Hores totals disponibles:",
            min_value=0,
            value=1688
        )
        
        available_guard_hours = st.number_input(
            "Hores de guàrdies disponibles:",
            min_value=0,
            value=499
        )
        
        # Submit button
        submitted = st.form_submit_button("Afegir Treballador")
        
        if submitted:
            if not name or not initials:
                st.error("Has d'introduir nom i inicials.")
            else:
                # Create new worker
                new_worker = Worker(
                    name=name,
                    initials=initials,
                    birth_year=birth_year,
                    category=category,
                    state=state,
                    areas=areas,
                    days_assigned=days_assigned,
                    avoid_days=[],  # Empty list for avoid_days
                    section_day_constraints={},  # Empty dict for constraints
                    available_work_hours=available_work_hours,
                    available_guard_hours=available_guard_hours,
                    ooo_days=[]  # Empty list for out-of-office days
                )
                
                # Add to database
                try:
                    created_worker = db.create_worker(new_worker)
                    if created_worker:
                        st.success(f"Treballador {name} afegit amb èxit!")
                        # Refresh the workers list
                        all_workers = db.get_workers()
                        # Clear the form by rerunning the script with empty values
                        st.experimental_rerun()
                    else:
                        st.error("No s'ha pogut afegir el treballador.")
                except Exception as e:
                    st.error(f"Error al crear el treballador: {e}")
                    # Add tab4 for delete worker functionality

with tab4:
    st.subheader("Eliminar Treballador")
    
    # Select worker to delete
    worker_names = [worker.name for worker in all_workers]
    delete_worker_name = st.selectbox("Selecciona treballador per eliminar:", worker_names, key="delete_worker")
    
    # Find the selected worker
    delete_worker = next((w for w in all_workers if w.name == delete_worker_name), None)
    
    if delete_worker:
        st.write(f"Estàs segur que vols eliminar a: **{delete_worker_name}**?")
        
        # Show worker details before deletion
        st.write("Detalls del treballador:")
        st.write(f"- Nom: {delete_worker.name}")
        st.write(f"- Categoria: {delete_worker.category if hasattr(delete_worker, 'category') else 'No especificada'}")
        st.write(f"- Estat: {delete_worker.state if hasattr(delete_worker, 'state') else 'Alta'}")
        
        # Confirmation
        confirm = st.checkbox("Confirmo que vull eliminar aquest treballador", key="confirm_delete")
        
        if st.button("Eliminar Treballador"):
            if confirm:
                try:
                    success = db.delete_worker(delete_worker.name)
                    if success:
                        st.success(f"Treballador {delete_worker_name} eliminat amb èxit!")
                        # Refresh the workers list
                        all_workers = db.get_workers()
                        # Reset the selection
                        st.session_state.pop("delete_worker", None)
                        st.session_state.pop("confirm_delete", None)
                        # Rerun to update the UI
                        st.experimental_rerun()
                    else:
                        st.error("No s'ha pogut eliminar el treballador.")
                except Exception as e:
                    st.error(f"Error al eliminar el treballador: {e}")
            else:
                st.error("Has de confirmar l'eliminació marcant la casella de confirmació.")
    else:
        st.warning("No s'ha seleccionat cap treballador per eliminar.")