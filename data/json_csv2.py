import json
import csv

# Read the JSON file
with open('sections.json', 'r', encoding='utf-8') as f:
    sections_data = json.load(f)

# Define CSV headers
headers = [
    'nombre', 'horas_turno', 'personal', 'libra', 'dias', 'fechas',
    'num_dias', 'num_fechas', 'tipo', 'periodo',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'festivo'
]

# Write CSV file
with open('sections.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    writer.writeheader()
    
    for section in sections_data:
        dias = section.get('dias', [])
        fechas = section.get('fechas', [])
        
        # Determine section type
        if 'HEMS' in section['nombre']:
            tipo = 'HEMS'
        elif 'Coordis' in section['nombre']:
            tipo = 'Coordis'
        elif 'UCI' in section['nombre']:
            tipo = 'UCI'
        elif 'Urg' in section['nombre']:
            tipo = 'Urgencias'
        else:
            tipo = 'Otro'
        
        # Determine time period
        nombre_lower = section['nombre'].lower()
        if 'noche' in nombre_lower:
            periodo = 'Noche'
        elif 'tarde' in nombre_lower:
            periodo = 'Tarde'
        elif 'mañana' in nombre_lower or 'diurno' in nombre_lower:
            periodo = 'Mañana'
        elif 'festivo' in nombre_lower:
            periodo = 'Festivo'
        else:
            periodo = 'Otro'
        
        # Write row
        writer.writerow({
            'nombre': section['nombre'],
            'horas_turno': section['horas_turno'],
            'personal': section['personal'],
            'libra': section['libra'],
            'dias': ', '.join(dias),
            'fechas': ', '.join(fechas),
            'num_dias': len(dias),
            'num_fechas': len(fechas),
            'tipo': tipo,
            'periodo': periodo,
            'monday': 'monday' in dias,
            'tuesday': 'tuesday' in dias,
            'wednesday': 'wednesday' in dias,
            'thursday': 'thursday' in dias,
            'friday': 'friday' in dias,
            'saturday': 'saturday' in dias,
            'sunday': 'sunday' in dias,
            'festivo': 'festivo' in dias
        })

print("Sections CSV file created successfully!")