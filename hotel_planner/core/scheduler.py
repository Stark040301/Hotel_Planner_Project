from collections import defaultdict
from bisect import bisect_left
from datetime import timedelta

from hotel_planner.models.resource import Resource, Room, Employee, Item
from hotel_planner.models.event import Event
from hotel_planner.models.inventory import Inventory

class Scheduler:
    """Planificador de eventos.
    
    Mantiene índices en memoria (events_sorted, name_to_event, resource_index).
    Valida y programa eventos (sin mutar el inventario) y busca huecos disponibles.
    Supone nombres normalizados; Event.resources → lista de nombres.
    """
    def __init__(self, inventory: Inventory = None):
        self.inventory = inventory or Inventory()
        self.events_sorted = []           # lista ordenada por start
        self.name_to_event = {}           # name_normalized -> Event
        self.resource_index = defaultdict(list)  # resource_name -> [Event, ...]

    # Helper: normalizar nombres
    def _normalize(self, name: str) -> str:
        return name.lower().strip()

    # Helper: contar reservas para un recurso en un intervalo
    def _count_reserved(self, resource_name: str, start, end) -> int:
        normalized_name = self._normalize(resource_name)
        count = 0
        for event in self.resource_index[normalized_name]:
            latest_start = max(event.start, start)
            earliest_end = min(event.end, end)
            if (earliest_end - latest_start).total_seconds() > 0:
                count += 1
        return count

    # Comprueba si se puede programar; devuelve (True, None) o (False, motivo)
    def _can_schedule(self, event: Event):
        # ...validaciones básicas, buscar resource en inventory, usar _count_reserved...
        pass

    # Inserta evento en events_sorted manteniendo orden por start
    def _insert_event_sorted(self, event: Event):
        # ...usar bisect para encontrar índice e insertar...
        pass

    # API pública
    def add_event(self, event: Event):
        # ...usar _can_schedule, _insert_event_sorted, actualizar name_to_event y resource_index...
        pass

    def remove_event(self, event_name: str):
        # ...buscar por name_to_event, eliminar en índices y devolver True/False...
        pass

    def list_events(self):
        return list(self.events_sorted)

    def find_next_available(self, duration: timedelta, resource_names: list, start_from, window_end, step_minutes: int = 30):
        # ...bucle por candidate_start con pasos de step_minutes y usar _can_schedule en eventos temporales...
        pass
