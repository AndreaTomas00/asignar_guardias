import datetime
class Section:
    def __init__(self, nombre, dias, horas_turno, horas_jornada, personal, libra, fechas):
        self.nombre = nombre
        self.dias = dias
        self.horas_turno = horas_turno
        self.horas_jornada = horas_jornada
        self.personal = personal
        self.libra = libra
        self.fechas = fechas
        
    def _es_semana_hems(fecha):
        semana = fecha.isocalendar()[1]
        if fecha < datetime.date(2026, 5, 25):
            return semana % 2 == 0  # Semanas pares hasta el 25 de mayo
        elif fecha < datetime.date(2026, 11, 23):
            return semana % 2 != 0  # Semanas impares hasta el 23 de noviembre
        else:
            return semana % 2 == 0 #Semanas pares hasta final de año
    
    def _to_dict(self):
        return {
            "nombre": self.nombre,
            "dias": self.dias,
            "horas_turno": self.horas_turno,
            "personal": self.personal,
            "libra": self.libra,
            "fechas": self.fechas
        }

dias_coordis = {
    datetime.date(2025, 1, 2),
    datetime.date(2025, 1, 4),
    datetime.date(2025, 1, 14),
    datetime.date(2025, 1, 31),
    datetime.date(2025, 2, 12),
    datetime.date(2025, 2, 16),
    datetime.date(2025, 2, 24),
    datetime.date(2025, 3, 13),
    datetime.date(2025, 3, 15),
    datetime.date(2025, 3, 25),
    datetime.date(2025, 4, 11),
    datetime.date(2025, 4, 23),
    datetime.date(2025, 4, 27),
    datetime.date(2025, 5, 5),
    datetime.date(2025, 5, 22),
    datetime.date(2025, 5, 24),
    datetime.date(2025, 5, 28),
    datetime.date(2025, 6, 1),
    datetime.date(2025, 6, 9),
    datetime.date(2025, 6, 26),
    datetime.date(2025, 6, 28),
    datetime.date(2025, 7, 8),
    datetime.date(2025, 7, 25),
    datetime.date(2025, 8, 6),
    datetime.date(2025, 8, 10),
    datetime.date(2025, 8, 18),
    datetime.date(2025, 9, 4),
    datetime.date(2025, 9, 6),
    datetime.date(2025, 9, 16),
    datetime.date(2025, 10, 3),
    datetime.date(2025, 10, 15),
    datetime.date(2025, 10, 19),
    datetime.date(2025, 10, 27),
    datetime.date(2025, 11, 13),
    datetime.date(2025, 11, 15),
    datetime.date(2025, 12, 1),
    datetime.date(2025, 12, 18),
    datetime.date(2025, 12, 20),
    datetime.date(2025, 12, 30)
}

festivos = [
    datetime.date(2026, 1, 1),
    datetime.date(2026, 1, 6),
    datetime.date(2026, 4, 3),
    datetime.date(2026, 4, 6),
    datetime.date(2026, 5, 1),
    datetime.date(2026, 5, 11),
    datetime.date(2026, 6, 24),
    datetime.date(2026, 8, 15),
    datetime.date(2026, 9, 7),
    datetime.date(2026, 9, 11),
    datetime.date(2026, 10, 12),
    datetime.date(2026, 12, 8),
    datetime.date(2026, 12, 25),
    datetime.date(2026, 12, 26),
    datetime.date(2025, 2, 16),
    datetime.date(2025, 4, 3),
    datetime.date(2025, 4, 6),
    datetime.date(2025, 5, 1),
    datetime.date(2025, 5, 12),
    datetime.date(2025, 6, 24),
    datetime.date(2025, 8, 15),
    datetime.date(2025, 9, 7),
    datetime.date(2025, 9, 11),
    datetime.date(2025, 10, 12),
    datetime.date(2025, 10, 31),
    datetime.date(2025, 11, 1),
    datetime.date(2025, 12, 8),
    datetime.date(2025, 12, 25),
    datetime.date(2025, 12, 26),
]
def generar_calendario_anual(year, festivos):
    calendario = []
    fecha = datetime.date(year, 1, 1)
    while fecha.year == year:
        if fecha in festivos:
            dia_semana = "festivo"
        else:
            dia_semana = fecha.strftime("%A").lower()
        calendario.append((fecha, dia_semana))
        fecha += datetime.timedelta(days=1)
    return calendario

calendario_2026 = generar_calendario_anual(2026, festivos)

sections = []

