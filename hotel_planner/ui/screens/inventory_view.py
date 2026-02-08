import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import tkinter.messagebox as msg
import json
import os
import tempfile
import uuid
from pathlib import Path
from hotel_planner.models import inventory_store as inv_store
import customtkinter as ctk
from typing import Optional, Iterable
from hotel_planner.models.resource import Resource, Room, Employee, Item

class InventoryView(ctk.CTkFrame):
    """Vista / pantalla para mostrar el inventario en 3 tablas: Espacios, Empleados, Objetos."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        # guarda mínimos de columna por pestaña (usado para auto-ajustar)
        self._min_col_widths = {}
        self._build_ui()
        # bind a virtual event so other views can notify us when inventory changed on disk
        try:
            root = self.winfo_toplevel()
            root.bind("<<InventoryChanged>>", lambda ev: self.refresh())
        except Exception:
            # ignore if binding fails at init time
            pass

    def _build_ui(self):
        # header row: title (left) + actions (right)
        header_row = ctk.CTkFrame(self)
        header_row.pack(fill="x", padx=12, pady=(8, 6))
        self.title = ctk.CTkLabel(header_row, text="Inventario del Hotel", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(side="left")
        # botón en la esquina superior derecha
        del_btn = ctk.CTkButton(header_row, text="Eliminar recurso", command=self._delete_selected_resource, width=160)
        del_btn.pack(side="right")

        # Tabbed area: three categories
        self.tabview = ctk.CTkTabview(self, width=900)
        self.tabview.add("Espacios")
        self.tabview.add("Empleados")
        self.tabview.add("Objetos")
        self.tabview.pack(fill="both", expand=True, padx=12, pady=12)

        # Treeviews per tab
        self._trees = {}
        self._create_tree(
            tab="Espacios",
            columns=("nombre", "capacidad", "tipo", "interior", "cantidad", "requisitos", "exclusiones_r", "exclusiones_c", "disponibilidad"),
            headings=("Nombre", "Capacidad", "Tipo", "Interior/Exterior", "Cantidad","Requisitos","Exclusiones(req)", "Exclusiones(cat)", "Disponibilidad"),
            col_widths=(220, 80, 120, 120, 80, 220, 240, 240, 240),
        )
        self._create_tree(
            tab="Empleados",
            columns=("nombre", "rol", "turno", "cantidad", "requisitos", "exclusiones_r", "exclusiones_c", "disponibilidad"),
            headings=("Nombre", "Rol", "Turno", "Cantidad","Requisitos","Exclusiones(req)", "Exclusiones(cat)", "Disponibilidad"),
            col_widths=(260, 140, 100, 80, 80, 220, 240, 240, 240),
        )
        self._create_tree(
            tab="Objetos",
            columns=("nombre", "descripcion", "cantidad", "requisitos", "exclusiones_r", "exclusiones_c", "disponibilidad"),
            headings=("Nombre", "Descripción", "Cantidad","Requisitos","Exclusiones(req)", "Exclusiones(cat)", "Disponibilidad"),
            col_widths=(260, 360, 80, 80, 220, 240, 240, 240),
        )

    def _create_tree(self, tab: str, columns: tuple, headings: tuple, col_widths: tuple):
        frame = self.tabview.tab(tab)
        container = ctk.CTkFrame(frame)
        container.pack(fill="both", expand=True, padx=6, pady=6)
        tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse", height=12)
        for col, head, w in zip(columns, headings, col_widths):
            tree.heading(col, text=head)
            tree.column(col, width=w, anchor="w")
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self._trees[tab] = tree
        # almacenar mínimas (siempre en píxeles) para uso posterior en autosize
        try:
            self._min_col_widths[tab] = {col: int(w) for col, w in zip(columns, col_widths)}
        except Exception:
            self._min_col_widths[tab] = {col: 50 for col in columns}

    # -------- helpers to format metadata ----------
    def _fmt_meta(self, res) -> str:
        parts = []
        qty = getattr(res, "quantity", None)
        if qty is not None:
            parts.append(str(qty))
        # requires/excludes/excludes_categories expected as sets of lower-case strings
        reqs = getattr(res, "requires", None)
        if reqs:
            parts.append("req: " + ", ".join(sorted(reqs)))
        ex = getattr(res, "excludes", None)
        if ex:
            parts.append("ex: " + ", ".join(sorted(ex)))
        excat = getattr(res, "excludes_categories", None)
        if excat:
            parts.append("ex_cat: " + ", ".join(sorted(excat)))
        return " | ".join(parts) if parts else ""

    def _fmt_availability(self, name: str, res) -> str:
        # Mantener simple: delegar a controller.scheduler.format_usage_intervals()
        # Si no existe controller/scheduler devolver "N/A".
        if not self.controller or not hasattr(self.controller, "scheduler"):
            return "N/A"
        lines = self.controller.scheduler.format_usage_intervals(name)
        if lines:
            return " ; ".join(lines)
        # Si no hay intervalos formateados, usar flag disponible del recurso
        avail = getattr(res, "available", None)
        return "Disponible" if avail else "Ocupado"

    def _clear_all(self):
        for tree in self._trees.values():
            for iid in tree.get_children():
                tree.delete(iid)

    def on_show(self):
        """Refresca datos desde controller al mostrar la vista."""
        self.refresh()

    def refresh(self):
        # Obtener recursos únicamente a través de controller.list_resources()
        if not self.controller or not hasattr(self.controller, "list_resources"):
            resources = []
        else:
            resources = list(self.controller.list_resources())

        # clear
        self._clear_all()

        # populate per category
        for res in resources:
            cat = getattr(res, "category", "") or ""
            name = getattr(res, "name", "")
            # common metadata pieces
            qty = str(getattr(res, "quantity", "")) if getattr(res, "quantity", None) is not None else ""
            reqs = ", ".join(sorted(getattr(res, "requires", []))) if getattr(res, "requires", None) else ""
            exr = ", ".join(sorted(getattr(res, "excludes", []))) if getattr(res, "excludes", None) else ""
            exc = ", ".join(sorted(getattr(res, "excludes_categories", []))) if getattr(res, "excludes_categories", None) else ""
            availability = self._fmt_availability(name, res)

            if cat == "room":
                tree = self._trees["Espacios"]
                vals = (
                    name,
                    str(getattr(res, "capacity", "")),
                    str(getattr(res, "room_type", "")),
                    "Interior" if getattr(res, "interior", True) else "Exterior",
                    qty,
                    reqs,
                    exr,
                    exc,
                    availability,
                )
                tree.insert("", "end", values=vals)
            elif cat == "employee":
                tree = self._trees["Empleados"]
                vals = (
                    name,
                    str(getattr(res, "role", "")),
                    str(getattr(res, "shift", "")),
                    qty,
                    reqs,
                    exr,
                    exc,
                    availability,
                )
                tree.insert("", "end", values=vals)
            else:  # item / default
                tree = self._trees["Objetos"]
                vals = (
                    name,
                    str(getattr(res, "description", "")),
                    qty,
                    reqs,
                    exr,
                    exc,
                    availability,
                )
                tree.insert("", "end", values=vals)
        # ajustar anchos de columnas automáticamente después de poblar
        try:
            for tab, tree in self._trees.items():
                self._autosize_tree(tree, tab)
        except Exception:
            pass

    def _autosize_tree(self, tree: ttk.Treeview, tab: str, padding: int = 12, max_width: int = 1200):
        """
        Ajusta cada columna del tree al ancho del texto más largo entre encabezado y celdas,
        respetando un ancho mínimo (definido en self._min_col_widths[tab]) y un máximo opcional.
        """
        # obtener fuente usada por el tree (fallback a font por defecto)
        try:
            f = tkfont.Font(font=tree.cget("font")) if tree.cget("font") else tkfont.Font()
        except Exception:
            f = tkfont.Font()

        min_map = self._min_col_widths.get(tab, {})
        cols = tree["columns"]
        for col in cols:
            # medir encabezado
            hdr = ""
            try:
                hdr = tree.heading(col).get("text", "") or ""
            except Exception:
                hdr = str(col)
            max_px = f.measure(hdr)
            # medir celdas
            for iid in tree.get_children():
                try:
                    cell = tree.set(iid, col) or ""
                except Exception:
                    cell = ""
                if cell:
                    w = f.measure(str(cell))
                    if w > max_px:
                        max_px = w
            # añadir padding y respetar mínimo y máximo
            desired = max_px + padding
            min_w = int(min_map.get(col, 50))
            final_w = max(min_w, desired)
            final_w = min(final_w, max_width)
            try:
                tree.column(col, width=final_w)
            except Exception:
                pass

    def _get_selected_name(self):
        """Devuelve (tree, resource_name) o (None, None) si no hay selección."""
        try:
            tab = self.tabview.get()
            tree = self._trees.get(tab)
            if tree is None:
                return None, None
            sel = tree.focus() or (tree.selection()[0] if tree.selection() else None)
            if not sel:
                return tree, None
            vals = tree.item(sel, "values") or ()
            name = vals[0] if len(vals) > 0 else None
            return tree, name
        except Exception:
            return None, None

    def _delete_selected_resource(self):
        """Eliminar recurso seleccionado: intentar vía controller, si no via working JSON."""
        tree, name = self._get_selected_name()
        if name is None:
            msg.showwarning("Seleccionar", "Selecciona un recurso primero.")
            return

        if not msg.askyesno("Confirmar eliminación", f"¿Eliminar recurso '{name}' del inventario?"):
            return

        # 1) intentar vía controller API si existe
        try:
            if self.controller and hasattr(self.controller, "remove_resource"):
                ok = self.controller.remove_resource(name)
                # controller may return (True, info) or True
                if isinstance(ok, tuple):
                    ok = ok[0]
                if ok:
                    msg.showinfo("Ok", f"Recurso '{name}' eliminado.")
                    self.refresh()
                    return
        except Exception:
            pass

        # 2) update the single DATA file ~/.hotel_planner/data.json
        try:
            DATA = Path.home() / ".hotel_planner" / "data.json"
            if DATA.exists():
                raw = DATA.read_text(encoding="utf-8")
                payload = json.loads(raw) if raw.strip() else {"version": 1, "inventory": {"resources": []}, "events": []}
            else:
                payload = {"version": 1, "inventory": {"resources": []}, "events": []}

            resources = (payload.get("inventory") or {}).get("resources", [])
            before = len(resources)
            resources = [r for r in resources if (r.get("name") or "") != name]
            after = len(resources)
            if after == before:
                msg.showwarning("No encontrado", f"No se encontró '{name}' en el inventory combinado.")
                return
            payload["inventory"] = {"resources": resources}

            # Remove any events that reference this resource (case-insensitive match)
            evs = payload.get("events", []) or []
            keep = []
            removed_events = []
            target = name.strip().lower()
            for ev in evs:
                try:
                    ev_resources = ev.get("resources", []) if isinstance(ev, dict) else []
                    used = False
                    for er in ev_resources:
                        try:
                            rname = (er.get("name") if isinstance(er, dict) else getattr(er, "name", "") ) or ""
                            if rname.strip().lower() == target:
                                used = True
                                break
                        except Exception:
                            continue
                    if used:
                        removed_events.append(ev)
                    else:
                        keep.append(ev)
                except Exception:
                    keep.append(ev)
            if removed_events:
                payload["events"] = keep

            # write DATA file atomically
            tmp = DATA.with_name(DATA.name + ".tmp")
            DATA.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(str(tmp), str(DATA))

            # recargar inventario en memoria y actualizar controller/scheduler if possible
            # build a small ephemeral legacy-style payload so inv_store can parse it
            new_inv = None
            try:
                payload_now = payload  # payload ya leído arriba
                inv_payload = {"version": payload_now.get("version", 1), "resources": (payload_now.get("inventory") or {}).get("resources", [])}
                tmp_name = f"hotel_planner_inv_{os.getpid()}_{uuid.uuid4().hex}.json"
                tmp_path = Path(tempfile.gettempdir()) / tmp_name
                tmp_path.write_text(json.dumps(inv_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                try:
                    new_inv = inv_store.load_inventory_from_json(tmp_path)
                except Exception:
                    new_inv = None
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            except Exception:
                new_inv = None
            try:
                if self.controller:
                    if hasattr(self.controller, "scheduler") and getattr(self.controller, "scheduler", None) is not None:
                        try:
                            setattr(self.controller.scheduler, "inventory", new_inv)
                        except Exception:
                            pass
                    try:
                        setattr(self.controller, "inventory", new_inv)
                    except Exception:
                        pass
            except Exception:
                pass

            # If we removed events, update controller/scheduler in-memory and notify event views
            if removed_events:
                try:
                    serializable = payload.get("events", []) or []
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
                try:
                    root = self.winfo_toplevel()
                    root.event_generate("<<EventsChanged>>", when="tail")
                except Exception:
                    pass

            try:
                root = self.winfo_toplevel()
                root.event_generate("<<InventoryChanged>>", when="tail")
            except Exception:
                pass

            info_msg = f"Recurso '{name}' eliminado del inventario combinado."
            if removed_events:
                info_msg += f" Se eliminaron {len(removed_events)} evento(s) que lo utilizaban."
            msg.showinfo("Ok", info_msg)
            self.refresh()
            return
        except Exception as e:
            msg.showerror("Error", f"No se pudo eliminar '{name}': {e}")
            return