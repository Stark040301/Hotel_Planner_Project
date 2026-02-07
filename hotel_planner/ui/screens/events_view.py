import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import customtkinter as ctk
from typing import Optional, Iterable
from datetime import datetime, timedelta
from pathlib import Path
import json
import os
import tkinter.messagebox as msg

class PlannedEventsView(ctk.CTkFrame):
    """Pantalla para listar y gestionar eventos planificados en una tabla."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._min_col_widths = {}
        self._build_ui()
        # react when events.json is changed by other views
        try:
            root = self.winfo_toplevel()
            root.bind("<<EventsChanged>>", lambda ev: self.refresh())
        except Exception:
            pass

    def _build_ui(self):
        # header row: title left, actions right
        header_row = ctk.CTkFrame(self)
        header_row.pack(fill="x", padx=16, pady=12)
        self.title = ctk.CTkLabel(header_row, text="Eventos Planificados", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(side="left")
        del_btn = ctk.CTkButton(header_row, text="Eliminar evento", command=self._delete_selected_event, width=160)
        del_btn.pack(side="right")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=12, pady=8)
        columns = ("name", "start", "end", "duration", "resources", "recurrence")
        headings = ("Nombre", "Comienza", "Termina", "Duración", "Recursos", "Recurrencia")
        col_widths = (240, 160, 160, 100, 360, 120)

        self.tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse", height=14)
        for col, head, w in zip(columns, headings, col_widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # store minimum widths
        self._min_col_widths = {col: int(w) for col, w in zip(columns, col_widths)}

        # double click to open details (hook placeholder)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        iid = self.tree.focus()
        if not iid:
            return
        vals = self.tree.item(iid, "values")
        # placeholder: open a detail dialog or call controller
        print("DEBUG: event double-click:", vals)

    def _fmt_dt(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value).strftime("%d/%m/%y %H:%M")
            except Exception:
                return str(value)
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%y %H:%M")
        # assume string
        return str(value)

    def _fmt_duration(self, start, end) -> str:
        try:
            if isinstance(start, str):
                try:
                    start = datetime.fromisoformat(start)
                except Exception:
                    start = None
            if isinstance(end, str):
                try:
                    end = datetime.fromisoformat(end)
                except Exception:
                    end = None
            if isinstance(start, datetime) and isinstance(end, datetime):
                delta: timedelta = end - start
                total_min = int(delta.total_seconds() // 60)
                h = total_min // 60
                m = total_min % 60
                if h:
                    return f"{h}h {m}m"
                return f"{m}m"
        except Exception:
            pass
        return ""

    def _fmt_resources(self, resources) -> str:
        if not resources:
            return ""
        # accept list of names or list of dicts with 'name'
        try:
            if isinstance(resources, (list, tuple)):
                out = []
                for r in resources:
                    if isinstance(r, str):
                        out.append(r)
                    elif isinstance(r, dict):
                        out.append(r.get("name") or r.get("resource") or str(r))
                    else:
                        out.append(getattr(r, "name", str(r)))
                return ", ".join(out)
        except Exception:
            pass
        return str(resources)

    def on_show(self):
        """Called when this view is raised; refresh table contents."""
        self.refresh()

    def refresh(self):
        # clear
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        events = []
        if self.controller and hasattr(self.controller, "list_events"):
            try:
                events = list(self.controller.list_events())
            except Exception:
                events = []

        for ev in events:
            # ev may be dict-like or object
            try:
                name = ev.get("name") if isinstance(ev, dict) else getattr(ev, "name", "")
                start = ev.get("start") if isinstance(ev, dict) else getattr(ev, "start", None)
                end = ev.get("end") if isinstance(ev, dict) else getattr(ev, "end", None)
                recurrence = ev.get("recurrence") if isinstance(ev, dict) else getattr(ev, "recurrence", "")
                resources = ev.get("resources") if isinstance(ev, dict) else getattr(ev, "resources", None)
            except Exception:
                # fallback minimal extraction
                name = getattr(ev, "name", str(ev))
                start = getattr(ev, "start", None)
                end = getattr(ev, "end", None)
                recurrence = getattr(ev, "recurrence", "")
                resources = getattr(ev, "resources", None)

            vals = (
                name,
                self._fmt_dt(start),
                self._fmt_dt(end),
                self._fmt_duration(start, end),
                self._fmt_resources(resources),
                str(recurrence or ""),
            )
            self.tree.insert("", "end", values=vals)

        # autosize columns based on contents
        try:
            self._autosize_tree(self.tree, padding=12, max_width=1200)
        except Exception:
            pass

        # debug
        try:
            print("DEBUG PlannedEventsView.refresh loaded:", len(self.tree.get_children()), "events")
        except Exception:
            pass

    def _autosize_tree(self, tree: ttk.Treeview, padding: int = 12, max_width: int = 1200):
        """Adjust columns to fit their longest content, respecting minimum widths."""
        try:
            f = tkfont.Font(font=tree.cget("font")) if tree.cget("font") else tkfont.Font()
        except Exception:
            f = tkfont.Font()

        cols = tree["columns"]
        for col in cols:
            hdr = tree.heading(col).get("text", "") if tree.heading(col) else str(col)
            max_px = f.measure(hdr)
            for iid in tree.get_children():
                cell = tree.set(iid, col) or ""
                if cell:
                    w = f.measure(str(cell))
                    if w > max_px:
                        max_px = w
            desired = max_px + padding
            min_w = int(self._min_col_widths.get(col, 80)) if isinstance(self._min_col_widths, dict) else 80
            final_w = max(min_w, desired)
            final_w = min(final_w, max_width)
            try:
                tree.column(col, width=final_w)
            except Exception:
                pass

    def _get_selected_event_ident(self):
        """Return (iid, visible_name, visible_start) or (None, None, None)."""
        try:
            iid = self.tree.focus() or (self.tree.selection()[0] if self.tree.selection() else None)
            if not iid:
                return None, None, None
            vals = self.tree.item(iid, "values") or ()
            name = vals[0] if len(vals) > 0 else None
            start = vals[1] if len(vals) > 1 else None
            return iid, name, start
        except Exception:
            return None, None, None

    def _serialize_event(self, ev):
        """Turn event object/dict into JSON-serializable dict (convert datetimes to ISO)."""
        if ev is None:
            return {}
        if isinstance(ev, dict):
            out = dict(ev)
        else:
            try:
                out = dict(getattr(ev, "__dict__", {})) or {}
            except Exception:
                out = {}
            # fallback: try extracting common attrs
            for a in ("name", "start", "end", "resources", "recurrence", "notes"):
                if a not in out and hasattr(ev, a):
                    out[a] = getattr(ev, a)
        # normalize datetimes
        for k in ("start", "end"):
            if k in out and isinstance(out[k], datetime):
                out[k] = out[k].isoformat()
        return out

    def _delete_selected_event(self):
        iid, vis_name, vis_start = self._get_selected_event_ident()
        if vis_name is None:
            msg.showwarning("Seleccionar", "Selecciona un evento primero.")
            return

        if not msg.askyesno("Confirmar eliminación", f"¿Eliminar el evento '{vis_name}'?"):
            return

        # try to find the matching event in controller list (prefer exact match by name+start formatted)
        existing = []
        try:
            if self.controller and hasattr(self.controller, "list_events"):
                existing = list(self.controller.list_events()) or []
        except Exception:
            existing = []

        # find candidate index
        match_idx = None
        for idx, ev in enumerate(existing):
            try:
                ev_name = ev.get("name") if isinstance(ev, dict) else getattr(ev, "name", "")
                ev_start = ev.get("start") if isinstance(ev, dict) else getattr(ev, "start", None)
                if self._fmt_dt(ev_start) == (vis_start or "") and (str(ev_name).strip().lower() == str(vis_name).strip().lower()):
                    match_idx = idx
                    break
            except Exception:
                continue

        # fallback: match by name only (first)
        if match_idx is None:
            for idx, ev in enumerate(existing):
                try:
                    ev_name = ev.get("name") if isinstance(ev, dict) else getattr(ev, "name", "")
                    if str(ev_name).strip().lower() == str(vis_name).strip().lower():
                        match_idx = idx
                        break
                except Exception:
                    continue

        if match_idx is None:
            msg.showwarning("No encontrado", f"No se encontró el evento '{vis_name}' en memoria.")
            return

        # remove from list and persist to combined file
        try:
            removed = existing.pop(match_idx)
            # build serializable list
            serializable = [self._serialize_event(e) for e in existing]
            COMBINED = Path.home() / ".hotel_planner" / "data.json"
            try:
                payload = json.loads(COMBINED.read_text(encoding="utf-8")) if COMBINED.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
            except Exception:
                payload = {"version": 1, "inventory": {"resources": []}, "events": []}

            payload["events"] = serializable
            tmp = COMBINED.with_name(COMBINED.name + ".tmp")
            COMBINED.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(str(tmp), str(COMBINED))

            # update controller/scheduler in-memory
            try:
                if self.controller and hasattr(self.controller, "load_events"):
                    try:
                        self.controller.load_events(serializable)
                    except Exception:
                        pass
                elif self.controller and hasattr(self.controller, "scheduler") and hasattr(self.controller.scheduler, "load_events_from_list"):
                    try:
                        self.controller.scheduler.load_events_from_list(serializable)
                    except Exception:
                        pass
            except Exception:
                pass

            # notify UI and refresh
            try:
                root = self.winfo_toplevel()
                root.event_generate("<<EventsChanged>>", when="tail")
            except Exception:
                pass

            msg.showinfo("Ok", f"Evento '{vis_name}' eliminado.")
            self.refresh()
            return
        except Exception as e:
            msg.showerror("Error", f"No se pudo eliminar evento: {e}")