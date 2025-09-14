import streamlit as st
import pandas as pd
import logging
import json
from supabase import create_client, Client
from typing import Dict, List, Optional, Any, Union
from utils.worker import Worker  # Import the Worker class
from utils.sections import Section  # Import the Section class

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SupabaseManager:
    """
    Manager class for Supabase database operations.
    Handles connection and CRUD operations for the guardias_pedi application.
    """
    
    def __init__(self):
        """
        Initialize the Supabase client using credentials from .streamlit/secrets.toml
        """
        try:
            # Get connection details from Streamlit secrets
            self.supabase_url = st.secrets["supabase"]["url"]
            self.supabase_key = st.secrets["supabase"]["key"]
            
            # Initialize Supabase client
            self.supabase: Client = create_client(
                self.supabase_url, 
                self.supabase_key
            )
            logger.info("Supabase connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase connection: {str(e)}")
            raise

    # ========== WORKER OPERATIONS ==========
    
    def get_workers(self) -> List[Worker]:
        """
        Retrieve all workers from the database
        
        Returns:
            List of Worker objects
        """
        logger.info("Fetching all workers from database")
        try:
            response = self.supabase.table("Workers").select("*").execute()
            worker_list = []
            logger.info("Hola")
            logger.info(f"Raw worker data: {response.data}")
            for worker_data in response.data:
                # Handle days_assigned JSON field if present
                if 'days_assigned' in worker_data and worker_data['days_assigned'] is not None:
                    if isinstance(worker_data['days_assigned'], str):
                        try:
                            worker_data['days_assigned'] = json.loads(worker_data['days_assigned'])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse days_assigned JSON for worker {worker_data.get('name')}")
                            worker_data['days_assigned'] = {}
                if 'areas' in worker_data:
                    # Convert string areas to list and remove blank/whitespace elements
                    if isinstance(worker_data['areas'], str):
                        worker_data['areas'] = [area.strip() for area in worker_data['areas'].split(",") if area.strip()]

                # Convert database row to Worker object
                worker_list.append(Worker(**worker_data))
                
            logger.info(f"Retrieved {len(worker_list)} workers from database")
            for worker in worker_list:
                logger.info(f"Worker: {worker.name}, Days Assigned: {worker.days_assigned}, Areas: {worker.areas}")
            return worker_list
        except Exception as e:
            logger.error(f"Error fetching workers: {str(e)}")
            return []
    
    def get_worker(self, worker_name: str) -> Optional[Worker]:
        """
        Retrieve a specific worker by name
        
        Args:
            worker_name: The name of the worker to retrieve
            
        Returns:
            Worker object or None if not found
        """
        try:
            response = self.supabase.table("Workers").select("*").eq("name", worker_name).execute()
            if response.data:
                return Worker(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching worker '{worker_name}': {str(e)}")
            return None
    
    def create_worker(self, worker: Worker) -> Optional[Worker]:
        """
        Create a new worker in the database
        
        Args:
            worker: Worker object to create
            
        Returns:
            Updated Worker object or None if failed
        """
        try:
            # Convert Worker object to dictionary
            worker_data = worker.__dict__
            
            # Remove any keys that shouldn't be sent to the database
            if '_id' in worker_data:
                del worker_data['_id']
                
            # Check if worker already exists
            existing = self.get_worker(worker.name)
            if existing:
                logger.warning(f"Worker with name '{worker.name}' already exists")
                return self.update_worker(worker)
                
            response = self.supabase.table("Workers").insert(worker_data).execute()
            logger.info(f"Worker created: {worker.name}")
            
            # Return Worker with updated data
            if response.data:
                return Worker(**response.data[0])
            return worker
        except Exception as e:
            logger.error(f"Error creating worker: {str(e)}")
            raise
    
    def update_worker(self, worker: Worker) -> Optional[Worker]:
        """
        Update an existing worker
        
        Args:
            worker: Worker object with updated data
            
        Returns:
            Updated Worker object or None if failed
        """
        try:
            # Convert Worker object to dictionary
            worker_data = worker.__dict__
            logger.info(f"Updating worker with data: {worker_data}")
            if not worker.name:
                raise ValueError("Worker must have a name to update")
                
            response = self.supabase.table("Workers").update(worker_data).eq("name", worker.name).execute()
            logger.info(f"Worker updated: {worker.name}")
            
            if response.data:
                logger.info(f"Updated worker data: {response.data[0]}")
                return response.data
            return worker
        except Exception as e:
            logger.error(f"Error updating worker: {str(e)}")
            raise
    
    def update_worker(self, worker: Worker) -> Optional[Worker]:
        """
        Update an existing worker
        
        Args:
            worker: Worker object with updated data
            
        Returns:
            Updated Worker object or None if failed
        """
        try:
            # Convert Worker object to dictionary
            worker_data = worker.__dict__.copy()  # Create a copy to avoid modifying the original
            
            # Handle special fields that might need serialization
            if isinstance(worker_data.get('days_assigned'), dict):
                worker_data['days_assigned'] = json.dumps(worker_data['days_assigned'])
            
            if isinstance(worker_data.get('areas'), list):
                # Keep areas as a list for Supabase
                pass
            
            if isinstance(worker_data.get('avoid_days'), list):
                worker_data['avoid_days'] = json.dumps(worker_data['avoid_days'])
                
            if isinstance(worker_data.get('section_day_constraints'), dict):
                worker_data['section_day_constraints'] = json.dumps(worker_data['section_day_constraints'])
                
            if isinstance(worker_data.get('ooo_days'), list):
                worker_data['ooo_days'] = json.dumps(worker_data['ooo_days'])
            
            # Remove any internal attributes that shouldn't be sent to the database
            keys_to_remove = []
            for key in worker_data:
                if key.startswith('_'):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del worker_data[key]
                
            logger.info(f"Updating worker with data: {worker_data}")
            
            if not worker.name:
                raise ValueError("Worker must have a name to update")
                
            # Make sure to use the correct table name (lowercase)
            response = self.supabase.table("Workers").update(worker_data).eq("name", worker.name).execute()
            logger.info(f"Worker updated: {worker.name}, Response: {response}")
            
            if response.data:
                logger.info(f"Updated worker data: {response.data[0]}")
                # Convert the response data back to a Worker object
                return Worker(**response.data[0])
            return worker
        except Exception as e:
            logger.error(f"Error updating worker: {str(e)}")
            raise

    def delete_worker(self, worker_name: str) -> bool:
        """
        Delete a worker from the database
        
        Args:
            worker_name: The name of the worker to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.table("Workers").delete().eq("name", worker_name).execute()
            logger.info(f"Worker deleted: {worker_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting worker '{worker_name}': {str(e)}")
            return False
    
    # ========== SECTION OPERATIONS ==========
    
    def get_sections(self) -> List[Section]:
        """
        Retrieve all sections from the database
        
        Returns:
            List of Section objects
        """
        try:
            response = self.supabase.table("Sections").select("*").execute()
            section_list = []
            for section_data in response.data:
                if 'dias' in section_data and section_data['dias'] is not None and isinstance(section_data['dias'], str):
                    section_data['dias'] = [day.strip() for day in section_data['dias'].split(",") if day.strip()]
                if 'fechas' in section_data and section_data['fechas'] is not None and isinstance(section_data['fechas'], str):
                    section_data['fechas'] = [day.strip() for day in section_data['fechas'].split(",") if day.strip()]

                section_list.append(Section(**section_data))
                
            logger.info(f"Retrieved {len(section_list)} sections from database")
            # Sort sections by name for consistent display
            section_list.sort(key=lambda section: section.nombre)
            return section_list
        except Exception as e:
            logger.error(f"Error fetching sections: {str(e)}")
            return []
    
    def get_section(self, section_nombre: str) -> Optional[Section]:
        """
        Retrieve a specific section by nombre
        
        Args:
            section_nombre: The nombre of the section to retrieve
            
        Returns:
            Section object or None if not found
        """
        try:
            response = self.supabase.table("Sections").select("*").eq("nombre", section_nombre).execute()
            if response.data:
                return Section(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching section '{section_nombre}': {str(e)}")
            return None
    
    def create_section(self, section: Section) -> Optional[Section]:
        """
        Create a new section in the database
        
        Args:
            section: Section object to create
            
        Returns:
            Updated Section object or None if failed
        """
        try:
            # Convert Section object to dictionary
            section_data = section._to_dict()
            
            # Check if section already exists
            existing = self.get_section(section.nombre)
            if existing:
                logger.warning(f"Section with nombre '{section.nombre}' already exists")
                return self.update_section(section)
            
            section_data['dias'] = str(", ".join(section_data['dias']))
            logger.info(f"Serialized dias: {section_data['dias']}")
            logger.info(type(section_data['dias']))
                
            if 'fechas' in section_data and isinstance(section_data['fechas'], list):
                section_data['fechas'] = ", ".join(section_data['fechas'])
            
            response = self.supabase.table("Sections").insert(section_data).execute()
            logger.info(f"Section created: {section.nombre}")
            
            # Return Section with updated data
            if response.data:
                return Section(**response.data[0])
            return section
        except Exception as e:
            logger.error(f"Error creating section: {str(e)}")
            raise
    
    def update_section(self, section: Section) -> Optional[Section]:
        """
        Update an existing section
        
        Args:
            section: Section object with updated data
            
        Returns:
            Updated Section object or None if failed
        """
        try:
            # Convert Section object to dictionary
            section_data = section._to_dict()
            logger.info(f"Updating section with data: {section_data}")
            # Handle special fields that might need serialization
            if 'dias' in section_data and isinstance(section_data['dias'], list):
                logger.info("Entra")
                section_data['dias'] = str(", ".join(section_data['dias']))
                logger.info(f"Serialized dias: {section_data['dias']}")
                logger.info(type(section_data['dias']))
                
            if 'fechas' in section_data and isinstance(section_data['fechas'], list):
                section_data['fechas'] = ", ".join(section_data['fechas'])
            
            if not section.nombre:
                raise ValueError("Section must have a nombre to update")
                
            response = self.supabase.table("Sections").update(section_data).eq("nombre", section.nombre).execute()
            logger.info(f"Section updated: {section.nombre}")
            
            if response.data:
                return Section(**response.data[0])
            return section
        except Exception as e:
            logger.error(f"Error updating section: {str(e)}")
            raise
    
    def delete_section(self, section_nombre: str) -> bool:
        """
        Delete a section from the database
        
        Args:
            section_nombre: The nombre of the section to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.table("Sections").delete().eq("nombre", section_nombre).execute()
            logger.info(f"Section deleted: {section_nombre}")
            return True
        except Exception as e:
            logger.error(f"Error deleting section '{section_nombre}': {str(e)}")
            return False
    
    # ========== SHIFT ASSIGNMENT OPERATIONS ==========
    
    def save_assignment_scenario(self, name: str, created_by: str, year: int, 
                                 assignments_df: pd.DataFrame, metrics_dict: Dict, 
                                 description: str = "", settings: Dict = None) -> Optional[int]:
        """
        Save a complete assignment scenario to the database
        
        Args:
            name: Name of the scenario
            created_by: Username who created the scenario
            year: Year for which assignments were generated
            assignments_df: DataFrame containing all shift assignments
            metrics_dict: Dictionary containing worker metrics
            description: Optional description of the scenario
            settings: Optional dictionary of settings used to generate this scenario
            
        Returns:
            ID of the created scenario or None if failed
        """
        try:
            # Insert the scenario and get its ID
            scenario_data = {
                "name": name,
                "created_by": created_by,
                "year": year,
                "description": description,
                "settings": json.dumps(settings) if settings else None
            }
            
            response = self.supabase.table("assignment_scenarios").insert(scenario_data).execute()
            scenario_id = response.data[0]['id']
            logger.info(f"Created assignment scenario: {name} (ID: {scenario_id})")
            
            # Prepare batch insert data for shift assignments
            assignments_batch = []
            for _, row in assignments_df.iterrows():
                assignment = {
                    "scenario_id": scenario_id,
                    "date": row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date'],
                    "day_of_week": row['day_of_week'],
                    "section_name": row['section_name'],
                    "worker_name": row['worker_name'],
                    "hours": float(row['hours']),
                    "libra": bool(row.get('libra', False)),
                    "is_festivo": bool(row.get('is_festivo', False)),
                    "is_weekend": bool(row.get('is_weekend', False)),
                    "period": row.get('period', None)
                }
                assignments_batch.append(assignment)
            
            # Insert assignments in batches of 1000 (Supabase limit)
            batch_size = 1000
            for i in range(0, len(assignments_batch), batch_size):
                batch = assignments_batch[i:i+batch_size]
                self.supabase.table("shift_assignments").insert(batch).execute()
            
            logger.info(f"Inserted {len(assignments_batch)} shift assignments for scenario {scenario_id}")
            
            # Insert metrics
            metrics_batch = []
            for worker_name, metrics in metrics_dict.items():
                if worker_name not in ('period_stats', 'total_shifts_assigned', 'unassigned_shifts_count'):
                    metric_data = {
                        "scenario_id": scenario_id,
                        "worker_name": worker_name,
                        "total_shifts": metrics.get('total_shifts', 0),
                        "total_hours": metrics.get('total_hours', 0),
                        "night_shifts": metrics.get('night_shifts', 0),
                        "weekend_shifts": metrics.get('weekend_shifts', 0),
                        "festivo_shifts": metrics.get('festivo_shifts', 0),
                        "period": None  # For overall metrics
                    }
                    metrics_batch.append(metric_data)
            
            if metrics_batch:
                self.supabase.table("assignment_metrics").insert(metrics_batch).execute()
                logger.info(f"Inserted metrics for {len(metrics_batch)} workers for scenario {scenario_id}")
            
            return scenario_id
        except Exception as e:
            logger.error(f"Error saving assignment scenario: {str(e)}")
            return None
    
    def get_assignment_scenarios(self) -> pd.DataFrame:
        """
        Get all assignment scenarios
        
        Returns:
            DataFrame containing all scenarios with metadata
        """
        try:
            response = self.supabase.table("assignment_scenarios").select("*").order("created_at", desc=True).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching assignment scenarios: {str(e)}")
            return pd.DataFrame()
    
    def get_assignment_scenario(self, scenario_id: int) -> Optional[Dict]:
        """
        Get a specific assignment scenario by ID
        
        Args:
            scenario_id: ID of the scenario to retrieve
            
        Returns:
            Dictionary containing scenario data or None if not found
        """
        try:
            response = self.supabase.table("assignment_scenarios").select("*").eq("id", scenario_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching assignment scenario {scenario_id}: {str(e)}")
            return None
    
    def get_assignments(self, scenario_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get all shift assignments for a specific scenario
        
        Args:
            scenario_id: ID of the scenario to retrieve assignments for
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            DataFrame containing all assignments for the scenario
        """
        try:
            query = self.supabase.table("shift_assignments").select("*").eq("scenario_id", scenario_id)
            
            if start_date:
                query = query.gte("date", start_date)
            if end_date:
                query = query.lte("date", end_date)
                
            response = query.order("date").execute()
            
            df = pd.DataFrame(response.data)
            
            # Convert date to datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
            return df
        except Exception as e:
            logger.error(f"Error fetching assignments for scenario {scenario_id}: {str(e)}")
            return pd.DataFrame()
    
    def get_worker_assignments(self, scenario_id: int, worker_name: str) -> pd.DataFrame:
        """
        Get all shift assignments for a specific worker in a scenario
        
        Args:
            scenario_id: ID of the scenario
            worker_name: Name of the worker
            
        Returns:
            DataFrame containing worker's assignments
        """
        try:
            response = self.supabase.table("shift_assignments").select("*")\
                .eq("scenario_id", scenario_id)\
                .eq("worker_name", worker_name)\
                .order("date").execute()
                
            df = pd.DataFrame(response.data)
            
            # Convert date to datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
            return df
        except Exception as e:
            logger.error(f"Error fetching assignments for worker {worker_name} in scenario {scenario_id}: {str(e)}")
            return pd.DataFrame()
    
    def get_assignment_metrics(self, scenario_id: int) -> pd.DataFrame:
        """
        Get all metrics for a specific assignment scenario
        
        Args:
            scenario_id: ID of the scenario to retrieve metrics for
            
        Returns:
            DataFrame containing metrics for all workers
        """
        try:
            response = self.supabase.table("assignment_metrics").select("*")\
                .eq("scenario_id", scenario_id).execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            logger.error(f"Error fetching metrics for scenario {scenario_id}: {str(e)}")
            return pd.DataFrame()
    
    def delete_assignment_scenario(self, scenario_id: int) -> bool:
        """
        Delete an assignment scenario and all related assignments and metrics
        
        Args:
            scenario_id: ID of the scenario to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Due to cascade delete, we only need to delete the scenario
            self.supabase.table("assignment_scenarios").delete().eq("id", scenario_id).execute()
            logger.info(f"Deleted assignment scenario {scenario_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting assignment scenario {scenario_id}: {str(e)}")
            return False
    
    def clone_assignment_scenario(self, scenario_id: int, new_name: str) -> Optional[int]:
        """
        Clone an existing assignment scenario with a new name
        
        Args:
            scenario_id: ID of the scenario to clone
            new_name: Name for the new scenario
            
        Returns:
            ID of the new scenario or None if failed
        """
        try:
            # Get original scenario
            original = self.get_assignment_scenario(scenario_id)
            if not original:
                logger.error(f"Scenario {scenario_id} not found for cloning")
                return None
                
            # Get assignments for the original scenario
            assignments_df = self.get_assignments(scenario_id)
            if assignments_df.empty:
                logger.warning(f"No assignments found for scenario {scenario_id}")
                
            # Get metrics for the original scenario
            metrics_df = self.get_assignment_metrics(scenario_id)
            
            # Convert metrics to the dictionary format needed for save_assignment_scenario
            metrics_dict = {}
            for _, row in metrics_df.iterrows():
                worker_name = row['worker_name']
                metrics_dict[worker_name] = {
                    'total_shifts': row['total_shifts'],
                    'total_hours': row['total_hours'],
                    'night_shifts': row['night_shifts'],
                    'weekend_shifts': row['weekend_shifts'],
                    'festivo_shifts': row['festivo_shifts']
                }
                
            # Create new scenario
            new_scenario_id = self.save_assignment_scenario(
                name=new_name,
                created_by=original['created_by'],
                year=original['year'],
                assignments_df=assignments_df,
                metrics_dict=metrics_dict,
                description=f"Cloned from {original['name']} (ID: {scenario_id})",
                settings=json.loads(original['settings']) if original.get('settings') else None
            )
            
            logger.info(f"Cloned scenario {scenario_id} to new scenario {new_scenario_id}")
            return new_scenario_id
        except Exception as e:
            logger.error(f"Error cloning assignment scenario {scenario_id}: {str(e)}")
            return None
    
    def get_assignment_calendar(self, scenario_id: int, month: int, year: int) -> Dict[str, List[Dict]]:
        """
        Get shift assignments organized by day for a specific month and year
        
        Args:
            scenario_id: ID of the scenario
            month: Month (1-12)
            year: Year
            
        Returns:
            Dictionary with dates as keys and lists of assignments as values
        """
        try:
            # Format date range
            start_date = f"{year}-{month:02d}-01"
            # Get the last day of the month
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{month+1:02d}-01"
                from datetime import datetime, timedelta
                end_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                
            # Get assignments for this date range
            assignments_df = self.get_assignments(scenario_id, start_date, end_date)
            
            # Organize by date
            calendar_data = {}
            if not assignments_df.empty:
                for date, group in assignments_df.groupby(assignments_df['date'].dt.strftime('%Y-%m-%d')):
                    calendar_data[date] = group.to_dict('records')
                    
            return calendar_data
        except Exception as e:
            logger.error(f"Error fetching assignment calendar for scenario {scenario_id}: {str(e)}")
            return {}
    
    def get_section_assignments(self, scenario_id: int, section_name: str) -> pd.DataFrame:
        """
        Get all assignments for a specific section in a scenario
        
        Args:
            scenario_id: ID of the scenario
            section_name: Name of the section
            
        Returns:
            DataFrame with assignments for the section
        """
        try:
            response = self.supabase.table("shift_assignments").select("*")\
                .eq("scenario_id", scenario_id)\
                .eq("section_name", section_name)\
                .order("date").execute()
                
            df = pd.DataFrame(response.data)
            
            # Convert date to datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
            return df
        except Exception as e:
            logger.error(f"Error fetching assignments for section {section_name} in scenario {scenario_id}: {str(e)}")
            return pd.DataFrame()
    
    def publish_assignment_scenario(self, scenario_id: int) -> bool:
        """
        Publish an assignment scenario (change status from 'draft' to 'published')
        
        Args:
            scenario_id: ID of the scenario to publish
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.table("assignment_scenarios").update({"status": "published"})\
                .eq("id", scenario_id).execute()
            logger.info(f"Published assignment scenario {scenario_id}")
            return True
        except Exception as e:
            logger.error(f"Error publishing assignment scenario {scenario_id}: {str(e)}")
            return False
    
    def archive_assignment_scenario(self, scenario_id: int) -> bool:
        """
        Archive an assignment scenario (change status to 'archived')
        
        Args:
            scenario_id: ID of the scenario to archive
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.table("assignment_scenarios").update({"status": "archived"})\
                .eq("id", scenario_id).execute()
            logger.info(f"Archived assignment scenario {scenario_id}")
            return True
        except Exception as e:
            logger.error(f"Error archiving assignment scenario {scenario_id}: {str(e)}")
            return False
    # ========== UTILITY METHODS ==========
    
    def get_festivos(self, year: Optional[int] = None) -> pd.DataFrame:
        """
        Retrieve holiday/festivo dates
        
        Args:
            year: Optional year filter
            
        Returns:
            DataFrame with festivo dates
        """
        try:
            query = self.supabase.table("festivos").select("*")
            
            if year:
                query = query.like("date", f"{year}%")
                
            response = query.execute()
            df = pd.DataFrame(response.data)
            
            # Convert date column to datetime
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
            return df
        except Exception as e:
            logger.error(f"Error fetching festivos: {str(e)}")
            return pd.DataFrame()
    
    def create_festivo(self, date: str, description: str = "") -> Dict:
        """
        Create a new festivo/holiday
        
        Args:
            date: Date string in YYYY-MM-DD format
            description: Optional description of the holiday
            
        Returns:
            Dictionary of created festivo
        """
        try:
            festivo_data = {"date": date, "description": description}
            response = self.supabase.table("festivos").insert(festivo_data).execute()
            logger.info(f"Festivo created: {date}")
            return response.data[0] if response.data else festivo_data
        except Exception as e:
            logger.error(f"Error creating festivo for {date}: {str(e)}")
            raise
    
    def delete_festivo(self, date: str) -> bool:
        """
        Delete a festivo by date
        
        Args:
            date: Date string in YYYY-MM-DD format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.table("festivos").delete().eq("date", date).execute()
            logger.info(f"Festivo deleted: {date}")
            return True
        except Exception as e:
            logger.error(f"Error deleting festivo {date}: {str(e)}")
            return False

# Create a singleton instance
def get_db():
    """
    Get or create a database manager instance
    
    Returns:
        SupabaseManager instance
    """
    if 'db' not in st.session_state:
        st.session_state.db = SupabaseManager()
    return st.session_state.db