import datetime
import logging
import pandas as pd
import numpy as np
import os
import json
import random
import streamlit as st
from datetime import datetime as datetime_type
from datetime import timedelta
from datetime import date as datetime_date

from utils.sections import festivos, calendario_2026
from utils.worker import Worker
from utils.sections import Section

from datetime import datetime
from utils.db import get_db

db = get_db()
# Get sections and workers from the database instead of JSON files
all_sections = db.get_sections()
# Get workers from database
workers = db.get_workers()

class ShiftAssigner:
    def __init__(self, workers, sections, priority, calendario, session_state, year=2025,):
        self.workers = workers
        self.sections = [section for section in all_sections if section.nombre in sections]
        self.sections_priority = priority if priority else {
            "HEMS_tarde": 1,
            "Coordis_diurno": 2,
            "Coordis_nocturno": 3,
            "HEMS_festivo": 4,
            "Coordis_festivo_dia": 5,
            "Coordis_festivo_noche": 6,
            "UCI_G_lab": 7,
            "UCI_G_festivo": 8,
            "Urg_G_noche_l": 9,
            "Urg_G_tarde-noche_l": 10,
            "Urg_G_festivo_mañana": 11,
            "Urg_G_festivo_mañana": 12,
            "Urg_G_refuerzo_fyf": 13,
            }
        self.calendario = calendario
        self.year = year
        self.logger = None
        self.session_state = session_state  # Store session_state

        
        # Initialize overall metrics for the entire year
        self.yearly_metrics = {worker.name: {
            'night_shifts': 0,
            'weekend_shifts': 0, 
            'festivo_shifts': 0,
            'total_hours': 0,
            'total_shifts': 0
        } for worker in workers}

        # Create assignment dataframe (will store all shift assignments)
        self.assignments = pd.DataFrame(columns=[
            'date', 'day_of_week', 'section_name', 'worker_name', 
            'hours', 'libra', 'is_festivo', 'is_weekend', 'period'
        ])
        self.setup_logging()  # Setup logging for this run
        self.logger.info("=== ShiftAssigner initialized ===")
        self.logger.info(f"Year: {self.year}")
        self.logger.info(f"Sections: {[section.nombre for section in self.sections]}")
        # self._generate_and_load_historical_data()

        self._init_metrics()        # Add these imports at the top if they're not already there
     

    def _generate_and_load_historical_data(self):
        """Generate historical shift data based on the summary information"""
        csv_path = "data/historical_shifts_2024.csv"

        # Define shift types and their corresponding hours
        shift_types = {
            'UCI_G_lab': 12,
            'UCI_G_festivo': 12,
            'Coordis_diurno': 8,  # Using system naming convention
            'Coordis_nocturno': 10,
            'HEMS_tarde': 7,
            'HEMS_festivo': 12
        }
        
        # Shift counts from provided data
        shift_counts = {
            'Núria Torre': {'UCI_G_lab': 2, 'UCI_G_festivo': 1, 'Coordis_diurno': 1, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 1},
            'Marta Sardà': {'UCI_G_lab': 13, 'UCI_G_festivo': 10, 'Coordis_diurno': 0, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 0},
            'Dani de Luis': {'UCI_G_lab': 15, 'UCI_G_festivo': 4, 'Coordis_diurno': 3, 'Coordis_nocturno': 2, 'HEMS_tarde': 9, 'HEMS_festivo': 5},
            'Anabel Prigent': {'UCI_G_lab': 8, 'UCI_G_festivo': 8, 'Coordis_diurno': 0, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 0},
            'M.M.': {'UCI_G_lab': 3, 'UCI_G_festivo': 5, 'Coordis_diurno': 0, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 0},
            'Irene Baena': {'UCI_G_lab': 15, 'UCI_G_festivo': 10, 'Coordis_diurno': 0, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 0},
            'Adrián Ranera': {'UCI_G_lab': 7, 'UCI_G_festivo': 3, 'Coordis_diurno': 5, 'Coordis_nocturno': 2, 'HEMS_tarde': 6, 'HEMS_festivo': 6},
            'Aurora Eslava': {'UCI_G_lab': 2, 'UCI_G_festivo': 3, 'Coordis_diurno': 2, 'Coordis_nocturno': 2, 'HEMS_tarde': 0, 'HEMS_festivo': 2},
            'Anna Gelman': {'UCI_G_lab': 16, 'UCI_G_festivo': 9, 'Coordis_diurno': 0, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 0},
            'María Coma': {'UCI_G_lab': 7, 'UCI_G_festivo': 4, 'Coordis_diurno': 2, 'Coordis_nocturno': 0, 'HEMS_tarde': 7, 'HEMS_festivo': 3},
            'Lluís Renter': {'UCI_G_lab': 12, 'UCI_G_festivo': 4, 'Coordis_diurno': 2, 'Coordis_nocturno': 2, 'HEMS_tarde': 12, 'HEMS_festivo': 5},
            'María García Besteiro': {'UCI_G_lab': 13, 'UCI_G_festivo': 5, 'Coordis_diurno': 3, 'Coordis_nocturno': 4, 'HEMS_tarde': 8, 'HEMS_festivo': 4},
            'Miguel García': {'UCI_G_lab': 13, 'UCI_G_festivo': 5, 'Coordis_diurno': 3, 'Coordis_nocturno': 1, 'HEMS_tarde': 8, 'HEMS_festivo': 4},
            'Pilar Díez del Corral': {'UCI_G_lab': 12, 'UCI_G_festivo': 4, 'Coordis_diurno': 0, 'Coordis_nocturno': 7, 'HEMS_tarde': 11, 'HEMS_festivo': 8},
            'Sara Gracía Gómez': {'UCI_G_lab': 2, 'UCI_G_festivo': 0, 'Coordis_diurno': 3, 'Coordis_nocturno': 2, 'HEMS_tarde': 6, 'HEMS_festivo': 0},
            'L.C.': {'UCI_G_lab': 4, 'UCI_G_festivo': 2, 'Coordis_diurno': 0, 'Coordis_nocturno': 0, 'HEMS_tarde': 0, 'HEMS_festivo': 0}
        }
        
        # Target date range - Jan 1 to Jun 30, 2024
        start_date = datetime_type(2025, 1, 1)
        end_date = datetime_type(2025, 6, 30)
        date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                        for i in range((end_date - start_date).days + 1)]
        
        # Create records for each shift
        records = []
        
        for worker in shift_counts.keys():
            for shift_type, count in shift_counts[worker].items():
                # Skip if worker didn't do this shift type
                if count == 0:
                    continue
                    
                # Select random dates for this worker's shifts of this type
                worker_dates = random.sample(date_range, min(count, len(date_range)))
                
                for date in worker_dates:
                    records.append({
                        'date': date,
                        'worker_name': worker,  # Using abbreviated names
                        'section_name': shift_type,
                        'hours': shift_types[shift_type]
                    })
        
        # Create DataFrame and save to CSV
        historical_df = pd.DataFrame(records)
        historical_df['date'] = pd.to_datetime(historical_df['date'])
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        historical_df.to_csv(csv_path, index=False)
        
        # Add to assignments
        self.assignments = pd.concat([self.assignments, historical_df])
        self.logger.info(f"Generated {len(historical_df)} historical assignments")
        
    def _init_metrics(self):
        # Initialize yearly metrics for each worker
        self.yearly_metrics = {}
        for worker in self.workers:
            self.yearly_metrics[worker.name] = {
                'total_shifts': 0,
                'total_hours': 0,
                'night_shifts': 0,
                'weekend_shifts': 0,
                'festivo_shifts': 0
            }
        
        # Update metrics from all assignments (including historical)
        for _, row in self.assignments.iterrows():
            worker_name = row['worker_name']
            section_name = row['section_name']
            date = row['date'].date()
            hours = row['hours']
            
            if worker_name in self.yearly_metrics:
                self.yearly_metrics[worker_name]['total_shifts'] += 1
                self.yearly_metrics[worker_name]['total_hours'] += hours
                
                # Count night shifts
                if any(night_type in section_name for night_type in ['nocturno', 'nocturna']):
                    self.yearly_metrics[worker_name]['night_shifts'] += 1
                
                # Count weekend shifts
                if self.is_weekend(date):
                    self.yearly_metrics[worker_name]['weekend_shifts'] += 1
                
                # Count holiday shifts
                if date in festivos:
                    self.yearly_metrics[worker_name]['festivo_shifts'] += 1

    def initialize_availability_matrix(self, start_date, end_date):
        """Create a matrix tracking worker availability for a specific period"""
        # Create date range for the period
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Initialize availability matrix (True = available)
        availability = pd.DataFrame(
            True, 
            index=date_range, 
            columns=[worker.name for worker in self.workers]
        )
        
        # Mark unavailable days due to vacations, training, etc.
        for worker in self.workers:
            # Skip days worker is unavailable (if this data exists)
            if hasattr(worker, 'ooo_days') and worker.ooo_days:
                for day in worker.ooo_days:
                    if day in availability.index:
                        availability.loc[day, worker.name] = False
                        self.logger.info(f"Marking {day} as unavailable for {worker.name} (OOO day)")
            if hasattr(worker, 'avoid_days') and worker.avoid_days:  
                for day in worker.avoid_days:
                    if day in availability.index:
                        availability.loc[day, worker.name] = False
        # Mark days where workers are already assigned shifts (from previous periods)
        for _, row in self.assignments.iterrows():
            date = row['date']
            worker_name = row['worker_name']
            
            # Mark this day as unavailable
            if date in availability.index:
                availability.loc[date, worker_name] = False
            
            # If shift requires time off next day (libra=True), mark that too
            if row['libra'] and date + timedelta(days=1) in availability.index:
                availability.loc[date + timedelta(days=1), worker_name] = False
        
        return availability
    
    def is_night_shift(self, section):
        """Check if a section is considered a night shift"""
        return 'noche' in section.nombre.lower() or 'nocturno' in section.nombre.lower() or section.nombre == "UCI_G_lab"
    
    def is_weekend(self, date):
        """Check if a date is a weekend"""
        return date.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    # Add this function to the ShiftAssigner class
    def get_urgencias_friday_cadence(self):
        """Get all workers who can work in Urgencias, sorted by birth year (youngest first)"""
        urgencias_workers = []
        
        for worker in self.workers:
            if worker.can_work_in_area("Guardia_Urg"):
                urgencias_workers.append(worker)
        
        # Sort workers by birth year in descending order (youngest first)
        # Assuming worker objects have a birth_year attribute
        return sorted(urgencias_workers, key=lambda w: w.birth_year if hasattr(w, 'birth_year') else 0, reverse=True)
    
    def is_first_friday_of_month(self, date):
        """Check if date is the first Friday of its month"""
        return date.weekday() == 4 and date.day <= 7
    
    def count_monthly_shifts(self, worker_name, month, year, section_pattern):
        """Count how many shifts of a specific type a worker has in a month"""
        month_shifts = self.assignments[
            (self.assignments['worker_name'] == worker_name) &
            (pd.DatetimeIndex(self.assignments['date']).month == month) &
            (pd.DatetimeIndex(self.assignments['date']).year == year) &
            (self.assignments['section_name'].str.contains(section_pattern))
        ]
        return len(month_shifts)
    
    def worker_had_weekend_night_shift(self, worker_name, monday_date):
        """Check if worker had a night shift on Saturday or Sunday before this Monday"""
        saturday = monday_date - timedelta(days=2)
        sunday = monday_date - timedelta(days=1)
        
        weekend_shifts = self.assignments[
            (self.assignments['worker_name'] == worker_name) &
            ((self.assignments['date'] == saturday) | (self.assignments['date'] == sunday)) &
            (self.assignments['section_name'].str.contains('nocturno|noche'))
        ]
        return len(weekend_shifts) > 0
    
    def assign_shift(self, date, section, worker, availability, period_metrics, period_name):
        """Assign a worker to a shift and update metrics"""
        # Add to assignments dataframe
        self.assignments = pd.concat([self.assignments, pd.DataFrame([{
            'date': date,
            'day_of_week': date.strftime("%A"),
            'section_name': section.nombre,
            'worker_name': worker.name,
            'hours': section.horas_turno,
            'libra': section.libra,
            'is_festivo': date in festivos,
            'is_weekend': self.is_weekend(date),
            'period': period_name
        }])], ignore_index=True)
        
        # Mark worker as unavailable for this day
        availability.loc[date, worker.name] = False
        
        # If libra=True, mark next day as unavailable too
        if section.libra and date + timedelta(days=1) in availability.index:
            availability.loc[date + timedelta(days=1), worker.name] = False

        # Update period metrics
        period_metrics[worker.name]['total_shifts'] += 1
        period_metrics[worker.name]['total_hours'] += section.horas_turno
        
        if self.is_night_shift(section):
            period_metrics[worker.name]['night_shifts'] += 1
        
        if self.is_weekend(date):
            period_metrics[worker.name]['weekend_shifts'] += 1
            
        if date in festivos:
            period_metrics[worker.name]['festivo_shifts'] += 1
            
        # Update yearly metrics as well
        self.yearly_metrics[worker.name]['total_shifts'] += 1
        self.yearly_metrics[worker.name]['total_hours'] += section.horas_turno
        
        if self.is_night_shift(section):
            self.yearly_metrics[worker.name]['night_shifts'] += 1
        
        if self.is_weekend(date):
            self.yearly_metrics[worker.name]['weekend_shifts'] += 1
            
        if date in festivos:
            self.yearly_metrics[worker.name]['festivo_shifts'] += 1
    
    def get_workload_score(self, worker_name, period_metrics, is_night=False, is_weekend=False, is_festivo=False, yearly_weight=0.3):
        """
        Calculate a worker's current workload score (lower is better)
        This considers both period metrics (primary) and yearly metrics (secondary)
        """
        # Period metrics (more important for short-term fairness)
        p_metrics = period_metrics[worker_name]
        period_score = p_metrics['total_shifts'] * 10 + p_metrics['total_hours']
        
        if is_night:
            period_score += p_metrics['night_shifts'] * 30
        
        if is_weekend:
            period_score += p_metrics['weekend_shifts'] * 20
            
        if is_festivo:
            period_score += p_metrics['festivo_shifts'] * 25
        
        # Yearly metrics (for long-term fairness)
        y_metrics = self.yearly_metrics[worker_name]
        yearly_score = y_metrics['total_shifts'] * 10 + y_metrics['total_hours']
        
        if is_night:
            yearly_score += y_metrics['night_shifts'] * 30
        
        if is_weekend:
            yearly_score += y_metrics['weekend_shifts'] * 20
            
        if is_festivo:
            yearly_score += y_metrics['festivo_shifts'] * 25
        
        # Combined score (weighted)
        return (1 - yearly_weight) * period_score + yearly_weight * yearly_score
    
    def _get_required_category(self, section):
        """Map section to required worker category"""
        # This mapping would need to be customized based on your requirements
        category_mapping = {
            # HEMS sections
            "HEMS_tarde": "HEMS",
            "HEMS_festivo": "HEMS",
            
            # Coordinators sections
            "Coordis_diurno": "Coordis", 
            "Coordis_nocturno": "Coordis",
            "Coordis_festivo_dia": "Coordis",
            "Coordis_festivo_noche": "Coordis",
            
            # UCI sections
            "UCI_G_lab": "Guardia_UCI",
            "UCI_G_festivo": "Guardia_UCI",
            "UCI_G_nocturno": "Guardia_UCI",
            
            # Emergency sections
            "Urg_G_noche_l": "Guardia_Urg",
            "Urg_G_tarde-noche_l": "Guardia_Urg",
            "Urg_G_festivo_mañana": "Guardia_Urg",
            "Urg_G_festivo_noche": "Guardia_Urg",
            "Urg_G_refuerzo_fyf": "Guardia_Urg",
            
            # Hospitalization sections
            "Hosp_G_diurna": "Guardia_Hosp",
            "Hosp_G_festivo": "Guardia_Hosp",
            "Hosp_G_nocturno": "Guardia_Hosp"
            
            # Add other mappings as needed
        }
        
        return category_mapping.get(section.nombre, None)
        
    def assign_period_shifts_with_backtracking(self, start_date, end_date, period_name):
        """Assign shifts for a specific period using backtracking when necessary"""
        primer = True
        weekdays = {0:"monday", 1:"tuesday", 2:"wednesday", 3:"thursday", 4:"friday", 5:"saturday", 6:"sunday"}
        print(f"Assigning shifts for period: {period_name} ({start_date} to {end_date})")

        # Initialize metrics for this period
        period_metrics = {worker.name: {
            'night_shifts': 0,
            'weekend_shifts': 0, 
            'festivo_shifts': 0,
            'total_hours': 0,
            'total_shifts': 0
        } for worker in self.workers}

        # Get all shifts that need to be assigned in this period
        shifts_to_assign = []
        first_friday_reinforcements = []  # Initialize this list for first Friday special cases
        current_date = start_date
        
        # Initialize TWO availability matrices
        # 1. Shift availability matrix (for shift assignments)
        shift_availability = self.initialize_availability_matrix(start_date, end_date)
        self.logger.info(f"Shift availability matrix initialized for period {period_name}")
        
        # 2. Regular work schedule availability matrix (for regular jornada)
        regular_availability = self.initialize_regular_availability_matrix(start_date, end_date)
        self.logger.info(f"Regular availability matrix initialized for period {period_name}")
        
        while current_date <= end_date:
            # Find day type (weekday, weekend, holiday)
            day_type = next((day_type for date, day_type in self.calendario if date == current_date), None)
            if not day_type:
                current_date += timedelta(days=1)
                continue
            
            # Check which sections apply for this day
            for section in self.sections:
                # Check if this section applies to this day type
                if day_type not in section.dias:
                    continue
                # Check if section has specific dates and this date is not one of them
                if hasattr(section, 'fechas') and section.fechas and len(section.fechas) > 0:
                    # Only continue with sections that have specific dates when the current date is in those dates
                    if str(current_date) not in section.fechas:
                        continue
                if current_date.weekday() == 4 and self.is_first_friday_of_month(current_date):
                    # Find the reinforcement section
                    refuerzo_section = next((s for s in all_sections if s.nombre == "Urg_G_refuerzo_fyf"), None)
                    if refuerzo_section:
                        first_friday_reinforcements.append((current_date, refuerzo_section))
                        self.logger.info(f"Added reinforcement shift for first Friday on {current_date}")
                # This shift needs to be assigned
                shifts_to_assign.append((current_date, section))
                    
            current_date += timedelta(days=1)
        for shift in first_friday_reinforcements:
            shifts_to_assign.append(shift)
        
        # Log the shifts we need to assign
        self.logger.info(f"Need to assign {len(shifts_to_assign)} shifts in this period")
        shifts_to_assign.sort(key=lambda x: (
            self.sections_priority.get(x[1].nombre, 99),  # First sort by section priority
            x[0]                                    # Then sort by date
        ))

        regular_shifts = []
        urg_lab = []  # For Urgencias lab shifts
        urg_weekend_shifts = {}  # Organize by month/weekend
        
        for shift_date, section in shifts_to_assign:
            is_urg_weekend = (
                "Urg_G" in section.nombre and 
                (shift_date.weekday() >= 4 or shift_date in festivos)  # Friday-Sunday or holiday
            )
            if is_urg_weekend:
                # Group by weekend start date (Friday) to keep weekends together
                # For Friday: use the same date
                # For Saturday: use the previous day (Friday)
                # For Sunday: use Friday (2 days back)
                # For holidays on weekdays: use the date itself
                if shift_date.weekday() == 4:  # Friday
                    weekend_key = shift_date
                elif shift_date.weekday() == 5:  # Saturday
                    weekend_key = shift_date - timedelta(days=1)  # Previous Friday
                elif shift_date.weekday() == 6:  # Sunday
                    weekend_key = shift_date - timedelta(days=2)  # Previous Friday
                else:
                    # Holiday on weekday - use the date itself
                    weekend_key = shift_date
                
                if weekend_key not in urg_weekend_shifts:
                    urg_weekend_shifts[weekend_key] = []
                
                urg_weekend_shifts[weekend_key].append((shift_date, section))
            elif section.nombre == "Urg_G_noche_l":
                urg_lab.append((shift_date, section))
            else:
                # Regular shifts go into the main list
                regular_shifts.append((shift_date, section))
        shifts_to_assign = regular_shifts

        # Create a backup of the current assignments for rollback if needed
        original_assignments = self.assignments.copy()
        
        # Set for keeping track of assignments we've tried
        tried_combinations = set()
        
        # Stack for backtracking
        assignment_stack = []
        current_shift_index = 0
        current_assignments_key = tuple()  # Initialize as empty tuple
        first_ass = True
        self.logger.info("Starting backtracking assignment process with regular shifts")

        while current_shift_index < len(shifts_to_assign):
            if self.session_state.get("stop_assignment", False):
                self.logger.info("Assignment process stopped by user")
                return False
            if current_shift_index < 0:
                self.logger.info("FAILED: Backtracking failed - no solution found")
                print("Backtracking failed - no solution found")
                # Reset assignments to original state if we can't find a solution
                self.assignments = original_assignments
                return False
                
            date, section = shifts_to_assign[current_shift_index]
            self.logger.info(f"Processing shift {current_shift_index+1}/{len(shifts_to_assign)}: {date.strftime('%Y-%m-%d')} ({weekdays[date.weekday()]}) {section.nombre}")

            # Find eligible workers for this shift
            eligible_workers = []

            for worker in self.workers:
                # Check if worker is available on this date and can work in this section
                if (worker.name in shift_availability.columns and 
                    shift_availability.loc[date, worker.name] and worker.state == "Alta" and
                    worker.can_work_in_area(self._get_required_category(section))):
                    
                    # Check if this is a weekday (Monday-Thursday) that needs special handling
                    weekday = date.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday
                    weekday_name = weekdays[weekday]
                    # For Monday-Thursday, check if this worker has this day assigned to this section
                    is_eligible = True
                    if 0 <= weekday <= 3 and section.nombre in ["UCI_G_lab", "Coordis_nocturno", "Coordis_diurno", "HEMS_tarde", "Urg_G_noche_l"]:  # Monday to Thursday
                        if hasattr(worker, 'days_assigned') and worker.days_assigned:
                            section_days = worker.days_assigned.get(self._get_required_category(section), [])
                            # If worker has specific days assigned for this section but today is not one of them
                            if weekday_name not in section_days:
                                is_eligible = False
                                self.logger.info(f"  - {worker.name} not eligible: day {weekday_name} not in assigned days for {section.nombre}")
                        if len(worker.days_assigned)==0:
                            is_eligible = False
                            self.logger.info(f"  - {worker.name} not eligible: doesn't have a day assigned from Monday to Thursday")
                    
                    # NEW: Check minimum staffing requirement for regular shifts
                    if is_eligible and self.is_regular_shift(section) and 0 <= weekday <= 3:
                        if not self.check_minimum_staffing(worker, date, regular_availability):
                            is_eligible = False
                            self.logger.info(f"  - {worker.name} not eligible: insufficient staffing would remain in department")
                    
                    if is_eligible:
                        # Check if we've already tried this worker for this shift
                        potential_combination = current_assignments_key + ((date.isoformat(), section.nombre, worker.name),)
                        if potential_combination not in tried_combinations:
                            eligible_workers.append(worker)
                        else:
                            self.logger.info(f"  - {worker.name} already tried for this shift with this combination")

                        self.log_backtracking("eligible", date, section, eligible_workers)

            # No eligible workers for this shift - need to backtrack
            if not eligible_workers:
                # CRITICAL FIX: Check if this shift is fundamentally impossible
                # (i.e., no worker can EVER do this shift regardless of availability)
                weekday = date.weekday()
                weekday_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][weekday]
                
                fundamentally_possible = False
                for worker in self.workers:
                    if (worker.state == "Alta" and
                        worker.can_work_in_area(self._get_required_category(section))):
                        
                        # Check weekday eligibility for Monday-Thursday
                        if 0 <= weekday <= 3:  # Monday to Thursday
                            if hasattr(worker, 'days_assigned') and worker.days_assigned:
                                section_days = worker.days_assigned.get(self._get_required_category(section), [])
                                if weekday_name in section_days:
                                    fundamentally_possible = True
                                    break
                        else:
                            # For weekends/holidays, if worker can work in area, it's possible
                            fundamentally_possible = True
                            break
                
                if not fundamentally_possible:
                    if self.logger:
                        self.logger.error(f"FUNDAMENTAL ERROR: No worker can EVER work {section.nombre} on {weekday_name}s")
                        self.logger.error(f"This is a configuration problem - please assign at least one worker to {weekday_name} for {self._get_required_category(section)}")
                    print(f"CONFIGURATION ERROR: No worker assigned to work {section.nombre} on {weekday_name}s")
                    print(f"Please check worker day assignments for {self._get_required_category(section)}")
                    return False
                
                # Mark all possible assignments for this shift as tried
                for worker in self.workers:
                    current_assignments_key = tuple((d.isoformat(), s.nombre, w.name) for d, s, w, _, _ in assignment_stack)
                    tried_combinations.add(current_assignments_key + ((date.isoformat(), section.nombre, worker.name),))
                    
                # Undo the last assignment
                if assignment_stack:
                    prev_date, prev_section, prev_worker, prev_shift_availability, prev_regular_availability = assignment_stack.pop()
                    current_assignments_key = tuple((d.isoformat(), s.nombre, w.name) for d, s, w, _, _ in assignment_stack)
                    self.log_backtracking("backtrack", prev_date, prev_section, prev_worker)

                    # Reset availability to previous state
                    shift_availability = prev_shift_availability.copy()
                    regular_availability = prev_regular_availability.copy()
                    
                    # Remove the previous assignment from the dataframe
                    self.assignments = self.assignments[
                        ~((self.assignments['date'] == prev_date) & 
                        (self.assignments['section_name'] == prev_section.nombre))
                    ]
                    
                    # Update metrics
                    if self.is_night_shift(prev_section):
                        self.yearly_metrics[prev_worker.name]['night_shifts'] -= 1
                        period_metrics[prev_worker.name]['night_shifts'] -= 1
                        
                    if self.is_weekend(prev_date):
                        self.yearly_metrics[prev_worker.name]['weekend_shifts'] -= 1
                        period_metrics[prev_worker.name]['weekend_shifts'] -= 1
                    
                    if prev_date in festivos:
                        self.yearly_metrics[prev_worker.name]['festivo_shifts'] -= 1
                        period_metrics[prev_worker.name]['festivo_shifts'] -= 1
                    
                    self.yearly_metrics[prev_worker.name]['total_hours'] -= prev_section.horas_turno
                    self.yearly_metrics[prev_worker.name]['total_shifts'] -= 1
                    period_metrics[prev_worker.name]['total_hours'] -= prev_section.horas_turno
                    period_metrics[prev_worker.name]['total_shifts'] -= 1
                    
                    # Go back to previous shift
                    current_shift_index -= 1
                else:
                    # If no assignments to undo, we've tried all possibilities
                    self.logger.info("FAILED: No solution found - backtracking exhausted")
                    print("No solution found - backtracking exhausted")
                    self.assignments = original_assignments
                    return False
                    
                continue
            
            # Find the best worker for this shift
            best_worker = self.find_best_worker_for_shift(
                eligible_workers, date, section, period_metrics
            )
            self.log_backtracking("attempt", date, section, best_worker)

            # Save current availability for backtracking
            prev_shift_availability = shift_availability.copy()
            prev_regular_availability = regular_availability.copy()
            
            # Assign the shift
            self.assign_shift_with_dual_availability(date, section, best_worker, shift_availability, regular_availability, period_metrics, period_name)
            self.log_backtracking("assign", date, section, best_worker)

            # Mark this assignment as tried
            current_assignments_key = tuple((d.isoformat(), s.nombre, w.name) for d, s, w, _, _ in assignment_stack)
            tried_combinations.add(current_assignments_key + ((date.isoformat(), section.nombre, best_worker.name),))

            # Save this assignment for potential backtracking
            assignment_stack.append((date, section, best_worker, prev_shift_availability, prev_regular_availability))
            current_assignments_key = tuple((d.isoformat(), s.nombre, w.name) for d, s, w, _, _ in assignment_stack)
            # Move to next shift
            current_shift_index += 1

            with open("tried_combinations.json", "w") as f:
                json.dump(list(tried_combinations), f, indent=2)

        self.logger.info("SUCCESS: Successfully assigned all regular shifts")
        # Replace the current Urgencias weekend assignment section with this:
        
        self.logger.info("Starting Urgencias weekend shifts assignment")
        
        # Get workers eligible for Urgencias shifts
        urg_workers = [w for w in self.workers if w.can_work_in_area("Guardia_Urg")]
        
        # Sort workers consistently
        urg_workers.sort(key=lambda w: w.name)
        
        # Process each weekend (now keyed by weekend start date)
        for weekend_key, shifts in urg_weekend_shifts.items():
            # Use the weekend key (Friday date) for rotation calculation
            weekend_start_month = weekend_key.month
            
            # Use the weekend start month for rotation calculation
            rotation_offset = (weekend_start_month - 1) % 3
            
            self.logger.info(f"Weekend starting {weekend_key.strftime('%Y-%m-%d')} uses rotation for month {weekend_start_month} (offset={rotation_offset})")
            
            # HANDLE FIRST FRIDAYS ONCE, BEFORE ROLE ASSIGNMENTS
            assigned_shifts = set()
            
            # Check if this weekend contains a first Friday
            for shift_date, section in shifts:
                if self.is_first_friday_of_month(shift_date):
                    self.logger.info(f"First Friday of the month detected on {shift_date.strftime('%Y-%m-%d')}")
                    
                    # Assign Friday shift to Violeta Fariña
                    if section.nombre == "Urg_G_tarde-noche_l":
                        violeta = next((w for w in urg_workers if w.name == "Violeta Fariña"), None)
                        if violeta:
                            self.assign_shift_with_dual_availability(shift_date, section, violeta, shift_availability, regular_availability, period_metrics, period_name)
                            self.logger.info(f"Assigned Violeta Fariña to Friday shift {section.nombre} on {shift_date.strftime('%Y-%m-%d')}")
                            
                            # Mark as assigned
                            assigned_shifts.add((shift_date.isoformat(), section.nombre))
                            
                            # Also handle Sunday morning for Violeta
                            sunday_date = shift_date + timedelta(days=2)
                            for sec in self.sections:
                                if sec.nombre == "Urg_G_festivo_mañana":
                                    sunday_morning_section = sec
                                    self.assign_shift_with_dual_availability(sunday_date, sunday_morning_section, violeta, shift_availability, regular_availability, period_metrics, period_name)
                                    self.logger.info(f"Assigned Violeta Fariña to Sunday morning shift on {sunday_date.strftime('%Y-%m-%d')}")
                                    
                                    # Mark Sunday as assigned
                                    assigned_shifts.add((sunday_date.isoformat(), sunday_morning_section.nombre))
                                    break
                    
                    # Handle reinforcement shift for first Friday weekend
                    elif section.nombre == "Urg_G_refuerzo_fyf":
                        saturday_date = shift_date + timedelta(days=1)  # Saturday after first Friday
                        eligible_workers = [
                            w for w in urg_workers
                            if w.name != "Violeta Fariña" and  # Exclude Violeta
                            w.name in shift_availability.columns and 
                            shift_availability.loc[saturday_date, w.name] and 
                            w.state == "Alta"
                        ]
                        if eligible_workers:
                            best_worker = self.find_best_worker_for_shift(eligible_workers, saturday_date, section, period_metrics)
                            self.assign_shift_with_dual_availability(saturday_date, section, best_worker, shift_availability, regular_availability, period_metrics, period_name)
                            self.logger.info(f"Assigned {best_worker.name} to refuerzo shift on {saturday_date.strftime('%Y-%m-%d')}")
                            
                            # Mark as assigned
                            assigned_shifts.add((saturday_date.isoformat(), section.nombre))
            
            # Group shifts by type (excluding already assigned ones)
            friday_shifts = []
            saturday_morning_shifts = []
            saturday_night_shifts = []
            sunday_morning_shifts = []
            sunday_night_shifts = []
            refuerzo = []
            
            for shift_date, section in shifts:
                # Skip if already assigned in first Friday handling
                if (shift_date.isoformat(), section.nombre) in assigned_shifts:
                    continue
                    
                day_of_week = shift_date.weekday()
                
                if day_of_week == 4:  # Friday
                    friday_shifts.append((shift_date, section))
                elif day_of_week == 5:  # Saturday
                    if "mañana" in section.nombre:
                        saturday_morning_shifts.append((shift_date, section))
                    elif "refuerzo" in section.nombre:
                        refuerzo.append((shift_date, section))
                    elif "noche" in section.nombre:
                        saturday_night_shifts.append((shift_date, section))
                elif day_of_week == 6 or shift_date in festivos:  # Sunday or holiday
                    if "mañana" in section.nombre:
                        sunday_morning_shifts.append((shift_date, section))
                    elif "noche" in section.nombre:
                        sunday_night_shifts.append((shift_date, section))
                    elif "refuerzo" in section.nombre:
                        refuerzo.append((shift_date, section))
            
            # NOW assign workers according to roles using the WEEKEND-CONSISTENT rotation
            self._assign_role_shifts(
                0, rotation_offset, urg_workers, 
                friday_shifts + sunday_morning_shifts, 
                shift_availability, period_metrics, period_name, assigned_shifts
            )
    
            self._assign_role_shifts(
                1, rotation_offset, urg_workers, 
                saturday_morning_shifts + sunday_night_shifts, 
                shift_availability, period_metrics, period_name, assigned_shifts
            )
    
            self._assign_role_shifts(
                2, rotation_offset, urg_workers, 
                saturday_night_shifts, 
                shift_availability, period_metrics, period_name, assigned_shifts
            )
            
            # Assign remaining reinforcement shifts
            for shift_date, section in refuerzo:
                if (shift_date.isoformat(), section.nombre) not in assigned_shifts:
                        eligible_workers = [
                            w for w in self.workers
                            if w.name in shift_availability.columns and
                            shift_availability.loc[shift_date, w.name] and w.can_work_in_area("Guardia_Urg") and
                            w.state == "Alta"
                        ]
                        if eligible_workers:
                            best_worker = self.find_best_worker_for_shift(eligible_workers, shift_date, section, period_metrics)
                            self.assign_shift_with_dual_availability(shift_date, section, best_worker, shift_availability, regular_availability, period_metrics, period_name)
                            self.logger.info(f"Assigned {best_worker.name} to reinforcement shift {section.nombre} on {shift_date.strftime('%Y-%m-%d')}")
        self.logger.info("Urgencias weekend shifts assignment completed")
        self.logger.info("Starting Urgencias lab shifts assignment")
        urg_shift_index = 0
        while urg_shift_index < len(urg_lab):
            if st.session_state.get("stop_assignment", False):
                self.logger.info("Assignment process stopped by user")
                st.warning("Assignació aturada per l'usuari.")
                return False
            date, section = urg_lab[urg_shift_index]
            self.logger.info(f"Processing Urgencias lab shift {urg_shift_index+1}/{len(urg_lab)}: {date.strftime('%Y-%m-%d')} ({weekdays[date.weekday()]}) {section.nombre}")
            
            # Initialize eligible workers list for this shift
            eligible_workers = []
            
            for worker in self.workers:
                # Check if worker is available on this date and can work in this section
                if (worker.name in shift_availability.columns and 
                    shift_availability.loc[date, worker.name] and worker.state == "Alta" and
                    worker.can_work_in_area(self._get_required_category(section))):
                    
                    # Check if this is a weekday (Monday-Thursday) that needs special handling
                    weekday = date.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday
                    weekday_name = weekdays[weekday]
                    # For Monday-Thursday, check if this worker has this day assigned to this section
                    is_eligible = True
                    if 0 <= weekday <= 3:  # Monday to Thursday
                        if hasattr(worker, 'days_assigned') and worker.days_assigned:
                            section_days = worker.days_assigned.get(self._get_required_category(section), [])
                            # If worker has specific days assigned for this section but today is not one of them
                            if weekday_name not in section_days:
                                is_eligible = False
                                self.logger.info(f"  - {worker.name} not eligible: day {weekday_name} not in assigned days for {section.nombre}")
                        if len(worker.days_assigned)==0:
                            is_eligible = False
                            self.logger.info(f"  - {worker.name} not eligible: doesn't have a day assigned from Monday to Thursday")
                    
                    if is_eligible:
                        # Check if we've already tried this worker for this shift
                        potential_combination = current_assignments_key + ((date.isoformat(), section.nombre, worker.name),)
                        if potential_combination not in tried_combinations:
                            eligible_workers.append(worker)
                        else:
                            self.logger.info(f"  - {worker.name} already tried for this shift with this combination")

            # Log eligible workers once after processing all workers
            self.log_backtracking("eligible", date, section, eligible_workers)

            
            if not eligible_workers:
                self.logger.info(f"FAILED: No eligible workers for Urgencias lab shift on {date.strftime('%Y-%m-%d')}")
                print(f"No eligible workers for Urgencias lab shift on {date.strftime('%Y-%m-%d')}")
                return False
            # For Monday shifts, handle the special rule for Velasco/Marín/María Coma
            if date.weekday() == 0:  # Monday
                self.logger.info(f"Monday shift detected on {date.strftime('%Y-%m-%d')}, applying special rules")
                
                # Find Velasco and Marín in eligible workers
                velasco = next((w for w in eligible_workers if "Roberto Velasco" in w.name), None)
                marin = next((w for w in eligible_workers if "Edu Marin" in w.name), None)
                maria_coma = next((w for w in eligible_workers if w.name == "María Coma"), None)
                
                # Check if Velasco or Marín worked weekend nights
                velasco_worked_weekend =self.worker_had_weekend_night_shift("Roberto Velasco", date)
                marin_worked_weekend = self.worker_had_weekend_night_shift("Edu Marin", date)
                
                # If either of them worked weekend nights, assign to María Coma
                if (velasco_worked_weekend or marin_worked_weekend) and maria_coma:
                    self.logger.info(f"Velasco or Marin worked weekend nights, assigning to María Coma")
                    best_worker = maria_coma
                # Otherwise, assign to either Velasco or Marín (prefer Velasco if both available)
                # If both Velasco and Marín are available, choose the one of the 3 (Velasco, Coma, Marin( who had their last shift the longest time ago
                else:
                # Not Monday, use regular assignment logic
                     best_worker = self.find_best_worker_for_shift(eligible_workers, date, section, period_metrics)
            else:
                # Not Monday, use regular assignment logic
                best_worker = self.find_best_worker_for_shift(eligible_workers, date, section, period_metrics)
            self.assign_shift_with_dual_availability(date, section, best_worker, shift_availability, regular_availability, period_metrics, period_name)
            self.logger.info(f"Assigned {best_worker.name} to Urgencias lab shift on {date.strftime('%Y-%m-%d')}")
            
            # Mark this assignment as tried
            current_assignments_key = tuple((d.isoformat(), s.nombre, w.name) for d, s, w, _, _ in assignment_stack)
            tried_combinations.add(current_assignments_key + ((date.isoformat(), section.nombre, best_worker.name),))
            
            # Update shift_availability
            shift_availability.loc[date, best_worker.name] = False
            
            # If this shift requires time off the next day, update shift_availability
            if section.libra:
                next_day = date + timedelta(days=1)
                if next_day in shift_availability.index:
                    shift_availability.loc[next_day, best_worker.name] = False
            
            # Save this assignment for potential backtracking
            assignment_stack.append((date, section, best_worker, shift_availability.copy(), regular_availability.copy()))            
            # Move to next Urgencias lab shift
            urg_shift_index += 1

        self.logger.info(f"SUCCESS: Successfully assigned all shifts for period {period_name}")
        print(f"Successfully assigned all shifts for period {period_name}")
        return True


    def initialize_regular_availability_matrix(self, start_date, end_date):
        """Create a matrix tracking worker availability for regular work schedule (jornada)"""
        # Create date range for the period
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Initialize availability matrix (True = available for regular work)
        availability = pd.DataFrame(
            True, 
            index=date_range, 
            columns=[worker.name for worker in self.workers]
        )
        
        # Mark unavailable days due to vacations, training, etc.
        for worker in self.workers:
            # Skip days worker is unavailable (if this data exists)
            if hasattr(worker, 'ooo_days') and worker.ooo_days:
                for day in worker.ooo_days:
                    if day in availability.index:
                        availability.loc[day, worker.name] = False
            
            # NEW: Mark days based on worker's regular work schedule (dias_semana_jornada)
            if hasattr(worker, 'dias_semana_jornada') and worker.dias_semana_jornada:
                for date in date_range:
                    weekday_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][date.weekday()]
                    if weekday_name not in worker.dias_semana_jornada:
                        availability.loc[date, worker.name] = False
        
        return availability

    def is_regular_shift(self, section):
        """Check if a section is considered a regular shift (not urgencias)"""
        return not ("Urg_G" in section.nombre)

    def check_minimum_staffing(self, worker, date, regular_availability):
        """Check if assigning this worker would leave at least 2 other workers available in the same category"""
        worker_category = None
        
        # Determine worker's category based on what areas they can work in
        if worker.can_work_in_area("Guardia_UCI"):
            worker_category = "Guardia_UCI"
        elif worker.can_work_in_area("HEMS"):
            worker_category = "HEMS"
        elif worker.can_work_in_area("Coordis"):
            worker_category = "Coordis"
        elif worker.can_work_in_area("Guardia_Urg"):
            worker_category = "Guardia_Urg"
        else:
            return True  # If we can't determine category, don't restrict
        
        # Count available workers in the same category for this date and next day
        dates_to_check = [date]
        next_day = date + timedelta(days=1)
        if next_day in regular_availability.index:
            dates_to_check.append(next_day)
        
        for check_date in dates_to_check:
            available_count = 0
            
            for other_worker in self.workers:
                if (other_worker.name != worker.name and 
                    other_worker.can_work_in_area(worker_category) and
                    other_worker.name in regular_availability.columns and
                    regular_availability.loc[check_date, other_worker.name]):
                    available_count += 1
            
            if available_count < 2:
                self.logger.info(f"Insufficient staffing for {worker_category} on {check_date}: only {available_count} workers would remain")
                return False
        
        return True

    def assign_shift_with_dual_availability(self, date, section, worker, shift_availability, regular_availability, period_metrics, period_name):
        """Assign a worker to a shift and update both availability matrices"""
        # CHECK: Prevent duplicate assignments
        existing_assignment = self.assignments[
            (self.assignments['date'] == date) & 
            (self.assignments['section_name'] == section.nombre)
        ]
        
        if not existing_assignment.empty:
            existing_worker = existing_assignment.iloc[0]['worker_name']
            self.logger.warning(f"DUPLICATE ASSIGNMENT PREVENTED: {section.nombre} on {date} already assigned to {existing_worker}")
            return
    
        # Add to assignments dataframe
        self.assignments = pd.concat([self.assignments, pd.DataFrame([{
            'date': date,
            'day_of_week': date.strftime("%A"),
            'section_name': section.nombre,
            'worker_name': worker.name,
            'hours': section.horas_turno,
            'libra': section.libra,
            'is_festivo': date in festivos,
            'is_weekend': self.is_weekend(date),
            'period': period_name
        }])], ignore_index=True)
        
        # Mark worker as unavailable for this day in shift availability
        shift_availability.loc[date, worker.name] = False
        
        # If this is a regular shift, also mark as unavailable in regular availability
        if self.is_regular_shift(section):
            regular_availability.loc[date, worker.name] = False
        
        # If libra=True, mark next day as unavailable too in both matrices
        if section.libra:
            next_day = date + timedelta(days=1)
            if next_day in shift_availability.index:
                shift_availability.loc[next_day, worker.name] = False
            if self.is_regular_shift(section) and next_day in regular_availability.index and self.is_regular_shift(section):
                regular_availability.loc[next_day, worker.name] = False

        # Update period metrics
        period_metrics[worker.name]['total_shifts'] += 1
        period_metrics[worker.name]['total_hours'] += section.horas_turno
        
        if self.is_night_shift(section):
            period_metrics[worker.name]['night_shifts'] += 1
        
        if self.is_weekend(date):
            period_metrics[worker.name]['weekend_shifts'] += 1
            
        if date in festivos:
            period_metrics[worker.name]['festivo_shifts'] += 1
            
        # Update yearly metrics as well
        self.yearly_metrics[worker.name]['total_shifts'] += 1
        self.yearly_metrics[worker.name]['total_hours'] += section.horas_turno
        
        if self.is_night_shift(section):
            self.yearly_metrics[worker.name]['night_shifts'] += 1
        
        if self.is_weekend(date):
            self.yearly_metrics[worker.name]['weekend_shifts'] += 1
            
        if date in festivos:
            self.yearly_metrics[worker.name]['festivo_shifts'] += 1
    
    def find_best_worker_for_shift(self, eligible_workers, date, section, period_metrics):
        """Find the best worker for a shift using various criteria"""
        # Calculate a score for each worker
        worker_scores = []
        
        if section.nombre == "UCI_G_festivo":
            for worker in eligible_workers:
            # Find the last UCI_G_festivo shift assigned to this worker
                worker_history = self.assignments[
                    (self.assignments['worker_name'] == worker.name) &
                    (self.assignments['section_name'] == "UCI_G_festivo")
                ]
                if not worker_history.empty:
                    last_shift_date = worker_history['date'].max()
                    if isinstance(last_shift_date, pd.Timestamp):
                        last_shift_date = last_shift_date.date()

                    # last_shift_date = datetime.strptime(last_shift_date, '%Y-%m-%d')

                    days_since_last_shift = (date - last_shift_date).days
                else:
                    # Assign a fixed value if no shifts in history
                    days_since_last_shift = 9999  # Arbitrary large value
                
                worker_scores.append((worker, days_since_last_shift, worker.name))
                
            # Sort workers by days since last shift (descending order) and then by name (ascending order)
            worker_scores.sort(key=lambda x: (-x[1], x[2]))
            
            # Return the worker who did the shift longest ago (and resolves ties by name)
            return worker_scores[0][0]

        if section.nombre in ["Urg_G_noche_l", "Urg_G_festivo_mañana", "Urg_G_festivo_noche", "Urg_G_refuerzo_fyf"]:
            # From the available select the one who worked the longest time ago
            for worker in eligible_workers:
                # Find the last shift assigned to this worker for this section
                worker_history = self.assignments[
                    (self.assignments['worker_name'] == worker.name) &
                    (self.assignments['section_name'] == section.nombre)
                ]
                if not worker_history.empty:
                    last_shift_date = worker_history['date'].max()
                    if isinstance(last_shift_date, pd.Timestamp):
                        last_shift_date = last_shift_date.date()

                    days_since_last_shift = (date - last_shift_date).days
                else:
                    # Assign a fixed value if no shifts in history
                    days_since_last_shift = 9999  # Arbitrary large value
                
                worker_scores.append((worker, days_since_last_shift, worker.birth_year if hasattr(worker, 'birth_year') else 0))
            
            # Sort workers by days since last shift (descending order) and then by birth year (ascending order)
            worker_scores.sort(key=lambda x: (-x[1], x[2]))
            
            # Return the worker who did the shift longest ago (and resolves ties by youngest age)
            return worker_scores[0][0]
        
        # Default case - only consider current and prior month
        current_month = date.month
        current_year = date.year
        prior_month = current_month - 1 if current_month > 1 else 12
        prior_year = current_year if current_month > 1 else current_year - 1
        
        for worker in eligible_workers:
            score = 0
            
            # Get shifts from current and prior month only
            recent_shifts = self.assignments[
                (self.assignments['worker_name'] == worker.name) &
                (
                    ((pd.DatetimeIndex(self.assignments['date']).month == current_month) & 
                    (pd.DatetimeIndex(self.assignments['date']).year == current_year)) |
                    ((pd.DatetimeIndex(self.assignments['date']).month == prior_month) & 
                    (pd.DatetimeIndex(self.assignments['date']).year == prior_year))
                )
            ]
            
            recent_shifts_count = len(recent_shifts)
            recent_hours = recent_shifts['hours'].sum() if len(recent_shifts) > 0 else 0
            
            # NEW: Category-specific workload calculation for UCI shifts
            if section.nombre == "UCI_G_lab":
                # Count UCI-specific shifts for this worker
                uci_shifts = recent_shifts[recent_shifts['section_name'].str.contains('UCI_G')]
                uci_shifts_count = len(uci_shifts)
                uci_hours = uci_shifts['hours'].sum() if len(uci_shifts) > 0 else 0
                
                # Determine worker's versatility (how many areas they can work in)
                versatility = 0
                if worker.can_work_in_area("Guardia_UCI"):
                    versatility += 1
                if worker.can_work_in_area("HEMS"):
                    versatility += 1
                if worker.can_work_in_area("Coordis"):
                    versatility += 1
                if worker.can_work_in_area("Guardia_Urg"):
                    versatility += 1
                
                # Workers with fewer capabilities should get proportionally more UCI shifts
                # but not ALL of them
                versatility_factor = max(1, versatility)  # Minimum factor of 1
                
                # Calculate expected UCI workload based on versatility
                # Less versatile workers should have higher UCI workload tolerance
                expected_uci_ratio = 1.0 / versatility_factor
                
                # Score based on how much this worker has been doing UCI work
                # relative to their expected share
                uci_workload_score = uci_shifts_count * expected_uci_ratio
                
                # Penalize workers who are already doing too much UCI work relative to their versatility
                if versatility_factor == 1:  # UCI-only workers
                    # Allow them to do more UCI work, but with diminishing returns
                    score -= uci_workload_score * 0.3  # Reduced penalty
                    score -= recent_shifts_count * 0.3
                    score -= recent_hours * 0.2
                    period_shifts = period_metrics[worker.name]['total_shifts']
                    score -= period_shifts * 0.5
                else:  # Multi-area workers
                    # Encourage more balanced distribution
                    score -= uci_workload_score * 0.5
                    score -= recent_shifts_count * 0.3
                    score -= recent_hours * 0.2
                    period_shifts = period_metrics[worker.name]['total_shifts']
                    score -= period_shifts * 0.2
            
            else:# Consider current period workload
                period_shifts = period_metrics[worker.name]['total_shifts']
                score -= period_shifts * 0.2
            
            worker_scores.append((worker, score))
        
        # Return the worker with the highest score
        self.log_backtracking("scores", date, section, worker_scores)
        return max(worker_scores, key=lambda x: x[1])[0]
    
    def _assign_role_shifts(self, role_id, rotation_offset, workers, shifts, availability, period_metrics, period_name, assigned_shifts=None):
        """Assign shifts for a specific role in the Urgencias weekend rotation pattern"""
        if not shifts:
            self.logger.info(f"No shifts to assign for role {role_id} in period {period_name}")
            return
        
        # Use the passed assigned_shifts set, or create a new one if None
        if assigned_shifts is None:
            assigned_shifts = set()
        else:
            # Make a copy to avoid modifying the original
            assigned_shifts = assigned_shifts.copy()
        
        self.logger.info(f"Starting assignment for role {role_id} in period {period_name} with {len(shifts)} shifts")
        
        # REMOVE ALL FIRST FRIDAY HANDLING - it's now done before calling this method
        
        # Group remaining shifts by weekend (using Friday/Saturday date as the key)
        weekend_shifts = {}
        for shift_date, section in shifts:
            shift_key = (shift_date.isoformat(), section.nombre)
            if shift_key in assigned_shifts:
                self.logger.info(f"Skipping already assigned shift: {section.nombre} on {shift_date.strftime('%Y-%m-%d')}")
                continue

            if shift_date.weekday() == 4:  # Friday
                weekend_key = shift_date.isoformat()
            elif shift_date.weekday() == 5:  # Saturday
                weekend_key = (shift_date - timedelta(days=1)).isoformat()
            elif shift_date.weekday() == 6:  # Sunday
                weekend_key = (shift_date - timedelta(days=2)).isoformat()
            else:
                # For holidays that fall on weekdays, use the date itself
                weekend_key = shift_date.isoformat()
            
            if weekend_key not in weekend_shifts:
                weekend_shifts[weekend_key] = []
            weekend_shifts[weekend_key].append((shift_date, section))
        
        # Determine preferred workers for this role based on rotation
        preferred_workers = []
        for i, worker in enumerate(workers):
            if (i + rotation_offset) % 3 == role_id:
                preferred_workers.append(worker)
        
        self.logger.info(f"Preferred workers for role {role_id}: {[w.name for w in preferred_workers]}")
        
        # For each weekend, assign ALL shifts to ONE worker
        for weekend_key, weekend_role_shifts in weekend_shifts.items():
            self.logger.info(f"Processing weekend {weekend_key} with {len(weekend_role_shifts)} shifts for role {role_id}")
            
            # Find workers who are available for ALL shifts in this weekend's role
            eligible_preferred_workers = []
            
            # Check each preferred worker for availability on all shifts
            for worker in preferred_workers:
                can_do_all_shifts = True
                
                # Check if worker is available for every shift in this role for this weekend
                for shift_date, section in weekend_role_shifts:
                    if not (worker.name in availability.columns and 
                        availability.loc[shift_date, worker.name] and 
                        worker.state == "Alta"):
                        can_do_all_shifts = False
                        self.logger.info(f"Worker {worker.name} cannot do shift on {shift_date} for {section.nombre}")
                        break
                
                if can_do_all_shifts:
                    eligible_preferred_workers.append(worker)
            
            # If we found preferred workers who can do all shifts, use them
            if eligible_preferred_workers:
                # Find the best worker among those who can do all shifts
                best_worker = self.find_best_worker_for_shift(
                    eligible_preferred_workers, 
                    weekend_role_shifts[0][0],  # Use first shift date for scoring
                    weekend_role_shifts[0][1],  # Use first shift section for scoring
                    period_metrics
                )
                
                # Assign ALL shifts for this weekend's role to the same worker
                for shift_date, section in weekend_role_shifts:
                    self.assign_shift_with_dual_availability(shift_date, section, best_worker, availability, [], period_metrics, period_name)
                    assigned_shifts.add((shift_date.isoformat(), section.nombre))
                    self.logger.info(f"Assigned role {role_id} to preferred worker {best_worker.name} on {shift_date.strftime('%Y-%m-%d')}")
            
            # If no preferred workers can do all shifts, try other eligible workers
            else:
                self.logger.info(f"No preferred workers available for all role {role_id} shifts on weekend {weekend_key}")
                
                # Check all other workers who can do all shifts
                eligible_backup_workers = []
                for worker in workers:
                    if worker in preferred_workers:
                        continue  # Skip preferred workers, already checked
                        
                    can_do_all_shifts = True
                    for shift_date, section in weekend_role_shifts:
                        if not (worker.name in availability.columns and 
                            availability.loc[shift_date, worker.name] and 
                            worker.state == "Alta"):
                            can_do_all_shifts = False
                            break
                    
                    if can_do_all_shifts:
                        eligible_backup_workers.append(worker)
                
                if eligible_backup_workers:
                    best_worker = self.find_best_worker_for_shift(
                        eligible_backup_workers, 
                        weekend_role_shifts[0][0],
                        weekend_role_shifts[0][1],
                        period_metrics
                    )
                    
                    # Assign ALL shifts to the same worker
                    for shift_date, section in weekend_role_shifts:
                        self.assign_shift_with_dual_availability(shift_date, section, best_worker, availability, [], period_metrics, period_name)
                        assigned_shifts.add((shift_date.isoformat(), section.nombre))  # Add this line
                        self.logger.info(f"Assigned role {role_id} to worker {best_worker.name} on {shift_date.strftime('%Y-%m-%d')}")
                else:
                    self.logger.warning(f"FAILED TO ASSIGN: No worker available for all shifts in role {role_id} on weekend {weekend_key}")
        
        self.logger.info(f"Completed assignment for role {role_id} in period {period_name}")
    
    def assign_all_shifts(self):
        """Assign shifts for the entire year in biweekly periods"""
        # Start with January 1, 2025
        current_date = datetime_date(2025, 1, 1)
        end_of_year = datetime_date(2025, 12, 31)
        
        period_number = 1
        
        while current_date <= end_of_year:
            # Calculate the end of this two-week period
            end_date = current_date + timedelta(days=30)  # 14 days (2 weeks) minus 1
            
            # Make sure we don't go beyond the end of the year
            if end_date > end_of_year:
                end_date = end_of_year
                
            # Format period name as "Period X: Jan 1-14"
            period_name = f"Period {period_number}: {current_date.strftime('%b %d')}-{end_date.strftime('%d')}"
            
            # Assign shifts for this two-week period
            success = self.assign_period_shifts_with_backtracking(current_date, end_date, period_name)
            
            if not success:
                print(f"Failed to assign shifts for period {period_name}")
                break
            
            # Move to next period
            current_date = end_date + timedelta(days=1)
            period_number += 1
    
    def get_assignment_stats(self):
        """Get summary statistics for the assignments"""
        stats = {}
        
        # Per worker stats
        for worker_name, metrics in self.yearly_metrics.items():
            stats[worker_name] = {
                'total_shifts': metrics['total_shifts'],
                'total_hours': metrics['total_hours'],
                'night_shifts': metrics['night_shifts'],
                'weekend_shifts': metrics['weekend_shifts'],
                'festivo_shifts': metrics['festivo_shifts']
            }
            
        # Per period stats
        period_stats = {}
        for period_name in self.assignments['period'].unique():
            period_df = self.assignments[self.assignments['period'] == period_name]
            
            worker_stats = {}
            for worker_name in self.yearly_metrics.keys():
                worker_df = period_df[period_df['worker_name'] == worker_name]
                
                # Fix: Explicitly convert to int before summing
                night_shift_count = sum(1 if self.is_night_shift_by_name(row['section_name']) else 0 
                                    for _, row in worker_df.iterrows())
                weekend_shifts = int(worker_df['is_weekend'].sum()) if len(worker_df) > 0 else 0
                festivo_shifts = int(worker_df['is_festivo'].sum()) if len(worker_df) > 0 else 0
                
                worker_stats[worker_name] = {
                    'total_shifts': len(worker_df),
                    'total_hours': float(worker_df['hours'].sum()) if len(worker_df) > 0 else 0,
                    'night_shifts': night_shift_count,
                    'weekend_shifts': weekend_shifts,
                    'festivo_shifts': festivo_shifts
                }
                    
            period_stats[period_name] = worker_stats
            
        stats['period_stats'] = period_stats
        
        # Overall stats
        stats['total_shifts_assigned'] = len(self.assignments)
        stats['unassigned_shifts_count'] = self.count_unassigned_shifts()
        
        return stats

    def is_night_shift_by_name(self, section_name):
        """Check if a section name indicates a night shift"""
        return 'noche' in section_name.lower() or 'nocturno' in section_name.lower()
    
    def count_unassigned_shifts(self):
        """Count shifts that should be assigned but weren't"""
        unassigned_count = 0
        
        # For each day, check if all required shifts were assigned
        for date, day_type in self.calendario:
            for section in self.sections:
                # Skip the excluded sections
                if ("Urg_G_noche_l" in section.nombre or "Urg_G_tarde-noche_l" in section.nombre or
                    "Urg_G_festivo" in section.nombre or "Urg_G_refuerzo_fyf" in section.nombre):
                    continue
                
                # Check if this section applies to this day
                if day_type not in section.dias:
                    continue
                    
                # Skip if this section has specific dates and this date is not in it
                if hasattr(section, 'fechas') and section.fechas and date not in section.fechas:
                    continue
                
                # Check if we have an assignment for this date and section
                matching_assignments = self.assignments[
                    (self.assignments['date'] == date) & 
                    (self.assignments['section_name'] == section.nombre)
                ]
                
                if len(matching_assignments) == 0:
                    unassigned_count += 1
        
        return unassigned_count
    
    def export_to_csv(self, filename="shift_assignments.csv"):
        """Export assignments to CSV file"""
        self.assignments.sort_values(by=['date', 'section_name']).to_csv(filename, index=False)
        timestamp = datetime_type.now().strftime("%Y%m%d_%H%M%S")
        assignments_csv_path = f"./data/assignments_{timestamp}.csv"
        self.assignments.sort_values(by=['date', 'section_name']).to_csv(assignments_csv_path)
        # Also export period-wise statistics
        stats = self.get_assignment_stats()
        
        # Create a DataFrame with worker statistics per period
        period_stats_rows = []
        for period, workers in stats['period_stats'].items():
            for worker_name, metrics in workers.items():
                if metrics['total_shifts'] > 0:  # Only include workers with shifts
                    period_stats_rows.append({
                        'Period': period,
                        'Worker': worker_name,
                        'Total Shifts': metrics['total_shifts'],
                        'Total Hours': metrics['total_hours'],
                        'Night Shifts': metrics['night_shifts'],
                        'Weekend Shifts': metrics['weekend_shifts'],
                        'Festivo Shifts': metrics['festivo_shifts']
                    })
                    
        # Export to CSV if we have data
        if period_stats_rows:
            pd.DataFrame(period_stats_rows).to_csv("data/period_statistics.csv", index=False)
            print("Period statistics exported to period_statistics.csv")
            
        # Export yearly statistics
        yearly_stats_rows = []
        for worker_name, metrics in stats.items():
            if worker_name != 'period_stats' and worker_name != 'total_shifts_assigned' and worker_name != 'unassigned_shifts_count':
                yearly_stats_rows.append({
                    'Worker': worker_name,
                    'Total Shifts': metrics['total_shifts'],
                    'Total Hours': metrics['total_hours'],
                    'Night Shifts': metrics['night_shifts'],
                    'Weekend Shifts': metrics['weekend_shifts'],
                    'Festivo Shifts': metrics['festivo_shifts']
                })
                
        # Export to CSV if we have data
        if yearly_stats_rows:
            pd.DataFrame(yearly_stats_rows).to_csv("data/yearly_statistics.csv", index=False)
            print("Yearly statistics exported to data/yearly_statistics.csv")

    def setup_logging(self):
        """Configure logging for backtracking operations"""
        log_filename = f"./data/backtracking_log_{(datetime_type.now() + timedelta(hours=2)).strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)  # Ensure the directory exists
        # Create a logger
        self.logger = logging.getLogger('backtracking')
        self.logger.setLevel(logging.INFO)
        
        # Create a file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        
        # Create a formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        self.logger.addHandler(file_handler)
        self.logger.info("Logging setup complete")
    
    def log_backtracking(self, action, date, section, worker=None, success=None):
        """Log backtracking actions with relevant details"""
        if action == "attempt":
            self.logger.info(f"Attempting to assign {section.nombre} on {date.strftime('%Y-%m-%d')} to {worker.name}")
        elif action == "assign":
            self.logger.info(f"SUCCESS: Assigned {section.nombre} on {date.strftime('%Y-%m-%d')} to {worker.name}")
        elif action == "backtrack":
            self.logger.info(f"BACKTRACK: Undoing assignment of {section.nombre} on {date.strftime('%Y-%m-%d')} from {worker.name}")
        elif action == "no_eligible":
            self.logger.info(f"NO ELIGIBLE WORKERS: Failed to find eligible workers for {section.nombre} on {date.strftime('%Y-%m-%d')}")
        elif action == "eligible":
            worker_names = ", ".join([w.name for w in worker]) if isinstance(worker, list) else "None"
            self.logger.info(f"ELIGIBLE WORKERS for {section.nombre} on {date.strftime('%Y-%m-%d')}: {worker_names}")
        elif action == "scores":
            score_details = ", ".join([f"{w.name}: {score:.2f}" for w, score in worker])
            self.logger.info(f"WORKER SCORES for {section.nombre} on {date.strftime('%Y-%m-%d')}: {score_details}")

# Running the assignment process
def main():
    st.write("### Shift Assignment Process")
    assigner = ShiftAssigner(workers, all_sections, calendario_2026)
    assigner.assign_all_shifts()
    
    # Print assignment stats
    stats = assigner.get_assignment_stats()
    print("\nOverall Assignment Statistics:")
    print(f"Total shifts assigned: {stats['total_shifts_assigned']}")
    print(f"Unassigned shifts: {stats['unassigned_shifts_count']}")
    
    print("\nYearly Worker Statistics:")
    for worker_name, metrics in {k: v for k, v in stats.items() 
                                if k != 'period_stats' and k != 'total_shifts_assigned' and k != 'unassigned_shifts_count'}.items():
        print(f"{worker_name}: {metrics['total_shifts']} shifts, {metrics['total_hours']} hours, "
              f"{metrics['night_shifts']} nights, {metrics['weekend_shifts']} weekends, "
              f"{metrics['festivo_shifts']} festivos")
    
    # Export to CSV
    assigner.export_to_csv()

if __name__ == "__main__":
    main()