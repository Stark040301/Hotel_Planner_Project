from pathlib import Path
from hotel_planner.models.inventory import Inventory
from hotel_planner.models.resource import Room, Item, Employee

def main():
    project_dir = Path(__file__).resolve().parent
    sample_path = project_dir / "sample_inventory.json"

    inv = Inventory()
    # Recursos de ejemplo
    inv.add_resource(Room("Sala Grande", capacity=100, room_type="salón", interior=True))
    inv.add_resource(Item("Proyector", description="Full HD, HDMI", quantity=3))
    inv.add_resource(Employee("Juan Pérez", role="Técnico AV", shift="diurno"))

    print("Inventario inicial:")
    for r in inv.resources:
        print(" -", r, "-", r.to_dict())

    # Guardar
    inv.save_to_file(sample_path)
    print(f"\nInventario guardado en: {sample_path}")

    # Cargar en una nueva instancia para verificar persistencia
    inv2 = Inventory()
    inv2.load_from_file(sample_path)
    print("\nInventario cargado:")
    for r in inv2.resources:
        print(" -", r, "-", r.to_dict())

if __name__ == "__main__":
    main()