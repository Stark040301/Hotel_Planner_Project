import json
import os
from pathlib import Path
from collections import defaultdict
from bisect import bisect_left
from datetime import timedelta

from hotel_planner.models.resource import Resource, Room, Employee, Item, validate_resource_constraints
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

    def resource_usage_intervals(self, resource_name: str):
        """
        Devuelve una lista de segmentos donde el recurso está siendo usado.
        Cada segmento es un dict: {"start": datetime, "end": datetime, "quantity": int}
        Nota: no gestiona recurrencias; sólo eventos concretos presentes en resource_index.
        """
        norm = self._normalize(resource_name)
        events = list(self.resource_index.get(norm, []))
        points = []
        for ev in events:
            try:
                qty = int(ev.get_resource_quantity(norm))
            except Exception:
                qty = 0
            if qty <= 0:
                continue
            points.append((ev.start, qty))   # inicio: +qty
            points.append((ev.end, -qty))    # fin: -qty

        if not points:
            return []

        # ordenar; procesar cierres antes que aperturas en el mismo instante
        points.sort(key=lambda p: (p[0], 0 if p[1] < 0 else 1))

        segments = []
        curr = 0
        last_time = None
        for t, delta in points:
            if last_time is not None and t > last_time and curr > 0:
                segments.append({"start": last_time, "end": t, "quantity": curr})
            curr += delta
            last_time = t

        return segments

    def format_usage_intervals(self, resource_name: str, fmt="%d/%m/%y %H:%M"):
        """
        Devuelve una lista de strings legibles con la información de uso.
        Ej: '3 en uso (06/02/26 10:00 - 06/02/26 14:00)'
        """
        segs = self.resource_usage_intervals(resource_name)
        out = []
        for s in segs:
            try:
                start = s["start"].strftime(fmt)
                end = s["end"].strftime(fmt)
                out.append(f"{s['quantity']} en uso ({start} - {end})")
            except Exception:
                # en caso de objetos no-datetime, repr
                out.append(f"{s['quantity']} en uso ({s['start']} - {s['end']})")
        # TODO: añadir soporte para recurrencias (detectar eventos recurrentes y expandir/compactar)
        return out

    # Comprueba si se puede programar; devuelve (True, None) o (False, motivo)
    def _can_schedule(self, event: Event):
        # Validaciones básicas
        if event.start >= event.end:
            return (False, "El evento debe tener duración positiva")
        normalized_name = self._normalize(event.name)
        if normalized_name in self.name_to_event:
            return (False, "Ya existe un evento con ese nombre")

        # --- Validación de restricciones entre recursos (co-requisitos / exclusiones) ---
        try:
            requested = []
            for entry in getattr(event, "resources", []) or []:
                if isinstance(entry, dict):
                    nm = entry.get("name")
                else:
                    nm = getattr(entry, "name", None) or str(entry)
                if nm:
                    requested.append(nm)
            ok_constraints, constraint_errs = validate_resource_constraints(requested, list(self.inventory.resources))
            if not ok_constraints:
                # devolver estructura con detalles para que la UI la muestre
                return (False, {"constraint_error": constraint_errs})
        except Exception:
            # si el validador falla inesperadamente, seguimos con las validaciones normales
            pass

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

    # ----------------------------
    # Persistencia de eventos
    # ----------------------------
    def save_events(self, path):
        """
        Guarda los eventos actuales en JSON en la ruta indicada.
        Escritura atómica: escribe en un archivo temporal y luego reemplaza.
        path: str o Path
        Devuelve (True, None) o (False, "mensaje de error")
        """
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": 1,
                "events": [e.to_dict() for e in self.events_sorted]
            }
            tmp = p.with_suffix(p.suffix + ".tmp") if p.suffix else Path(str(p) + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(str(tmp), str(p))
            return (True, None)
        except Exception as exc:
            return (False, str(exc))

    def load_events(self, path, validate: bool = True):
        """
        Carga eventos desde JSON.
        - Si validate=True: intenta añadir cada evento vía add_event (aplica validaciones).
          Devuelve (True, None) si todo cargó; si hay errores devuelve (False, errores_dict).
        - Si validate=False: reconstruye índices directamente (se asume que los datos son confiables).
        path: str o Path
        """
        p = Path(path)
        if not p.exists():
            return (False, f"File not found: {p}")

        try:
            with p.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            events_data = payload.get("events", [])
        except Exception as exc:
            return (False, f"Error reading JSON: {exc}")

        if validate:
            # limpiar estado actual antes de cargar validado
            self.events_sorted = []
            self.name_to_event = {}
            self.resource_index = defaultdict(list)

            errors = {}
            for ed in events_data:
                try:
                    ev = Event.from_dict(ed)
                except Exception as exc:
                    errors[ed.get("name", "<unknown>")] = f"Invalid event data: {exc}"
                    continue
                ok, reason = self.add_event(ev)
                if not ok:
                    errors[ev.name] = reason
            if errors:
                return (False, errors)
            return (True, None)
        else:
            # reconstruir índices sin pasar por add_event
            self.events_sorted = []
            self.name_to_event = {}
            self.resource_index = defaultdict(list)

            for ed in events_data:
                ev = Event.from_dict(ed)
                # insertar ordenado
                starts = [e.start for e in self.events_sorted]
                idx = bisect_left(starts, ev.start)
                self.events_sorted.insert(idx, ev)
                self.name_to_event[self._normalize(ev.name)] = ev
                for entry in ev.resources:
                    rname = self._normalize(entry.get("name"))
                    self.resource_index[rname].append(ev)
            return (True, None)
