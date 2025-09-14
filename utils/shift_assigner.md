# ShiftAssigner Class Documentation

The `ShiftAssigner` class is responsible for managing and assigning shifts to workers based on various constraints and priorities. This document provides an overview of each function in the class and explains their purpose and functionality. Special attention is given to the `assign_period_shifts_with_backtracking` function, which is explained step by step.

---

## Class Initialization

### `__init__(self, workers, sections, priority, calendario, year=2025)`
Initializes the `ShiftAssigner` class with the following parameters:
- `workers`: A list of worker objects.
- `sections`: A list of section objects representing different shift types.
- `priority`: A dictionary mapping section names to their priority levels.
- `calendario`: A calendar object containing information about holidays and other special days.
- `year`: The year for which shifts are being assigned (default is 2025).

---

## Helper Functions

### `_generate_and_load_historical_data(self)`
Generates and loads historical shift data into the assignments dataframe. This function ensures that past assignments are considered when calculating metrics and assigning new shifts.

### `_init_metrics(self)`
Initializes yearly metrics for each worker, such as total shifts, night shifts, weekend shifts, and total hours. These metrics are updated as shifts are assigned.

### `initialize_availability_matrix(self, start_date, end_date)`
Creates a matrix tracking worker availability for a specific period. It marks unavailable days due to vacations, training, or previously assigned shifts.

### `is_night_shift(self, section)`
Checks if a section is considered a night shift based on its name.

### `is_weekend(self, date)`
Checks if a given date falls on a weekend (Saturday or Sunday).

### `get_urgencias_friday_cadence(self)`
Returns a list of workers eligible for "Urgencias" shifts on Fridays, sorted by birth year (youngest first).

### `is_first_friday_of_month(self, date)`
Checks if a given date is the first Friday of its month.

### `count_monthly_shifts(self, worker_name, month, year, section_pattern)`
Counts how many shifts of a specific type a worker has in a given month.

### `worker_had_weekend_night_shift(self, worker_name, monday_date)`
Checks if a worker had a night shift on the preceding Saturday or Sunday.

### `assign_shift(self, date, section, worker, availability, period_metrics, period_name)`
Assigns a worker to a shift and updates availability, metrics, and the assignments dataframe.

### `get_workload_score(self, worker_name, period_metrics, is_night=False, is_weekend=False, is_festivo=False, yearly_weight=0.3)`
Calculates a worker's workload score based on period and yearly metrics. Lower scores indicate better candidates for assignment.

### `_get_required_category(self, section)`
Maps a section to the required worker category based on predefined mappings.

---

## Main Function: `assign_period_shifts_with_backtracking`

### Description
This function assigns shifts for a specific period using a backtracking algorithm. It ensures that all shifts are assigned while respecting constraints such as worker availability, section requirements, and workload fairness.

### Step-by-Step Explanation

1. **Initialize Metrics and Availability**
   - Metrics for the period are initialized for each worker.
   - An availability matrix is created to track which workers are available on specific dates.

2. **Identify Shifts to Assign**
   - Iterates through each date in the period to determine which sections (shifts) apply to that day.
   - Checks if the section applies to the day type (weekday, weekend, holiday) and if it has specific dates.
   - Adds eligible shifts to the `shifts_to_assign` list.

3. **Sort Shifts by Priority and Date**
   - Shifts are sorted based on section priority and date to ensure high-priority shifts are assigned first.

4. **Backtracking Algorithm**
   - A stack is used to keep track of assignments and allow backtracking if a conflict arises.
   - For each shift:
     - Identifies eligible workers based on availability, state, and section requirements.
     - Calculates workload scores for eligible workers to find the best candidate.
     - Assigns the shift to the best worker and updates metrics and availability.
   - If no eligible workers are found, the algorithm backtracks to the previous assignment and tries a different combination.

5. **Handle Special Cases**
   - Special handling for "Urgencias" weekend shifts, including reinforcement shifts for the first Friday of the month.

6. **Finalize Assignments**
   - Once all shifts are successfully assigned, the function logs the results and returns `True`.
   - If no solution is found, the function restores the original assignments and returns `False`.

### Key Variables
- `shifts_to_assign`: A list of shifts that need to be assigned.
- `availability`: A matrix tracking worker availability.
- `period_metrics`: Metrics for the current period.
- `assignment_stack`: A stack used for backtracking.
- `tried_combinations`: A set of previously tried assignments to avoid repetition.

### Logging and Debugging
The function logs detailed information about the assignment process, including:
- Eligible workers for each shift.
- Reasons for backtracking.
- Final results of the assignment process.

---

## Example Usage
```python
# Initialize ShiftAssigner
shift_assigner = ShiftAssigner(workers, sections, priority, calendario)

# Assign shifts for a specific period
success = shift_assigner.assign_period_shifts_with_backtracking(
    start_date=datetime(2025, 6, 1),
    end_date=datetime(2025, 6, 30),
    period_name="June 2025"
)

if success:
    print("Shifts assigned successfully!")
else:
    print("Failed to assign all shifts.")
```

---

## Notes
- Ensure that the `workers` and `sections` lists are properly initialized before calling the `assign_period_shifts_with_backtracking` function.
- Use the logging output to debug issues with the assignment process.
- Customize the `_get_required_category` function to match your specific section-to-category mappings.
