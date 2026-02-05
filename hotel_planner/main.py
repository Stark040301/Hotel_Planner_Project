from pathlib import Path
from hotel_planner.models.inventory import Inventory
from hotel_planner.models.resource import Room, Item, Employee, Resource
from hotel_planner.models.event import Event
from hotel_planner.core.scheduler import Scheduler

def main():
    project_dir = Path(__file__).resolve().parent
    sample_path = project_dir / "sample_inventory.json"
    events_path = project_dir / "events.json"

    # Cargar o crear inventario de ejemplo
    inv = Inventory()
    if sample_path.exists():
        inv.load_from_file(sample_path)
        print(f"Cargado inventario desde: {sample_path}")
    else:
        inv.add_resource(Room("Sala Grande", capacity=100, room_type="salón", interior=True))
        inv.add_resource(Item("Proyector", description="Full HD, HDMI", quantity=3))
        inv.add_resource(Employee("Juan Pérez", role="Técnico AV", shift="diurno"))
        inv.save_to_file(sample_path)
        print(f"Inventario creado y guardado en: {sample_path}")

    print("\nInventario actual:")
    for r in inv.resources:
        print(" -", r, "-", r.to_dict())

    # Instanciar scheduler con el inventario
    sched = Scheduler(inv)

    # Intentar cargar eventos guardados (validate=True para aplicar reglas)
    if events_path.exists():
        ok, info = sched.load_events(events_path, validate=True)
        if ok:
            print(f"\nEventos cargados desde: {events_path}")
        else:
            print(f"\nAl cargar events.json hubo errores: {info}")
    else:
        print("\nNo se encontró events.json — procediendo sin eventos cargados.")


    # Mostrar eventos programados
    print("\nEventos programados:")
    for ev in sched.list_events():
        print(" -", ev)

    # Guardar eventos actuales
    ok, info = sched.save_events(events_path)
    if ok:
        print(f"\nEventos guardados en: {events_path}")
    else:
        print(f"\nError al guardar eventos: {info}")

    # Buscar el primer hueco disponible para 1h en la tarde
    from datetime import datetime, timedelta
    start_from = datetime(2026, 1, 10, 8, 0)
    window_end = datetime(2026, 1, 10, 18, 0)
    duration = timedelta(hours=1)
    slot = sched.find_next_available(duration, [{"name": "Sala Grande", "quantity": 1}], start_from, window_end, step_minutes=30)
    if slot:
        print(f"\nPrimer hueco disponible para 1h en 'Sala Grande': {slot[0]} - {slot[1]}")
    else:
        print("\nNo se encontró hueco disponible en la ventana indicada.")

def run_constraints_tests():
    """Ejecuta una serie de checks equivalentes a test_constraints.py e imprime resultados."""
    from datetime import datetime

    def report(name, ok, reason=None):
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        if reason is not None and not ok:
            print("  Reason:", reason)

    # 1) corequisite success
    inv = Inventory()
    inv.add_resource(Item("Cámara RED", quantity=1, requires=["Técnico de Cámara Certificado"]))
    inv.add_resource(Employee("Técnico de Cámara Certificado", role="cámara"))
    sched = Scheduler(inv)
    e = Event("Rodaje", datetime(2026,2,1,9,0), datetime(2026,2,1,12,0),
              resources=[{"name":"Cámara RED","quantity":1}, {"name":"Técnico de Cámara Certificado","quantity":1}])
    ok, reason = sched.add_event(e)
    report("corequisite_success", ok, reason)

    # 2) corequisite missing fails
    inv = Inventory()
    inv.add_resource(Item("Cámara RED", quantity=1, requires=["Técnico de Cámara Certificado"]))
    sched = Scheduler(inv)
    e = Event("RodajeSinTec", datetime(2026,2,2,9,0), datetime(2026,2,2,11,0),
              resources=[{"name":"Cámara RED","quantity":1}])
    ok, reason = sched.add_event(e)
    report("corequisite_missing_fails", ok, reason)

    # 3) mutual exclusion by name fails
    inv = Inventory()
    inv.add_resource(Item("Mechero Bunsen", quantity=1, excludes=["Contenedor de Éter"]))
    inv.add_resource(Item("Contenedor de Éter", quantity=1, excludes=["Mechero Bunsen"]))
    sched = Scheduler(inv)
    e = Event("Experimento Peligroso", datetime(2026,3,3,10,0), datetime(2026,3,3,12,0),
              resources=[{"name":"Mechero Bunsen","quantity":1}, {"name":"Contenedor de Éter","quantity":1}])
    ok, reason = sched.add_event(e)
    report("mutual_exclusion_by_name_fails", ok, reason)

    # 4) mutual exclusion by category fails
    inv = Inventory()
    inv.add_resource(Resource("Sala de Grabación A", category="room", excludes_categories=["item"]))
    inv.add_resource(Item("Batería Acústica", quantity=1))
    sched = Scheduler(inv)
    e = Event("Sesión", datetime(2026,4,5,14,0), datetime(2026,4,5,16,0),
              resources=[{"name":"Sala de Grabación A","quantity":1}, {"name":"Batería Acústica","quantity":1}])
    ok, reason = sched.add_event(e)
    report("mutual_exclusion_by_category_fails", ok, reason)

    # 5) complex requires multiple items success
    inv = Inventory()
    inv.add_resource(Item("Cirugía Robótica", quantity=1,
                          requires=["Consola Da Vinci", "Cirujano Certificado en Da Vinci"]))
    inv.add_resource(Item("Consola Da Vinci", quantity=1))
    inv.add_resource(Employee("Cirujano Certificado en Da Vinci", role="cirujano"))
    sched = Scheduler(inv)
    e = Event("Cirugía Especial", datetime(2026,5,1,8,0), datetime(2026,5,1,12,0),
              resources=[
                  {"name":"Cirugía Robótica","quantity":1},
                  {"name":"Consola Da Vinci","quantity":1},
                  {"name":"Cirujano Certificado en Da Vinci","quantity":1},
              ])
    ok, reason = sched.add_event(e)
    report("complex_requires_multiple_items_success", ok, reason)

if __name__ == "__main__":
    main()
    print("\n--- Ejecutando tests de restricciones (imprimible) ---")
    run_constraints_tests()