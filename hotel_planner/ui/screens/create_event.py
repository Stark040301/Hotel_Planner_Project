import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msg
from datetime import datetime, timedelta
import customtkinter as ctk
from typing import Optional, List, Dict, Callable
from pathlib import Path
import json
import os
from tkcalendar import DateEntry
from hotel_planner.models import event_store as ev_store


# ============================================================
# NUEVO COMPONENTE: Selector de fecha y hora con calendario
# ============================================================
class DateTimePicker(ctk.CTkFrame):
    """
    Selector de fecha y hora con calendario emergente.
    Muestra un campo de texto con la fecha/hora y un botón para abrir el calendario.
    Soporta un callback que se ejecuta cuando el valor cambia.
    """
    def __init__(self, master, initial_value: str = "", callback: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.callback = callback

        # Campo de texto para mostrar la fecha/hora
        self.entry = ctk.CTkEntry(self, placeholder_text="YYYY-MM-DDTHH:MM", width=200)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        if initial_value:
            self.entry.insert(0, initial_value)

        # Botón para abrir el selector
        self.btn = ctk.CTkButton(
            self,
            text="📅",
            width=40,
            command=self._open_picker,
            corner_radius=6
        )
        self.btn.grid(row=0, column=1, sticky="e")

        self._picker_window = None

    def _open_picker(self):
        """Abre una ventana emergente con calendario y selector de hora."""
        if self._picker_window and self._picker_window.winfo_exists():
            self._picker_window.focus()
            return

        self._picker_window = ctk.CTkToplevel(self)
        self._picker_window.title("Seleccionar fecha y hora")
        self._picker_window.geometry("300x350")
        self._picker_window.resizable(False, False)
        self._picker_window.transient(self.winfo_toplevel())
        self._picker_window.grab_set()  # Modal

        # Obtener fecha actual o la del campo si es válida
        try:
            current_text = self.entry.get()
            if current_text:
                dt = datetime.fromisoformat(current_text)
                default_year = dt.year
                default_month = dt.month
                default_day = dt.day
                default_hour = dt.hour
                default_minute = dt.minute
            else:
                now = datetime.now()
                default_year = now.year
                default_month = now.month
                default_day = now.day
                default_hour = now.hour
                default_minute = 0
        except Exception:
            now = datetime.now()
            default_year = now.year
            default_month = now.month
            default_day = now.day
            default_hour = now.hour
            default_minute = 0

        # Calendario
        cal = DateEntry(
            self._picker_window,
            year=default_year,
            month=default_month,
            day=default_day,
            date_pattern='yyyy-mm-dd',
            width=20,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            locale='es_ES'
        )
        cal.pack(pady=10)

        # Marco para hora
        time_frame = ctk.CTkFrame(self._picker_window)
        time_frame.pack(pady=10)

        ctk.CTkLabel(time_frame, text="Hora:").pack(side="left", padx=5)
        hour_spin = tk.Spinbox(
            time_frame,
            from_=0,
            to=23,
            width=3,
            font=("Arial", 12),
            wrap=True
        )
        hour_spin.pack(side="left", padx=2)
        hour_spin.delete(0, "end")
        hour_spin.insert(0, f"{default_hour:02d}")

        ctk.CTkLabel(time_frame, text=":").pack(side="left")
        minute_spin = tk.Spinbox(
            time_frame,
            from_=0,
            to=59,
            width=3,
            font=("Arial", 12),
            wrap=True
        )
        minute_spin.pack(side="left", padx=2)
        minute_spin.delete(0, "end")
        minute_spin.insert(0, f"{default_minute:02d}")

        # Botón Aceptar
        def accept():
            try:
                date_str = cal.get()
                hour = int(hour_spin.get())
                minute = int(minute_spin.get())
                dt = datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")
                iso_str = dt.isoformat()
                self.entry.delete(0, "end")
                self.entry.insert(0, iso_str)
                # Ejecutar callback si existe
                if self.callback:
                    self.callback()
                self._picker_window.destroy()
            except Exception as e:
                msg.showerror("Error", f"Fecha/hora inválida: {e}")

        btn_frame = ctk.CTkFrame(self._picker_window)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Aceptar", command=accept, width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self._picker_window.destroy, width=80).pack(side="left", padx=5)

        cal.focus_set()

    def get(self) -> str:
        """Devuelve el valor actual del campo."""
        return self.entry.get()

    def set(self, value: str):
        """Establece el valor del campo y ejecuta el callback."""
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        if self.callback:
            self.callback()


# ============================================================
# VISTA PRINCIPAL: Crear Evento
# ============================================================
class ManageEventsView(ctk.CTkFrame):
    """Pantalla para crear eventos (formulario)."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._resource_rows = []
        self._resource_names_cache: List[str] = []
        self._build_ui()

    def _build_ui(self):
        padx = 16
        pady = 12

        header = ctk.CTkLabel(
            self,
            text="➕ Crear Nuevo Evento",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(anchor="nw", padx=padx, pady=(12, 16))

        frm = ctk.CTkFrame(self)
        frm.pack(fill="x", padx=padx, pady=(0, 12))

        # Nombre
        ctk.CTkLabel(frm, text="Nombre del Evento", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=8, pady=(0, 8))
        self.name_var = tk.StringVar()
        ctk.CTkEntry(frm, textvariable=self.name_var, width=400).grid(row=0, column=1, columnspan=3, sticky="ew", padx=8, pady=(0, 8))

        # Start / End con selector de fecha (con callback)
        ctk.CTkLabel(frm, text="Comienza", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        self.start_picker = DateTimePicker(frm, callback=self._update_duration)
        self.start_picker.grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(frm, text="Termina", font=ctk.CTkFont(weight="bold")).grid(row=1, column=2, sticky="w", padx=8, pady=(0, 8))
        self.end_picker = DateTimePicker(frm, callback=self._update_duration)
        self.end_picker.grid(row=1, column=3, sticky="ew", padx=8, pady=(0, 8))

        # Vincular también los eventos de teclado para escritura manual
        self.start_picker.entry.bind("<KeyRelease>", lambda e: self._update_duration())
        self.end_picker.entry.bind("<KeyRelease>", lambda e: self._update_duration())

        # Duración auto
        self.duration_lbl = ctk.CTkLabel(frm, text="⏱️ Duración: --", font=ctk.CTkFont(size=12))
        self.duration_lbl.grid(row=2, column=1, sticky="w", padx=8, pady=(0, 12))

        # Resources area
        ctk.CTkLabel(self, text="📦 Recursos Necesarios", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="nw", padx=padx, pady=(12, 8))
        rframe = ctk.CTkFrame(self)
        rframe.pack(fill="both", expand=False, padx=padx, pady=(0, 12))
        self._resources_container = tk.Frame(rframe)
        self._resources_container.pack(fill="x", padx=8, pady=8)

        btn_row = ctk.CTkFrame(rframe)
        btn_row.pack(fill="x", padx=8, pady=8)

        add_btn = ctk.CTkButton(
            btn_row,
            text="+ Recurso",
            command=self._add_resource_row,
            width=120,
            corner_radius=6,
            hover_color="#059669"
        )
        add_btn.pack(side="left", padx=(0, 8))

        scan_btn = ctk.CTkButton(
            btn_row,
            text="🔄 Recargar",
            command=self._refresh_resource_names,
            width=130,
            corner_radius=6,
            hover_color="#059669"
        )
        scan_btn.pack(side="left")

        # Recurrence & notes
        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=padx, pady=(12, 16))

        ctk.CTkLabel(bottom, text="Recurrencia", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=8, pady=(0, 8))
        self.recur_var = tk.StringVar(value="none")
        recur_cb = ttk.Combobox(
            bottom,
            textvariable=self.recur_var,
            values=["none", "daily", "weekly", "monthly", "seasonal", "custom"],
            state="readonly",
            width=20
        )
        recur_cb.grid(row=0, column=1, sticky="w", padx=8, pady=(0, 8))

        ctk.CTkLabel(bottom, text="Notas/Comentarios", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="nw", padx=8, pady=(0, 8))
        self.notes_txt = tk.Text(bottom, height=3, width=50)
        self.notes_txt.grid(row=1, column=1, columnspan=3, sticky="ew", padx=8, pady=(0, 8))

        # buttons
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=padx, pady=(16, 12))

        cancel_btn = ctk.CTkButton(
            actions,
            text="✕ Cancelar",
            command=self._clear_form,
            fg_color="#999999",
            hover_color="#737373",
            width=120,
            corner_radius=6
        )
        cancel_btn.pack(side="right", padx=8)

        find_btn = ctk.CTkButton(
            actions,
            text="🔍 Siguiente Hueco",
            command=self._find_next_slot,
            width=150,
            corner_radius=6,
            hover_color="#1D4ED8"
        )
        find_btn.pack(side="right", padx=8)

        save_btn = ctk.CTkButton(
            actions,
            text="✓ Guardar",
            command=self._save_event,
            width=130,
            corner_radius=6,
            hover_color="#059669"
        )
        save_btn.pack(side="right", padx=8)

        # initial population of resources
        self._refresh_resource_names()
        # add one empty row by default
        self._add_resource_row()

    def _clear_form(self):
        self.name_var.set("")
        self.start_picker.set("")
        self.end_picker.set("")
        # Al usar set, el callback ya actualiza la duración, pero por si acaso:
        self._update_duration()
        for row in list(self._resource_rows):
            self._remove_resource_row(row)
        self._add_resource_row()
        self.recur_var.set("none")
        self.notes_txt.delete("1.0", "end")

    def _refresh_resource_names(self):
        names = []
        try:
            if self.controller and hasattr(self.controller, "list_resources"):
                res = list(self.controller.list_resources())
                for r in res:
                    if isinstance(r, dict):
                        names.append(r.get("name"))
                    else:
                        names.append(getattr(r, "name", None))
            names = [n for n in names if n]
        except Exception:
            names = []
        self._resource_names_cache = sorted(set(names))
        for row in list(self._resource_rows):
            combo = row["combo"]
            combo["values"] = self._resource_names_cache

    def _add_resource_row(self, prefill: Dict = None):
        row_frm = tk.Frame(self._resources_container)
        row_frm.pack(fill="x", pady=4)
        combo = ttk.Combobox(row_frm, values=self._resource_names_cache, width=48)
        combo.pack(side="left", padx=(0, 6))
        qty_var = tk.IntVar(value=1)
        qty_spin = tk.Spinbox(row_frm, from_=1, to=999, textvariable=qty_var, width=6)
        qty_spin.pack(side="left", padx=(0, 6))
        rem_btn = ctk.CTkButton(row_frm, text="Quitar", width=80, command=lambda: self._remove_resource_row(row))
        rem_btn.pack(side="left", padx=(6, 0))

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
        s = self.start_picker.get().strip()
        e = self.end_picker.get().strip()
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

    def _compute_duration_minutes(self) -> int:
        s = self.start_picker.get().strip()
        e = self.end_picker.get().strip()
        try:
            if s and e and self._validate_iso(s) and self._validate_iso(e):
                st = datetime.fromisoformat(s)
                ed = datetime.fromisoformat(e)
                if ed > st:
                    return int((ed - st).total_seconds() // 60)
        except Exception:
            pass
        return 60

    def _find_next_slot(self):
        if not self.controller or not hasattr(self.controller, "find_next_available"):
            msg.showerror("No disponible", "No hay controlador disponible para buscar huecos.")
            return

        resources = self._gather_resources()
        if not resources:
            msg.showwarning("Recursos", "Añade al menos un recurso para buscar hueco disponible.")
            return

        try:
            start_field = self.start_picker.get().strip()
            if start_field and self._validate_iso(start_field):
                start_from = datetime.fromisoformat(start_field)
            else:
                start_from = datetime.now()
        except Exception:
            start_from = datetime.now()

        duration_mins = self._compute_duration_minutes()
        window_end = start_from + timedelta(days=30)

        try:
            res = self.controller.find_next_available(duration_mins, resources, start_from, window_end)
        except Exception as e:
            msg.showerror("Error", f"Error buscando hueco: {e}")
            return

        if not res:
            msg.showinfo("No hay hueco", "No se encontró un intervalo disponible en el próximo mes.")
            return

        proposed_start, proposed_end = res
        proposed_start = proposed_start.replace(second=0, microsecond=0)
        proposed_end = proposed_end.replace(second=0, microsecond=0)
        pretty = f"{proposed_start.isoformat()} → {proposed_end.isoformat()}"
        if not msg.askyesno("Propuesta de hueco", f"Se propone el siguiente intervalo:\n\n{pretty}\n\n¿Desea usarlo?"):
            return

        self.start_picker.set(proposed_start.isoformat())
        self.end_picker.set(proposed_end.isoformat())
        # El callback ya actualizará la duración, pero por si acaso:
        self._update_duration()
        try:
            root = self.winfo_toplevel()
            root.event_generate("<<EventsDraftChanged>>", when="tail")
        except Exception:
            pass

    def _validate_iso(self, s: str) -> bool:
        try:
            datetime.fromisoformat(s)
            return True
        except Exception:
            return False

    def _save_event(self):
        name = self.name_var.get().strip()
        start = self.start_picker.get().strip()
        end = self.end_picker.get().strip()
        recurrence = self.recur_var.get() or None
        notes = self.notes_txt.get("1.0", "end").strip()
        resources = self._gather_resources()

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

            if self.controller and hasattr(self.controller, "load_events"):
                try:
                    res = self.controller.load_events(existing)
                    if isinstance(res, tuple):
                        ok = bool(res[0])
                        if not ok:
                            save_errors = res[1] if len(res) > 1 else "Error desconocido"
                            saved = False
                        else:
                            saved = True
                    else:
                        saved = True
                except Exception as e:
                    saved = False
                    save_errors = str(e)

                if saved:
                    try:
                        DATA = Path.home() / ".hotel_planner" / "data.json"
                        try:
                            payload = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
                        except Exception:
                            payload = {"version": 1, "inventory": {"resources": []}, "events": []}
                        payload["events"] = existing
                        tmp = DATA.with_name(DATA.name + ".tmp")
                        DATA.parent.mkdir(parents=True, exist_ok=True)
                        with tmp.open("w", encoding="utf-8") as f:
                            json.dump(payload, f, ensure_ascii=False, indent=2)
                        os.replace(str(tmp), str(DATA))
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

            if self.controller and hasattr(self.controller, "scheduler") and hasattr(self.controller.scheduler, "load_events_from_list"):
                try:
                    res = self.controller.scheduler.load_events_from_list(existing)
                except Exception as e:
                    msg.showerror("Error al guardar", f"Scheduler error: {e}")
                    return

                if isinstance(res, tuple) and res[0] is False:
                    msg.showerror("Error al guardar", f"Errores: {res[1]}")
                    return

                try:
                    DATA = Path.home() / ".hotel_planner" / "data.json"
                    try:
                        payload = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
                    except Exception:
                        payload = {"version": 1, "inventory": {"resources": []}, "events": []}
                    payload["events"] = existing
                    tmp = DATA.with_name(DATA.name + ".tmp")
                    DATA.parent.mkdir(parents=True, exist_ok=True)
                    with tmp.open("w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                    os.replace(str(tmp), str(DATA))
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
        self._refresh_resource_names()