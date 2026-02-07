import customtkinter as ctk
from typing import Optional

class ManageEventsView(ctk.CTkFrame):
    """Pantalla para crear eventos (formulario)."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        self.title = ctk.CTkLabel(self, text="Crear Evento", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(anchor="nw", padx=16, pady=12)
        # placeholder: añade campos y validaciones aquí
        ctk.CTkLabel(self, text="(Formulario de evento aquí)").pack(padx=16, pady=8)

    def on_show(self):
        pass