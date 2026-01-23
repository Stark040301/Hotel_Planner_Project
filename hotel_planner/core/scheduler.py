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
    Supone nombres normalizados; Event.resources → lista de dicts {'name','quantity'}.
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
        total = 0
        for event in self.resource_index.get(normalized_name, []):
            latest_start = max(event.start, start)
            earliest_end = min(event.end, end)
            if (earliest_end - latest_start).total_seconds() > 0:
                # sumar la cantidad que ese evento solicita de este recurso
                total += event.get_resource_quantity(normalized_name)
        return total

    # Comprueba si se puede programar; devuelve (True, None) o (False, motivo)
    def _can_schedule(self, event: Event):
        # Validaciones básicas
        if event.start >= event.end:
            return (False, "El evento debe tener duración positiva")
        normalized_name = self._normalize(event.name)
        if normalized_name in self.name_to_event:
            return (False, "Ya existe un evento con ese nombre")

        # Comprobar recursos y cantidades pedidas
        for entry in event.resources:
            # entry es dict {'name', 'quantity'}
            name = self._normalize(entry.get("name"))
            qty_needed = int(entry.get("quantity", 1))

            resource_obj = self.inventory.find_by_name(name)
            if resource_obj is None:
                return (False, f"El recurso '{name}' no existe en el inventario")

            reserved = self._count_reserved(name, event.start, event.end)
            available_total = int(resource_obj.quantity)

            if reserved + qty_needed > available_total:
                available = max(0, available_total - reserved)
                return (False, f"El recurso '{name}' no tiene suficiente disponibilidad (libres: {available})")

        # TODO: validaciones adicionales (co-requisitos, exclusiones)
        return (True, None)

    # Inserta evento en events_sorted manteniendo orden por start
    def _insert_event_sorted(self, event: Event):
        starts = [e.start for e in self.events_sorted]
        idx = bisect_left(starts, event.start)
        self.events_sorted.insert(idx, event)

    # API pública
    def add_event(self, event: Event):
        ok, reason = self._can_schedule(event)
        if not ok:
            return (False, reason)

        # Insertar en lista ordenada
        self._insert_event_sorted(event)

        # Actualizar índices
        normalized_name = self._normalize(event.name)
        self.name_to_event[normalized_name] = event

        for entry in event.resources:
            rname = self._normalize(entry.get("name"))
            self.resource_index[rname].append(event)

        return (True, None)

    def remove_event(self, event_name: str):
        normalized = self._normalize(event_name)
        event = self.name_to_event.pop(normalized, None)
        if event is None:
            return False

        # Eliminar de events_sorted
        try:
            self.events_sorted.remove(event)
        except ValueError:
            pass

        # Eliminar de resource_index
        for entry in event.resources:
            rname = self._normalize(entry.get("name"))
            lst = self.resource_index.get(rname, [])
            try:
                lst.remove(event)
            except ValueError:
                pass
            if not lst:
                self.resource_index.pop(rname, None)

        return True

    def list_events(self):
        return list(self.events_sorted)

    def find_next_available(self, duration: timedelta, resource_names: list, start_from, window_end, step_minutes: int = 30):
        # Normalizar / preparar recursos (acepta strings o dicts)
        resources_template = []
        for r in resource_names:
            if isinstance(r, dict):
                name = self._normalize(r.get("name"))
                qty = int(r.get("quantity", 1))
            else:
                name = self._normalize(r)
                qty = 1
            resources_template.append({"name": name, "quantity": qty})

        step = timedelta(minutes=step_minutes)
        candidate_start = start_from

        while candidate_start + duration <= window_end:
            candidate_end = candidate_start + duration
            # crear evento provisional
            temp_event = Event("__tmp__", candidate_start, candidate_end, resources=resources_template)
            ok, _ = self._can_schedule(temp_event)
            if ok:
                return (candidate_start, candidate_end)
            candidate_start = candidate_start + step

        return None
