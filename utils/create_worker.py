from utils.worker import Worker

workers = []
workers.append(
    Worker(name="Núria Torre", initials="NT", birth_year=1983, category="Uci_neonatal", state="Alta",
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["tuesday"], "Coordis":["tuesday"], "Guardia_UCI":["tuesday"]},
    available_work_hours=1688, available_guard_hours=499)
)
workers.append(
    Worker(name="Adrián Ranera", initials="AR", birth_year=1987, category="Urgencias", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["wednesday"], "Coordis":["wednesday"], "Guardia_UCI":["wednesday"]},
    section_day_constraints={"Coordis_dia": ["friday"], "HEMS_tarde": ["friday"]},
    available_work_hours=1688, available_guard_hours=499)
)
workers.append(
    Worker(name="Anna Gelman", initials="AG", birth_year=1986, category="Planta", 
    areas=["Guardia_UCI"], days_assigned={"Guardia_UCI":["monday"]}, available_work_hours=1688, available_guard_hours=499)
)
workers.append(
    Worker(name="Aurora Eslava", initials="AE", birth_year=1994, category="Planta", state="Baja",
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"Guardia_UCI":["monday"]}, available_work_hours=1688, available_guard_hours=499)
) ## PREGUNTAR

workers.append(
    Worker(name="Clara Comalrena", initials="CC", birth_year=1993, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["monday"]}, available_work_hours=1688, available_guard_hours=499)
)
workers.append(
    Worker(name="Dani de Luis", initials="DD", birth_year=1990, category="Uci_neonatal", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["thursday"], "Coordis":["thursday"], "Guardia_UCI":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Diana García", initials="DG", birth_year=1987, category="Urgencias", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Edu Marín", initials="EM", birth_year=1992, category="Urgencias", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["monday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Gemma Merlos", initials="GM", birth_year=1994, category="Urgencias", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["friday"]}, avoid_days=["sunday"],
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Griselda Vallés", initials="GV", birth_year=1984, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Helvia Benito", initials="GM", birth_year=1994, category="Urgencias", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["friday"]}, avoid_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Irene Baena", initials="IB", birth_year=1982, category="Urgencias", 
    areas=["Guardia_UCI", "Guardia_Urg"], days_assigned={"Guardia_UCI":["thursday"], "Guardia_Urg":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Jacobo Pérez", initials="JP", birth_year=1977, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["tuesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Judith Sánchez", initials="JS", birth_year=1983, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Lluís Renter", initials="LR", birth_year=1977, category="Uci_pediátrica", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["thursday"], "Coordis":["thursday"], "Guardia_UCI":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="María Coma", initials="MC", birth_year=1987, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["monday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="María García Besteiro", initials="MB", birth_year=1986, category="Uci_pediátrica", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["wednesday"], "Coordis":["wednesday"], "Guardia_UCI":["wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="María Gual", initials="MG", birth_year=1990, category="Uci_pediátrica", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["tuesday"], "Coordis":["tuesday"], "Guardia_UCI":["tuesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Marina Pedrosa", initials="MP", birth_year=1994, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Marta Sardà", initials="MS", birth_year=1983, category="Uci_neonatal", 
    areas=["Guardia_UCI"], days_assigned={"Guardia_UCI":["wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Marta Susana", initials="MSu", birth_year=1992, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["tuesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Miguel García", initials="MG", birth_year=1981, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Mireia García Cuscó", initials="MC", birth_year=1984, category="Uci_pediátrica", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["monday"], "Coordis":["monday"], "Guardia_UCI":["monday"]},
    available_work_hours=1688, available_guard_hours=399)
)

workers.append(
    Worker(name="Núria Cahís", initials="NC", birth_year=1989, category="urgencias", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Paula Ribes", initials="PR", birth_year=1993, category="planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Pilar Díez del Corral", initials="PD", birth_year=1990, category="Uci_neonatal", 
    areas=["HEMS", "Coordis", "Guardia_UCI"], days_assigned={"HEMS":["monday"], "Coordis":["monday"], "Guardia_UCI":["monday"]},
    available_work_hours=1688, available_guard_hours=399)
)

workers.append(
    Worker(name="Roberto Velasco", initials="RV", birth_year=1980, category="Urgencias", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["monday", "wednesday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Romina Conti", initials="RC", birth_year=1990, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["thursday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Violeta Fariña", initials="RC", birth_year=1990, category="Planta", 
    areas=["Guardia_Urg"], days_assigned={"Guardia_Urg":["friday"]},
    available_work_hours=1688, available_guard_hours=499)
)

workers.append(
    Worker(name="Sara Gracía Gómez", initials="GaGo", birth_year=1995, category="extra", 
    areas=["Guardia_UCI", "Guardia_Urg"], days_assigned={"Guardia_Urg":["tuesday"], "Guardia_UCI":["tuesday"]},)
)

workers.append(
    Worker(name="M.M.", initials="MM", birth_year=2000, category="extra", 
    areas=["Guardia_UCI", "Guardia_Urg"])
)

workers.append(
    Worker(name="L.C.", initials="LC", birth_year=2000, category="extra", 
    areas=["Guardia_Urg"])
)

workers.append(Worker(name="Anabel Prigent", initials="AP", birth_year=2000, category="extra", 
    areas=["Guardia_UCI"], days_assigned={"Guardia_UCI":["tuesday"]}, available_work_hours=1688, available_guard_hours=499))