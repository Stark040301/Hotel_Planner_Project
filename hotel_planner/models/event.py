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
        self.resources = resources or []  # Lista de objetos Resource
        self.recurrence = recurrence  # Por ejemplo: "daily", "weekly", etc.

    def __repr__(self):
        return f"<Event {self.name} ({self.start} - {self.end}) Recurrence: {self.recurrence}>"

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

    def add_resource(self, resource):
        """Agrega un recurso (objeto Resource) al evento."""
        if resource not in self.resources:
            self.resources.append(resource)

    def remove_resource(self, resource):
        """Elimina un recurso del evento."""
        if resource in self.resources:
            self.resources.remove(resource)

    def to_dict(self):
        """Convierte el evento a diccionario serializable (JSON)."""
        return {
            "name": self.name,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "resources": [r.name for r in self.resources],
            "recurrence": self.recurrence
        }
