import customtkinter as ctk
from typing import Optional

class PlannedEventsView(ctk.CTkFrame):
    """Pantalla para listar y gestionar eventos planificados."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        self.title = ctk.CTkLabel(self, text="Eventos Planificados", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(anchor="nw", padx=16, pady=12)
        self.events_box = ctk.CTkTextbox(self, width=600, height=300)
        self.events_box.pack(fill="both", expand=True, padx=16, pady=12)

    def on_show(self):
        try:
            self.events_box.delete("0.0", "end")
            if self.controller and hasattr(self.controller, "list_events"):
                for ev in self.controller.list_events():
                    self.events_box.insert("end", f"{ev}\n")
            else:
                self.events_box.insert("end", "No controller connected\n")
        except Exception:
            pass