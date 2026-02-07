import tkinter
import tkinter.messagebox
import customtkinter
from hotel_planner.ui.controller import Controller
from hotel_planner.models.inventory import Inventory
from hotel_planner.core.scheduler import Scheduler
from hotel_planner.ui.widgets.vertical_segmented import VerticalSegmentedButton
from hotel_planner.ui.screens.inventory_view import InventoryView
from hotel_planner.ui.screens.edit_resources import AddRemoveResourceView
from hotel_planner.ui.screens.events_view import PlannedEventsView
from hotel_planner.ui.screens.create_event import ManageEventsView
from pathlib import Path
from hotel_planner.models.inventory_store import ensure_working_copy, load_inventory_from_json, write_default_if_missing
import json

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue")


class App(customtkinter.CTk):
    def __init__(self, controller: Controller = None):
        super().__init__()

        # configure window
        self.title("Hotel Event Manager")
        self.geometry(f"{1100}x{580}")
        # controller: usar el pasado o crear uno por defecto
        if controller is None:
            # ensure working inventory exists: copy default from package data to user config if missing
            DEFAULT = Path(__file__).resolve().parents[2] / "data" / "default_inventory.json"
            WORKING = Path.home() / ".hotel_planner" / "inventory.json"

            # read packaged default if present, else use a minimal default
            _default_content = None
            try:
                with DEFAULT.open("r", encoding="utf-8") as f:
                    _default_content = json.load(f)
            except Exception:
                _default_content = {"version": 1, "resources": []}

            # ensure a default file exists in the package data and create working copy if missing
            write_default_if_missing(DEFAULT, _default_content)
            working_path = ensure_working_copy(DEFAULT, WORKING)

            # load inventory from the working json and create scheduler/controller
            inventory = load_inventory_from_json(working_path)
            scheduler = Scheduler(inventory)
            controller = Controller(scheduler)
        self.controller = controller

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Hotel Event Manager", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # mapping de etiqueta -> método
        self._seg_handlers = {
            "Inventario": self.on_menu_inventory,
            "Añadir Recurso": self.on_menu_add_resource,
            "Eventos Planificados": self.on_menu_planned_events,
            "Crear Evento": self.on_menu_create_event,
        }
        # pasar un dispatcher al comando del widget
        self.seg_button = VerticalSegmentedButton(
            self.sidebar_frame,
            list(self._seg_handlers.keys()),
            command=lambda v: self._seg_handlers.get(v, self._on_segment_default)(v),
            width=160,
            btn_height=36,
            corner_radius=8,
        )
        self.seg_button.grid(row=1, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # --- Main area: contenedor y pantallas por cada opción del segmented ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, rowspan=4, columnspan=3, sticky="nsew", padx=12, pady=12)
        # asegúrate que el main_frame expande su contenido
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # crear instancias concretas de cada pantalla (inyectar self.controller)
        self.frames = {
            "Inventario": InventoryView(self.main_frame, controller=self.controller, corner_radius=8),
            "Añadir Recurso": AddRemoveResourceView(self.main_frame, controller=self.controller, corner_radius=8),
            "Eventos Planificados": PlannedEventsView(self.main_frame, controller=self.controller, corner_radius=8),
            "Crear Evento": ManageEventsView(self.main_frame, controller=self.controller, corner_radius=8),
        }
        for f in self.frames.values():
            f.grid(row=0, column=0, sticky="nsew")
        # mostrar pantalla inicial
        self._show_frame("Inventario")
        
        
        # Default settiings
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")


    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    # ----------------------
    # Handlers para cada segmento
    # ----------------------
    def _show_frame(self, name: str):
        """Levanta el frame identificado por name (si existe)."""
        f = self.frames.get(name)
        if not f:
            return
        try:
            f.tkraise()
        except Exception:
            pass
        # llamar a on_show() para permitir que la vista refresque sus datos
        try:
            if hasattr(f, "on_show") and callable(getattr(f, "on_show")):
                f.on_show()
        except Exception:
            pass

    def on_menu_inventory(self, value=None):
        self._show_frame("Inventario")

    def on_menu_add_resource(self, value=None):
        self._show_frame("Añadir Recurso")

    def on_menu_planned_events(self, value=None):
        self._show_frame("Eventos Planificados")

    def on_menu_create_event(self, value=None):
        self._show_frame("Crear Evento")

    def _on_segment_default(self, value=None):
        print("Segmento no manejado:", value)


if __name__ == "__main__":
    DEFAULT = Path(__file__).resolve().parents[2] / "data" / "default_inventory.json"
    WORKING = Path.home() / ".hotel_planner" / "inventory.json"
    # asegurar default presente (opcional)
    try:
        _default_content = json.loads(DEFAULT.read_text(encoding="utf-8"))
    except Exception:
        _default_content = {"version":1,"resources":[]}
    write_default_if_missing(DEFAULT, _default_content)
    working = ensure_working_copy(DEFAULT, WORKING)
    inventory = load_inventory_from_json(working)
    scheduler = Scheduler(inventory)
    controller = Controller(scheduler)
    app = App(controller=controller)
    app.mainloop()