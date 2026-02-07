import json
from hotel_planner.models.resource import Resource, Room, Employee, Item

class Inventory:
    """
    Mantiene el registro de todos los recursos del hotel.
    Incluye habitaciones, personal y equipamiento.
    """

    TYPE_MAP = {
        "Room": Room,
        "Employee": Employee,
        "Item": Item
    }

    def __init__(self):
        self.resources = []  # lista de objetos Resource o derivados

    # ----------------------------
    # Agregar y buscar recursos
    # ----------------------------
    def add_resource(self, resource):
        """Agrega un nuevo recurso al inventario."""
        existing = self.find_by_name(resource.name)
        if existing:
            # sumar cantidades si el atributo existe
            try:
                existing.quantity = int(existing.quantity) + int(getattr(resource, "quantity", 1))
            except Exception:
                pass
            # fusionar metadatos si existen
            for attr in ("requires", "excludes", "excludes_categories"):
                if hasattr(existing, attr) and hasattr(resource, attr):
                    try:
                        getattr(existing, attr).update(getattr(resource, attr))
                    except Exception:
                        pass
        self.resources.append(resource)

    def find_by_name(self, name):
        """Busca un recurso por su nombre (case-insensitive)."""
        for r in self.resources:
            if r.name.lower() == name.lower():
                return r
        return None

    def get_resources_by_category(self, category):
        """Devuelve todos los recursos de una categoría (e.g., 'room', 'employee', 'item')."""
        return [r for r in self.resources if r.category == category]

    def get_available_resources_by_category(self, category):
        """Devuelve recursos de la categoría que estén disponibles."""
        return [r for r in self.resources if r.category == category and r.is_available]

    # ----------------------------
    # Modificar disponibilidad
    # ----------------------------
    def mark_unavailable(self, name, amount=1):
        """
        Marca una o varias unidades de un recurso como no disponibles.
        Si quantity <= 0, available se actualiza automáticamente.
        """
        r = self.find_by_name(name)
        if r and r.quantity >= amount:
            r.quantity = r.quantity - amount
            return True
        return False

    def mark_available(self, name, amount=1):
        """Aumenta la cantidad disponible de un recurso."""
        r = self.find_by_name(name)
        if r:
            r.quantity = r.quantity + amount
            return True
        return False

    # ----------------------------
    # Persistencia JSON
    # ----------------------------
    def to_dict(self):
        """Convierte el inventario a una lista de diccionarios usando to_dict() de cada recurso."""
        return [r.to_dict() for r in self.resources]

    def save_to_file(self, path):
        """Guarda el inventario en un archivo JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    def load_from_file(self, path):
        """Carga recursos desde un archivo JSON, reconstruyendo la subclase correcta."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for rdata in data:
                cls_name = rdata.get("type")
                cls = self.TYPE_MAP.get(cls_name, Resource)

                # Crear instancia según subclase
                if cls == Room:
                    r = Room(
                        rdata.get("name"),
                        capacity=rdata.get("capacity", 1),
                        room_type=rdata.get("room_type", "estándar"),
                        interior=rdata.get("interior", True)
                    )
                elif cls == Employee:
                    r = Employee(
                        rdata.get("name"),
                        role=rdata.get("role", ""),
                        shift=rdata.get("shift", "diurno")
                    )
                elif cls == Item:
                    r = Item(
                        rdata.get("name"),
                        description=rdata.get("description"),
                        quantity=rdata.get("quantity", 1)
                    )
                else:
                    r = Resource(
                        rdata.get("name"),
                        category=rdata.get("category", "item"),
                        quantity=rdata.get("quantity", 1)
                    )

                # Ajustar cantidad y disponibilidad
                r.quantity = rdata.get("quantity", getattr(r, "quantity", 1))
                r.available = rdata.get("available", r.quantity > 0)

                self.add_resource(r)

    # ----------------------------
    # Representación para debugging
    # ----------------------------
    def __repr__(self):
        return f"<Inventory: {len(self.resources)} recursos>"
