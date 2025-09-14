import json
import csv

# Read the JSON file
with open('workers.json', 'r', encoding='utf-8') as f:
    workers_data = json.load(f)

# Define CSV headers
headers = [
    'name', 'initials', 'birth_year', 'category', 'state',
    'available_work_hours', 'available_guard_hours', 'areas',
    'has_hems', 'has_coordis', 'has_guardia_uci', 'has_guardia_urg',
    'avoid_days', 'days_assigned_summary'
]

# Write CSV file
with open('workers.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    writer.writeheader()
    
    for worker in workers_data:
        # Process areas
        areas = worker.get('areas', [])
        areas_str = ', '.join(areas)
        
        # Process days assigned
        days_assigned = worker.get('days_assigned', {})
        days_summary = []
        for area, days in days_assigned.items():
            days_summary.append(f"{area}({','.join(days)})")
        days_assigned_summary = '; '.join(days_summary)
        
        # Write row
        writer.writerow({
            'name': worker['name'],
            'initials': worker['initials'],
            'birth_year': worker['birth_year'],
            'category': worker['category'],
            'state': worker['state'],
            'available_work_hours': worker['available_work_hours'],
            'available_guard_hours': worker['available_guard_hours'],
            'areas': areas_str,
            'has_hems': 'HEMS' in areas,
            'has_coordis': 'Coordis' in areas,
            'has_guardia_uci': 'Guardia_UCI' in areas,
            'has_guardia_urg': 'Guardia_Urg' in areas,
            'avoid_days': ', '.join(worker.get('avoid_days', [])),
            'days_assigned_summary': days_assigned_summary
        })

print("Workers CSV file created successfully!")