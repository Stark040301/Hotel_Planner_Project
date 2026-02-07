import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import customtkinter as ctk
from typing import Optional, Iterable
from datetime import datetime, timedelta

class PlannedEventsView(ctk.CTkFrame):
    """Pantalla para listar y gestionar eventos planificados en una tabla."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._min_col_widths = {}
        self._build_ui()

    def _build_ui(self):
        self.title = ctk.CTkLabel(self, text="Eventos Planificados", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(anchor="nw", padx=16, pady=12)

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