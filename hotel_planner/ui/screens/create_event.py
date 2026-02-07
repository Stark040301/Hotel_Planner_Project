import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msg
from datetime import datetime
import customtkinter as ctk
from typing import Optional, List, Dict
from pathlib import Path
import json
import os
from hotel_planner.models import event_store as ev_store

class ManageEventsView(ctk.CTkFrame):
    """Pantalla para crear eventos (formulario)."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._resource_rows = []
        self._resource_names_cache: List[str] = []
        self._build_ui()

    def _build_ui(self):
        padx = 12
        pady = 8
        header = ctk.CTkLabel(self, text="Crear Evento", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(anchor="nw", padx=padx, pady=(12, 6))

        frm = ctk.CTkFrame(self)
        frm.pack(fill="x", padx=padx, pady=(0,8))

        # Nombre
        ctk.CTkLabel(frm, text="Nombre").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.name_var = tk.StringVar()
        ctk.CTkEntry(frm, textvariable=self.name_var, width=480).grid(row=0, column=1, columnspan=3, sticky="w", padx=6)

        # Start / End
        ctk.CTkLabel(frm, text="Comienza (ISO YYYY-MM-DDTHH:MM)").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.start_var = tk.StringVar()
        e1 = ctk.CTkEntry(frm, textvariable=self.start_var, width=240)
        e1.grid(row=1, column=1, sticky="w", padx=6)

        ctk.CTkLabel(frm, text="Termina (ISO YYYY-MM-DDTHH:MM)").grid(row=1, column=2, sticky="w", padx=6)
        self.end_var = tk.StringVar()
        e2 = ctk.CTkEntry(frm, textvariable=self.end_var, width=240)
        e2.grid(row=1, column=3, sticky="w", padx=6)

        # duración auto
        self.duration_lbl = ctk.CTkLabel(frm, text="Duración: --")
        self.duration_lbl.grid(row=2, column=1, sticky="w", padx=6, pady=(0,6))
        # bind changes to recompute duration
        self.start_var.trace_add("write", lambda *_: self._update_duration())
        self.end_var.trace_add("write", lambda *_: self._update_duration())

        # Resources area
        ctk.CTkLabel(self, text="Recursos (añadir filas)").pack(anchor="nw", padx=padx, pady=(6,2))
        rframe = ctk.CTkFrame(self)
        rframe.pack(fill="both", expand=False, padx=padx, pady=(0,8))
        self._resources_container = tk.Frame(rframe)
        self._resources_container.pack(fill="x", padx=6, pady=6)

        btn_row = ctk.CTkFrame(rframe)
        btn_row.pack(fill="x", padx=6)
        add_btn = ctk.CTkButton(btn_row, text="Añadir recurso", command=self._add_resource_row, width=140)
        add_btn.pack(side="left", padx=(0,6))
        scan_btn = ctk.CTkButton(btn_row, text="Recargar recursos", command=self._refresh_resource_names, width=160)
        scan_btn.pack(side="left")

        # Recurrence & notes
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=padx, pady=(6,12))
        ctk.CTkLabel(bottom, text="Recurrencia").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.recur_var = tk.StringVar(value="none")
        recur_cb = ttk.Combobox(bottom, textvariable=self.recur_var, values=["none", "daily", "weekly", "monthly", "seasonal", "custom"], state="readonly", width=18)
        recur_cb.grid(row=0, column=1, sticky="w", padx=6)

        ctk.CTkLabel(bottom, text="Notas").grid(row=1, column=0, sticky="nw", padx=6, pady=6)
        self.notes_txt = tk.Text(bottom, height=4, width=60)
        self.notes_txt.grid(row=1, column=1, columnspan=3, sticky="w", padx=6)

        # buttons
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=padx, pady=(0,12))
        save_btn = ctk.CTkButton(actions, text="Guardar evento", command=self._save_event, width=160)
        save_btn.pack(side="right", padx=6)
        cancel_btn = ctk.CTkButton(actions, text="Cancelar", command=self._clear_form, fg_color="#999999", width=120)
        cancel_btn.pack(side="right", padx=6)

        # initial population of resources
        self._refresh_resource_names()
        # add one empty row by default
        self._add_resource_row()

    def _clear_form(self):
        self.name_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self._update_duration()
        for row in list(self._resource_rows):
            self._remove_resource_row(row)
        self._add_resource_row()
        self.recur_var.set("none")
        self.notes_txt.delete("1.0", "end")

    def _refresh_resource_names(self):
        # try to get canonical resource names from controller
        names = []
        try:
            if self.controller and hasattr(self.controller, "list_resources"):
                res = list(self.controller.list_resources())
                for r in res:
                    # r may be dict or object
                    if isinstance(r, dict):
                        names.append(r.get("name"))
                    else:
                        names.append(getattr(r, "name", None))
            names = [n for n in names if n]
        except Exception:
            names = []
        self._resource_names_cache = sorted(set(names))
        # update existing comboboxes
        for row in list(self._resource_rows):
            combo = row["combo"]
            combo["values"] = self._resource_names_cache

    def _add_resource_row(self, prefill: Dict = None):
        """Añade una fila con Combobox(resource) + Spinbox(cantidad) + remove button."""
        row_frm = tk.Frame(self._resources_container)
        row_frm.pack(fill="x", pady=4)
        combo = ttk.Combobox(row_frm, values=self._resource_names_cache, width=48)
        combo.pack(side="left", padx=(0,6))
        qty_var = tk.IntVar(value=1)
        qty_spin = tk.Spinbox(row_frm, from_=1, to=999, textvariable=qty_var, width=6)
        qty_spin.pack(side="left", padx=(0,6))
        rem_btn = ctk.CTkButton(row_frm, text="Quitar", width=80, command=lambda: self._remove_resource_row(row))
        rem_btn.pack(side="left", padx=(6,0))

        row = {"frame": row_frm, "combo": combo, "qty": qty_var, "spin": qty_spin, "remove": rem_btn}
        if prefill:
            combo.set(prefill.get("name", ""))
            qty_var.set(prefill.get("quantity", 1))
        self._resource_rows.append(row)

    def _remove_resource_row(self, row):
        try:
            self._resource_rows.remove(row)
        except ValueError:
            pass
        try:
            row["frame"].destroy()
        except Exception:
            pass

    def _update_duration(self):
        s = self.start_var.get().strip()
        e = self.end_var.get().strip()
        if not s or not e:
            self.duration_lbl.configure(text="Duración: --")
            return
        try:
            st = datetime.fromisoformat(s)
            ed = datetime.fromisoformat(e)
            if ed > st:
                delta = ed - st
                mins = int(delta.total_seconds() // 60)
                h = mins // 60
                m = mins % 60
                txt = f"{h}h {m}m" if h else f"{m}m"
                self.duration_lbl.configure(text=f"Duración: {txt}")
                return
        except Exception:
            pass
        self.duration_lbl.configure(text="Duración: inválida")

    def _gather_resources(self) -> List[Dict]:
        out = []
        for r in self._resource_rows:
            name = r["combo"].get().strip()
            if not name:
                continue
            qty = int(r["qty"].get()) if r["qty"].get() else 1
            out.append({"name": name, "quantity": qty})
        return out

    def _validate_iso(self, s: str) -> bool:
        try:
            datetime.fromisoformat(s)
            return True
        except Exception:
            return False

    def _save_event(self):
        name = self.name_var.get().strip()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()
        recurrence = self.recur_var.get() or None
        notes = self.notes_txt.get("1.0", "end").strip()
        resources = self._gather_resources()

        # basic validation
        if not name:
            msg.showerror("Error", "El evento necesita un nombre.")
            return
        if not (self._validate_iso(start) and self._validate_iso(end)):
            msg.showerror("Error", "Start / End deben estar en formato ISO: YYYY-MM-DDTHH:MM")
            return
        st = datetime.fromisoformat(start)
        ed = datetime.fromisoformat(end)
        if ed <= st:
            msg.showerror("Error", "La fecha de fin debe ser posterior a la de inicio.")
            return
        if not resources:
            if not msg.askyesno("Confirmar", "No ha añadido recursos. ¿Desea crear el evento igualmente?"):
                return

        event = {
            "name": name,
            "start": start,
            "end": end,
            "resources": resources,
            "recurrence": recurrence,
            "notes": notes,
        }

        saved = False
        save_errors = None

        try:
            existing = []
            if self.controller and hasattr(self.controller, "list_events"):
                existing = list(self.controller.list_events()) or []
            existing.append(event)

            # prefer controller.load_events if available
            if self.controller and hasattr(self.controller, "load_events"):
                try:
                    res = self.controller.load_events(existing)
                    # controller may return (ok, info) or bool/None
                    if isinstance(res, tuple):
                        ok = bool(res[0])
                        if not ok:
                            save_errors = res[1] if len(res) > 1 else "Error desconocido"
                            saved = False
                        else:
                            saved = True
                    else:
                        # assume success if no explicit False/exception
                        saved = True
                except Exception as e:
                    saved = False
                    save_errors = str(e)

                # if controller accepted in-memory, persist to combined file
                if saved:
                    try:
                        COMBINED = Path.home() / ".hotel_planner" / "data.json"
                        try:
                            payload = json.loads(COMBINED.read_text(encoding="utf-8")) if COMBINED.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
                        except Exception:
                            payload = {"version": 1, "inventory": {"resources": []}, "events": []}
                        payload["events"] = existing
                        tmp = COMBINED.with_name(COMBINED.name + ".tmp")
                        COMBINED.parent.mkdir(parents=True, exist_ok=True)
                        with tmp.open("w", encoding="utf-8") as f:
                            json.dump(payload, f, ensure_ascii=False, indent=2)
                        os.replace(str(tmp), str(COMBINED))
                        try:
                            root = self.winfo_toplevel()
                            root.event_generate("<<EventsChanged>>", when="tail")
                        except Exception:
                            pass
                    except Exception as e:
                        saved = False
                        save_errors = f"Fallo al persistir: {e}"

                if saved:
                    msg.showinfo("Ok", "Evento guardado.")
                    self._clear_form()
                    return
                else:
                    msg.showerror("Error al guardar", f"{save_errors or 'No se pudo guardar el evento.'}")
                    return

            # fallback: try to use scheduler directly
            if self.controller and hasattr(self.controller, "scheduler") and hasattr(self.controller.scheduler, "load_events_from_list"):
                try:
                    res = self.controller.scheduler.load_events_from_list(existing)
                except Exception as e:
                    msg.showerror("Error al guardar", f"Scheduler error: {e}")
                    return

                # res may be (False, errors) or truthy
                if isinstance(res, tuple) and res[0] is False:
                    msg.showerror("Error al guardar", f"Errores: {res[1]}")
                    return
                # on success persist to data.json
                try:
                    COMBINED = Path.home() / ".hotel_planner" / "data.json"
                    try:
                        payload = json.loads(COMBINED.read_text(encoding="utf-8")) if COMBINED.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
                    except Exception:
                        payload = {"version": 1, "inventory": {"resources": []}, "events": []}
                    payload["events"] = existing
                    tmp = COMBINED.with_name(COMBINED.name + ".tmp")
                    COMBINED.parent.mkdir(parents=True, exist_ok=True)
                    with tmp.open("w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                    os.replace(str(tmp), str(COMBINED))
                    try:
                        root = self.winfo_toplevel()
                        root.event_generate("<<EventsChanged>>", when="tail")
                    except Exception:
                        pass
                except Exception as e:
                    msg.showerror("Error al guardar", f"Fallo al persistir: {e}")
                    return

                msg.showinfo("Ok", "Evento guardado.")
                self._clear_form()
                return

        except Exception as ex:
            msg.showerror("Error", f"No se pudo guardar el evento: {ex}")
            return

        msg.showwarning("No guardado", "No se encontró un controlador para guardar el evento.")
        return

    def on_show(self):
        # refresh list of canonical resources each time view is shown
        self._refresh_resource_names()