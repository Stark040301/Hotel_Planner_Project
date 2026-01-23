from datetime import datetime, timedelta
from dateutil.parser import parse

class Event:
    """
    Representa un evento que ocurre en el hotel.
    Incluye nombre, intervalo de tiempo, recursos asignados y recurrencia opcional.
    """

    def __init__(self, name: str, start, end, resources: list = None, recurrence: str = None):
        if not name or not isinstance(name, str):
            raise ValueError("El nombre del evento debe ser una cadena no vacía.")
        
        # Convertir start y end a datetime si vienen como string
        self.start = parse(start) if isinstance(start, str) else start
        self.end = parse(end) if isinstance(end, str) else end

        if self.end <= self.start:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")

        self.name = name
        self.recurrence = recurrence  # Por ejemplo: "daily", "weekly", etc.

        # Normalizar y almacenar recursos como lista de dicts {name, quantity}
        self.resources = []
        if resources:
            for r in resources:
                # r puede ser: objeto Resource (tiene .name), string, o dict {'name', 'quantity'}
                if hasattr(r, "name"):
                    rname = str(r.name)
                    qty = getattr(r, "quantity", 1)
                elif isinstance(r, dict):
                    rname = str(r.get("name"))
                    qty = int(r.get("quantity", 1))
                else:
                    rname = str(r)
                    qty = 1
                self.add_resource(rname, qty)

    def __repr__(self):
        res_summary = ", ".join(f"{r['name']}({r['quantity']})" for r in self.resources)
        return f"<Event {self.name} ({self.start} - {self.end}) resources: [{res_summary}] recurrence: {self.recurrence}>"

    # ----------------------------
    # Métodos útiles
    # ----------------------------
    def duration(self):
        """Devuelve la duración del evento como timedelta."""
        return self.end - self.start

    def conflicts_with(self, other_event):
        """
        Verifica si hay solapamiento de horarios con otro evento.
        Devuelve True si hay conflicto, False si no.
        """
        latest_start = max(self.start, other_event.start)
        earliest_end = min(self.end, other_event.end)
        overlap = (earliest_end - latest_start).total_seconds()
        return overlap > 0

    # ----------------------------
    # Gestión de recursos con cantidad
    # ----------------------------
    def _normalize_name(self, name):
        return str(name).lower().strip()

    def add_resource(self, resource, quantity: int = 1):
        """
        Agrega o incrementa la cantidad de un recurso en el evento.
        resource: Resource object, string (nombre) o dict {'name':..., 'quantity':...}
        """
        if hasattr(resource, "name"):
            name = resource.name
        elif isinstance(resource, dict):
            name = resource.get("name")
            quantity = int(resource.get("quantity", quantity))
        else:
            name = resource
        name = self._normalize_name(name)
        if quantity < 1:
            raise ValueError("quantity debe ser >= 1")

        for entry in self.resources:
            if entry["name"] == name:
                entry["quantity"] += int(quantity)
                return
        self.resources.append({"name": name, "quantity": int(quantity)})

    def remove_resource(self, name, quantity: int = None):
        """
        Reduce o elimina un recurso del evento.
        Si quantity es None elimina la entrada por completo.
        Si quantity especificado, resta y elimina si llega a 0.
        """
        name = self._normalize_name(name)
        for entry in list(self.resources):
            if entry["name"] == name:
                if quantity is None or quantity >= entry["quantity"]:
                    self.resources.remove(entry)
                else:
                    entry["quantity"] -= int(quantity)
                return

    def get_resource_quantity(self, name) -> int:
        """Devuelve la cantidad solicitada de un recurso en este evento (0 si no existe)."""
        name = self._normalize_name(name)
        for entry in self.resources:
            if entry["name"] == name:
                return int(entry["quantity"])
        return 0

    def to_dict(self):
        """Convierte el evento a diccionario serializable (JSON)."""
        return {
            "name": self.name,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "resources": [{"name": r["name"], "quantity": r["quantity"]} for r in self.resources],
            "recurrence": self.recurrence
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Reconstruye Event desde dict (útil al cargar)."""
        resources = data.get("resources", [])
        return cls(
            name=data["name"],
            start=data["start"],
            end=data["end"],
            resources=resources,
            recurrence=data.get("recurrence")
        )
