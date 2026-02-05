from pathlib import Path
from datetime import timedelta, datetime
from typing import Optional, Tuple, List, Union
import threading
import json
import os
import queue
from collections import defaultdict
from bisect import bisect_left

from hotel_planner.core.scheduler import Scheduler
from hotel_planner.models.event import Event


class Controller:
    """
    Adaptador entre la UI y el backend.

    Provee métodos sencillos y consistentes que la UI puede llamar:
    - list_resources() -> lista de dicts serializables
    - list_events() -> lista de dicts serializables
    - add_event(data) -> (ok: bool, reason: Optional[str])
    - remove_event(name) -> (ok: bool, reason: Optional[str])
    - find_next_available(duration, resources, start_from, window_end, step_minutes) -> (start,end) | None
    - save_state(path) / load_state(path, validate=True)
    """

    def __init__(self, scheduler: Scheduler, events_path: Optional[Union[str, Path]] = None):
        self.scheduler = scheduler
        self.events_path = Path(events_path) if events_path else None
        self._lock = threading.Lock()

    def set_events_path(self, path: Union[str, Path]):
        self.events_path = Path(path)
        return self.events_path

    # -----------------------
    # Read helpers (UI <--- backend)
    # -----------------------
    def list_resources(self) -> List[dict]:
        with self._lock:
            return [r.to_dict() for r in self.scheduler.inventory.resources]

    def list_events(self) -> List[dict]:
        with self._lock:
            return [e.to_dict() for e in self.scheduler.list_events()]

    # -----------------------
    # Mutation helpers (UI ---> backend)
    # -----------------------
    def add_event(self, data: Union[Event, dict]) -> Tuple[bool, Optional[str]]:
        """
        data: Event instance or dict compatible with Event.from_dict()
        Returns (True, None) on success, (False, reason) on failure.
        """
        try:
            ev = data if isinstance(data, Event) else Event.from_dict(data)
        except Exception as exc:
            return (False, f"Invalid event data: {exc}")

        with self._lock:
            ok, reason = self.scheduler.add_event(ev)
        return (ok, reason)

    def remove_event(self, name: str) -> Tuple[bool, Optional[str]]:
        with self._lock:
            ok = self.scheduler.remove_event(name)
        if ok:
            return (True, None)
        return (False, f"Evento '{name}' no encontrado")

    def find_next_available(
        self,
        duration: Union[int, float, timedelta],
        resources: List[Union[str, dict]],
        start_from: datetime,
        window_end: datetime,
        step_minutes: int = 30,
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        duration: timedelta or number of minutes
        resources: list of names or dicts {'name', 'quantity'}
        """
        if not isinstance(duration, timedelta):
            duration = timedelta(minutes=float(duration))
        # normalize resources format for scheduler (list of dicts with name/quantity)
        normalized = []
        for r in resources:
            if isinstance(r, dict):
                normalized.append({"name": r.get("name"), "quantity": int(r.get("quantity", 1))})
            else:
                normalized.append({"name": r, "quantity": 1})

        if start_from is None or window_end is None:
            return None
        if start_from >= window_end:
            return None
        with self._lock:
            return self.scheduler.find_next_available(duration, normalized, start_from, window_end, step_minutes=step_minutes)

    # -----------------------
    # Persistence helpersI/O 
    # -----------------------
    def save_state(self, path: Optional[Union[str, Path]] = None) -> Tuple[bool, Optional[str]]:
        """
        Snapshot events under lock, then write JSON to disk outside the lock (avoid blocking UI/other threads).
        """
        p = Path(path) if path else self.events_path
        if p is None:
            return (False, "No events_path configured")

        # snapshot under lock
        with self._lock:
            events_snapshot = [e.to_dict() for e in self.scheduler.list_events()]

        # perform I/O outside lock
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(p.suffix + ".tmp") if p.suffix else Path(str(p) + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump({"version": 1, "events": events_snapshot}, f, indent=2, ensure_ascii=False)
            os.replace(str(tmp), str(p))
            return (True, None)
        except Exception as exc:
            return (False, str(exc))

    def load_state(self, path: Optional[Union[str, Path]] = None, validate: bool = True) -> Tuple[bool, Optional[Union[None, dict]]]:
        """
        Read JSON from disk (I/O) first, then apply to scheduler under lock.
        If validate=True each event is added via add_event (applies validations).
        If validate=False the scheduler indices are reconstructed atomically.
        """
        p = Path(path) if path else self.events_path
        if p is None:
            return (False, "No events_path configured")
        if not p.exists():
            return (False, f"File not found: {p}")

        # Read file (I/O) outside lock
        try:
            with p.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            events_data = payload.get("events", [])
        except Exception as exc:
            return (False, f"Error reading JSON: {exc}")

        if validate:
            errors = {}
            for ed in events_data:
                try:
                    ev = Event.from_dict(ed)
                except Exception as exc:
                    errors[ed.get("name", "<unknown>")] = f"Invalid event data: {exc}"
                    continue
                ok, reason = self.add_event(ev)  # add_event uses the lock
                if not ok:
                    errors[ev.name] = reason
            if errors:
                return (False, errors)
            return (True, None)
        else:
            # reconstruct indices atomically under lock
            with self._lock:
                self.scheduler.events_sorted = []
                self.scheduler.name_to_event = {}
                self.scheduler.resource_index = defaultdict(list)
                for ed in events_data:
                    ev = Event.from_dict(ed)
                    starts = [e.start for e in self.scheduler.events_sorted]
                    idx = bisect_left(starts, ev.start)
                    self.scheduler.events_sorted.insert(idx, ev)
                    self.scheduler.name_to_event[self.scheduler._normalize(ev.name)] = ev
                    for entry in ev.resources:
                        rname = self.scheduler._normalize(entry.get("name"))
                        self.scheduler.resource_index[rname].append(ev)
            return (True, None)

    # -----------------------
    # Async helpers for UI (worker threads + result queue)
    # -----------------------
    def save_state_async(self, result_q: queue.Queue, path: Optional[Union[str, Path]] = None):
        """
        Launch save_state in a background thread. Puts tuple ("save_done", ok, info) in result_q.
        """
        def worker():
            ok, info = self.save_state(path)
            result_q.put(("save_done", ok, info))
        threading.Thread(target=worker, daemon=True).start()

    def load_state_async(self, result_q: queue.Queue, path: Optional[Union[str, Path]] = None, validate: bool = True):
        """
        Launch load_state in a background thread. Puts tuple ("load_done", ok, info) in result_q.
        """
        def worker():
            ok, info = self.load_state(path, validate=validate)
            result_q.put(("load_done", ok, info))
        threading.Thread(target=worker, daemon=True).start()