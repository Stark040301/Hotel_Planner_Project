import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
from typing import Optional, Iterable
from hotel_planner.models.resource import Resource, Room, Employee, Item

class InventoryView(ctk.CTkFrame):
    """Vista / pantalla para mostrar el inventario en 3 tablas: Espacios, Empleados, Objetos."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        self.title = ctk.CTkLabel(self, text="Inventario del Hotel", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(anchor="nw", padx=12, pady=(8, 6))

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
        container = tk.Frame(frame)
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