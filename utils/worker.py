from datetime import datetime
class Worker:
    def __init__(self, name, initials, birth_year, category, state="Alta", 
                 areas=None, days_assigned=None, avoid_days=None, 
                 section_day_constraints=None, available_work_hours=1688, available_guard_hours=499, ooo_days=[], 
                 jornada_laboral = 100, dias_semana_jornada = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
        """Initialize a worker with their details
        
        Args:
            name (str): Full name of the worker
            initials (str): Initials for short identification
            birth_year (int): Year of birth (for age calculation)
            category (str): Professional category
            state (str): Current state (Alta/Baja)
            areas (list): List of areas the worker can work in
            days_assigned (dict): Dictionary mapping areas to preferred working days
            avoid_days (list): Days to avoid assigning shifts
            section_day_constraints (dict): Dictionary specifying which sections can't be done on specific days
                Format: {'section_name': ['monday', 'tuesday'], 'another_section': ['friday']}
                For sections the worker can't do on specific days
            available_work_hours (int): Available working hours per year
            available_guard_hours (int): Available guard hours per year
            jornada_laboral (int): Percentage of full-time work (e.g., 100 for full-time, 50 for half-time)
            dias_semana_jornada (list): Days of the week the worker is available to work (mornings, doesn't apply to shifts)
        """
        self.name = name
        self.initials = initials
        self.birth_year = birth_year
        self.category = category
        self.state = state
        self.areas = areas if areas else []
        self.days_assigned = days_assigned if days_assigned else {}
        self.avoid_days = avoid_days if avoid_days else []
        self.section_day_constraints = section_day_constraints if section_day_constraints else {}
        self.available_work_hours = available_work_hours
        self.available_guard_hours = available_guard_hours
        self.ooo_days = []
        self.jornada_laboral = jornada_laboral
        self.dias_semana_jornada = dias_semana_jornada
        if ooo_days:
            for day in ooo_days:
                if isinstance(day, str):
                    # Parse date string in format YYYY-MM-DD
                    try:
                        parsed_date = datetime.strptime(day, '%d/%m/%Y').date()
                        self.ooo_days.append(parsed_date)
                    except ValueError:
                        # Skip invalid dates
                        print(f"Warning: Could not parse date '{day}' for worker {name}")
                else:
                    self.ooo_days.append(day)
        
    def is_out_of_office(self, date):
        """Check if worker is out of office (holiday, personal day) on a specific date"""
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                return False
                
        return date in self.ooo_days
    def can_work_in_area(self, area):
        """Check if worker can work in a specific area"""
        return area in self.areas
        
    def can_work_shift(self, area, shift):
        """Check if worker can work a specific shift in an area"""
        return area in self.areas and shift in self.areas[area]["turnos"]
    
    def can_work_on_date(self, date):
        """Check if worker can work on a specific date based on availability"""
        if self.is_out_of_office(date):
            return False
            
        day_name = date.strftime("%A").lower()
        return day_name not in self.avoid_days

    def can_do_section_on_day(self, section_name, date):
        """Check if worker has restrictions for a specific section on this day
        
        Returns:
            bool: True if the worker CAN do the section on this day, False otherwise
        """
        day_name = date.strftime("%A").lower()
        
        # If this section has day constraints
        if section_name in self.section_day_constraints:
            # Return False if this day is in the constraints list
            if day_name in self.section_day_constraints[section_name]:
                return False
        
        return True
        
    def can_work_on_day(self, area, shift, day):
        """Check if worker can work on a specific day for a shift in an area"""
        if not self.can_work_shift(area, shift):
            return False
            
        days_available = self.areas[area]["turnos"][shift].get("dias_disponibles", [])
        
        # Handle the case where days_available is a dictionary with semana_par/semana_impar
        if isinstance(days_available, dict):
            # This would need actual week number logic in a real implementation
            # For now, we'll return True if the day is in either week type
            return (day in days_available.get("semana_par", []) or 
                    day in days_available.get("semana_impar", []))
        else:
            return day in days_available
            
    def get_max_monthly_shifts(self, area, shift, shift_type="turnos_maximos_mensual"):
        """Get the maximum number of shifts per month for a specific area/shift"""
        if not self.can_work_shift(area, shift):
            return 0
            
        return self.areas[area]["turnos"][shift].get(f"{shift_type}_festivos", 
                                                   self.areas[area]["turnos"][shift].get(shift_type, float('inf')))
        
    def __str__(self):
        return f"{self.name} ({self.category})"

