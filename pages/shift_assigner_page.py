import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from navigation import make_sidebar
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_db

# Check if user is logged in
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("login.py")

if "stop_assignment" not in st.session_state:
    st.session_state["stop_assignment"] = False

# Initialize database connection
db = get_db()

# Page configuration
st.set_page_config(
    page_title="Assignar Guàrdies",
    layout="wide"
)

# Add sidebar navigation
make_sidebar()

# Page header
st.title("🏥 Assignació de Guàrdies")
st.write("Selecciona els paràmetres per l'assignació de guàrdies i prem el botó per començar el procés.")
username = st.text_input("Nom d'usuari", value="", disabled=False)
# Create a form for input parameters
with st.form("assignment_params"):
    st.subheader("Interval de dates")
    
    # Year selection
    current_year = datetime.now().year
    year = st.selectbox(
        "Any",
        options=list(range(current_year, current_year + 3)),
        index=0
    )
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_month = st.selectbox(
            "Mes inicial",
            options=list(range(1, 13)),
            index=datetime.now().month - 1,
            format_func=lambda x: [
            "Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
            "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"
            ][x - 1]        )
    
    with col2:
        end_month = st.selectbox(
            "Mes final",
            options=list(range(1, 13)),
            index=min(datetime.now().month + 2, 12) - 1,
            format_func=lambda x: [
            "Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
            "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"
            ][x - 1]
        )
    
    # Calculate actual start and end dates based on selections
    start_date = pd.Timestamp(year=year, month=start_month, day=1)
    if end_month == 12:
        end_date = pd.Timestamp(year=year, month=end_month, day=31)
    else:
        end_date = pd.Timestamp(year=year, month=end_month + 1, day=1) - timedelta(days=1)
    
    # Load sections from database
    try:
        sections_data = db.get_sections()
        logger.info(f"Loaded {len(sections_data)} sections from database")

    except Exception as e:
        st.error(f"Error loading sections from database: {e}")
        sections_data = []
    
    sections_to_assign = [section.nombre for section in sections_data]
    
    if not sections_to_assign:
        st.warning("No s'han trobat seccions a la base de dades. Si us plau, creeu algunes seccions primer.")
        sections_to_assign = []

    # Advanced options
    st.subheader("Opcions avançades")
    
    priority_order = st.multiselect(
        "Ordre de prioritat de les seccions",
        options=sections_to_assign,
        default=sections_to_assign[:min(5, len(sections_to_assign))] if sections_to_assign else []
    )
    
    # Run button at the bottom of the form
    submitted = st.form_submit_button("Iniciar assignació de guàrdies", type="primary")
    
# Check if the user wants to stop the assignment
if st.button("Aturar assignació", key="stop_assignment_button"):
    st.session_state["stop_assignment"] = True
    st.warning("Assignació aturada per l'usuari.")

# Process form submission
if submitted:
    if not sections_to_assign:
        st.error("No hi ha seccions disponibles per assignar. Si us plau, creeu algunes seccions primer.")
        st.stop()
        
    st.session_state["stop_assignment"] = False
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Convert priority order into a dictionary with section name as key and order as value
    priority_order_dict = {section: index + 1 for index, section in enumerate(priority_order)}
    
    # Create configuration for the assignment script
    config = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "sections": sections_to_assign,
        "priority_order": priority_order_dict
    }
    
    # Import the shift assignment module
    try:
        from utils.shift_assignment import ShiftAssigner
        from utils.sections import calendario_2026
        
        # Load workers from database
        status_text.text("Carregant treballadors de la base de dades...")
        progress_bar.progress(5)
        
        try:
            workers = db.get_workers()
            logger.info(f"Loaded {len(workers)} workers from database")
        except Exception as e:
            st.error(f"Error loading workers from database: {e}")
            st.stop()
            
        if not workers:
            st.error("No s'han trobat treballadors a la base de dades. Si us plau, afegiu alguns treballadors primer.")
            st.stop()
            
        # Show process status
        status_text.text("Iniciant el procés d'assignació...")
        progress_bar.progress(10)
        
        # Create the shift assigner with your workers, sections, and calendar
        st.info("Creant assignador de guàrdies...")
        assigner = ShiftAssigner(workers, sections_to_assign, priority_order_dict, calendario_2026, st.session_state)
        
        # Extract date range from config
        start_date_str = config["start_date"]
        end_date_str = config["end_date"]
        
        # Convert strings to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        # Update progress
        status_text.text("Configurant assignacions...")
        progress_bar.progress(20)
        
        # Use assign_period_shifts_with_backtracking for just the selected period
        period_name = f"Periode: {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
        
        # Show progress
        status_text.text(f"Assignant guàrdies per a {period_name}...")
        progress_bar.progress(30)
        
        # Perform the assignment
        success = assigner.assign_period_shifts_with_backtracking(start_date, end_date, period_name)
        
        if success:
            # Update progress
            status_text.text("Desant resultats a la base de dades...")
            progress_bar.progress(80)
            
            # Get assignments dataframe
            assignments_df = assigner.assignments
            
            # Get statistics
            metrics_dict = assigner.yearly_metrics
            
            # Save to database
            scenario_name = f"Assignacions {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}"
            try:
                scenario_id = db.save_assignment_scenario(
                    name=scenario_name,
                    created_by=username,
                    year=year,
                    assignments_df=assignments_df,
                    metrics_dict=metrics_dict,
                    description=f"Període: {start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
                    settings=config
                )
                
                if scenario_id:
                    logger.info(f"Saved assignment scenario with ID: {scenario_id}")
                else:
                    st.warning("No s'ha pogut desar l'escenari d'assignació a la base de dades.")
            except Exception as e:
                st.error(f"Error desant l'escenari d'assignació a la base de dades: {e}")
                
            # Show success
            progress_bar.progress(100)
            status_text.text("Assignació completada amb èxit!")
            
            # Show results
            st.success(f"S'han assignat guàrdies amb èxit per al període {period_name}")
            
            # Display the assignments dataframe
            st.subheader("Vista prèvia d'assignacions")
            st.dataframe(assignments_df)
            
            # Create a CSV download button
            csv = assignments_df.to_csv(index=False)
            st.download_button(
                label="Descarregar assignacions (CSV)",
                data=csv,
                file_name=f"assignacions_{start_date.strftime('%Y%m%d')}_a_{end_date.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # Display metrics
            st.subheader("Estadístiques d'assignació")
            
            # Prepare metrics dataframe for display
            metrics_rows = []
            for worker_name, metrics in metrics_dict.items():
                if worker_name not in ('period_stats', 'total_shifts_assigned', 'unassigned_shifts_count'):
                    metrics_rows.append({
                        "Treballador": worker_name,
                        "Total guàrdies": metrics.get('total_shifts', 0),
                        "Total hores": metrics.get('total_hours', 0),
                        "Guàrdies nocturnes": metrics.get('night_shifts', 0),
                        "Guàrdies cap de setmana": metrics.get('weekend_shifts', 0),
                        "Guàrdies festius": metrics.get('festivo_shifts', 0)
                    })
            
            metrics_df = pd.DataFrame(metrics_rows)
            st.dataframe(metrics_df)
            
        else:
            # Assignment failed
            progress_bar.progress(100)
            status_text.text("Error en l'assignació")
            st.error("No s'han pogut assignar totes les guàrdies. Revisa les seccions seleccionades i els treballadors disponibles.")
            
            # Show backtracking log if available
            backtracking_log = assigner.get_backtracking_log()
            if backtracking_log:
                with st.expander("Veure log de backtracking (per a diagnòstic)"):
                    st.code(backtracking_log)
    
    except Exception as e:
        # Handle any exceptions
        progress_bar.progress(100)
        status_text.text("Error inesperat")
        st.error(f"Hi ha hagut un error inesperat: {str(e)}")
        
        # Show traceback for debugging
        import traceback
        with st.expander("Detalls tècnics de l'error"):
            st.code(traceback.format_exc())

# Add a section for viewing past scenarios
st.header("Escenaris d'assignació anteriors")

try:
    # Get all assignment scenarios from database
    scenarios_df = db.get_assignment_scenarios()
    
    if not scenarios_df.empty:
        # Format the created_at column for better display
        if 'created_at' in scenarios_df.columns:
            scenarios_df['created_at'] = pd.to_datetime(scenarios_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Show scenarios table
        st.dataframe(scenarios_df[['id', 'name', 'created_by', 'created_at', 'year', 'status', 'description']], 
                    use_container_width=True)
        
        # Allow user to select a scenario to view
        scenario_options = [f"{row['name']} (ID: {row['id']})" for _, row in scenarios_df.iterrows()]
        selected_scenario = st.selectbox("Selecciona un escenari per veure els detalls:", scenario_options)
        
        if selected_scenario:
            # Extract the scenario ID from the selection
            scenario_id = int(selected_scenario.split("(ID: ")[1].split(")")[0])
            
            # Create tabs for different views
            tab1, tab2 = st.tabs(["Assignacions", "Estadístiques"])
            
            with tab1:
                # Get assignments for the selected scenario
                assignments_df = db.get_assignments(scenario_id)
                if not assignments_df.empty:
                    st.dataframe(assignments_df, use_container_width=True)
                    
                    # Create a CSV download button
                    csv = assignments_df.to_csv(index=False)
                    st.download_button(
                        label="Descarregar assignacions (CSV)",
                        data=csv,
                        file_name=f"assignacions_escenari_{scenario_id}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No hi ha assignacions per a aquest escenari.")
            
            with tab2:
                # Get metrics for the selected scenario
                metrics_df = db.get_assignment_metrics(scenario_id)
                if not metrics_df.empty:
                    # Prepare for display
                    display_metrics = metrics_df[['worker_name', 'total_shifts', 'total_hours', 
                                                 'night_shifts', 'weekend_shifts', 'festivo_shifts']]
                    # Rename columns
                    display_metrics.columns = ['Treballador', 'Total guàrdies', 'Total hores', 
                                              'Guàrdies nocturnes', 'Guàrdies cap de setmana', 'Guàrdies festius']
                    st.dataframe(display_metrics, use_container_width=True)
                else:
                    st.info("No hi ha estadístiques per a aquest escenari.")
    else:
        st.info("No hi ha escenaris d'assignació desats a la base de dades.")
        
except Exception as e:
    st.error(f"Error carregant els escenaris d'assignació: {e}")