import customtkinter as ctk
from typing import Optional

class AddRemoveResourceView(ctk.CTkFrame):
    """Pantalla para añadir recursos."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        self.title = ctk.CTkLabel(self, text="Añadir Recurso", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(anchor="nw", padx=16, pady=12)
        # campos mínimos de ejemplo
        form = ctk.CTkFrame(self)
        form.pack(anchor="nw", padx=16, pady=8)
        ctk.CTkLabel(form, text="Nombre").grid(row=0, column=0, sticky="w")
        self.name_var = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.name_var).grid(row=0, column=1, padx=8, pady=6)
        ctk.CTkButton(form, text="Añadir (demo)", command=self._on_add_demo).grid(row=1, column=0, columnspan=2, pady=8)

    def _on_add_demo(self):
        if self.controller and hasattr(self.controller, "add_item"):
            ok, info = self.controller.add_item(name=self.name_var.get(), description="añadido desde UI", quantity=1)
            ctk.CTkMessagebox = getattr(ctk, "CTkMessagebox", None)
        # deja la lógica real al controller

    def on_show(self):
        pass