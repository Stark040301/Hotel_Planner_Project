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
import json
import tempfile
import os
from hotel_planner.models import store as unified_store
from hotel_planner.models import inventory_store as inv_store
from hotel_planner.models import event_store as ev_store
import tkinter.filedialog as fd
import shutil
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
            # Prefer single DATA file ~/.hotel_planner/data.json
            DATA_WORKING = Path.home() / ".hotel_planner" / "data.json"
            DATA_DEFAULT = Path(__file__).resolve().parents[2] / "data" / "default_data.json"
            # ensure default exists (use unified_store helper)
            try:
                default_payload = json.loads(DATA_DEFAULT.read_text(encoding="utf-8")) if DATA_DEFAULT.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
            except Exception:
                default_payload = {"version": 1, "inventory": {"resources": []}, "events": []}
            unified_store.write_default_if_missing(DATA_DEFAULT, default_payload)
            unified_store.ensure_working_copy(DATA_DEFAULT, DATA_WORKING)
            data = unified_store.load_data(DATA_WORKING)

            # create ephemeral files for existing loaders (no persistent inventory.json/events.json)
            tmpdir = Path(tempfile.gettempdir())
            tmp_inv = tmpdir / f"hotel_planner_inventory_{os.getpid()}.json"
            tmp_ev = tmpdir / f"hotel_planner_events_{os.getpid()}.json"
            try:
                inv_payload = {"version": data.get("version", 1), "resources": (data.get("inventory") or {}).get("resources", [])}
                tmp_inv.write_text(json.dumps(inv_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                tmp_inv = None
            try:
                ev_payload = {"version": data.get("version", 1), "events": data.get("events", [])}
                tmp_ev.write_text(json.dumps(ev_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                tmp_ev = None

            # load inventory using existing loader from ephemeral file (keeps Inventory construction)
            if tmp_inv and tmp_inv.exists():
                inventory = inv_store.load_inventory_from_json(tmp_inv)
            else:
                inventory = inv_store.load_inventory_from_json(DATA_DEFAULT) if DATA_DEFAULT.exists() else None

            scheduler = Scheduler(inventory)
            controller = Controller(scheduler)
            # cleanup ephemeral files
            try:
                if tmp_inv and tmp_inv.exists():
                    tmp_inv.unlink()
                if tmp_ev and tmp_ev.exists():
                    tmp_ev.unlink()
            except Exception:
                pass
        self.controller = controller

        # asegurar que tenemos referencia al scheduler (venga del controller o de la creación anterior)
        scheduler = getattr(self.controller, "scheduler", None)

        # --- cargar eventos inmediatamente desde data.json antes de crear las vistas ---
        # Esto asegura que al construir InventoryView la disponibilidad refleje los eventos ya cargados.
        try:
            DATA = Path.home() / ".hotel_planner" / "data.json"
            events_now = []
            try:
                if DATA.exists():
                    payload_now = json.loads(DATA.read_text(encoding="utf-8") or "{}")
                    events_now = payload_now.get("events", []) or []
            except Exception as _e:
                events_now = []

            if scheduler and hasattr(scheduler, "load_events_from_list"):
                try:
                    scheduler.load_events_from_list(events_now)
                except Exception as e:
                    print("DEBUG app: early scheduler.load_events_from_list error:", e)
            elif hasattr(self.controller, "load_events"):
                try:
                    self.controller.load_events(events_now)
                except Exception as e:
                    print("DEBUG app: early controller.load_events error:", e)
        except Exception:
            pass
        # --- fin carga temprana de eventos ---

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1)
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
        
        # Export / Import buttons (above appearance controls)
        self.export_btn = customtkinter.CTkButton(self.sidebar_frame, text="Exportar a JSON", command=self._on_export, width=120)
        self.export_btn.grid(row=4, column=0, padx=20, pady=(12, 6))
        self.import_btn = customtkinter.CTkButton(self.sidebar_frame, text="Importar desde JSON", command=self._on_import, width=120)
        self.import_btn.grid(row=5, column=0, padx=20, pady=(0, 8))

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(6, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

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

        # Default events
        WORKING_EVENTS = Path.home() / ".hotel_planner" / "events.json"
        try:
            events = ev_store.load_events_from_json(WORKING_EVENTS)
        except Exception:
            events = []
        if hasattr(scheduler, "load_events_from_list"):
            try:
                scheduler.load_events_from_list(events)
            except Exception as e:
                print("DEBUG app: scheduler.load_events_from_list error:", e)
        elif hasattr(controller, "load_events"):
            try:
                controller.load_events(events)
            except Exception:
                pass
        else:
            try:
                scheduler._events = events
            except Exception:
                pass

        # Use single DATA file (~/.hotel_planner/data.json) as sole source of events/inventory
        DATA = Path.home() / ".hotel_planner" / "data.json"
        # tell controller where to persist events
        try:
            if hasattr(controller, "set_events_path"):
                controller.set_events_path(DATA)
            else:
                controller.events_path = DATA
        except Exception:
            pass

        # load events from DATA file (fallback to empty list)
        events = []
        try:
            if DATA.exists():
                payload = json.loads(DATA.read_text(encoding="utf-8") or "{}")
                events = payload.get("events", []) or []
            else:
                events = []
        except Exception as e:
            print("DEBUG app: error reading DATA data.json:", e)
            events = []

        # inject events into scheduler/controller
        if hasattr(scheduler, "load_events_from_list"):
            try:
                scheduler.load_events_from_list(events)
            except Exception as e:
                print("DEBUG app: scheduler.load_events_from_list error:", e)
        elif hasattr(controller, "load_events"):
            try:
                controller.load_events(events)
            except Exception as e:
                print("DEBUG app: controller.load_events error:", e)
        else:
            try:
                scheduler._events = events
            except Exception:
                pass

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    # ----------------------
    # Import / Export helpers
    # ----------------------
    def _on_export(self):
        """Export DATA data.json to chosen path."""
        DATA = Path.home() / ".hotel_planner" / "data.json"
        if not DATA.exists():
            tkinter.messagebox.showwarning("Exportar", "No existe ~/.hotel_planner/data.json para exportar.")
            return
        # default folder: project data directory (Hotel_Planner_Project/data)
        DATA_DIR = Path(__file__).resolve().parents[2] / "data"
        initial_dir = str(DATA_DIR) if DATA_DIR.exists() else str(Path.home())
        dest = fd.asksaveasfilename(parent=self, initialdir=initial_dir, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title="Export data to...")
        if not dest:
            return
        try:
            shutil.copyfile(str(DATA), dest)
            tkinter.messagebox.showinfo("Exportar", f"Datos exportados a:\n{dest}")
        except Exception as e:
            tkinter.messagebox.showerror("Exportar", f"No se pudo exportar: {e}")

    def _on_import(self):
        """Import a JSON file and replace ~/.hotel_planner/data.json (validates minimal structure)."""
        DATA_DIR = Path(__file__).resolve().parents[2] / "data"
        initial_dir = str(DATA_DIR) if DATA_DIR.exists() else str(Path.home())
        src = fd.askopenfilename(parent=self, initialdir=initial_dir, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")], title="Import data from...")
        if not src:
            return
        try:
            with open(src, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:
            tkinter.messagebox.showerror("Importar", f"Archivo inválido: {e}")
            return

        # minimal validation: must be a dict and contain 'inventory' or 'events'
        if not isinstance(payload, dict) or (("inventory" not in payload) and ("events" not in payload)):
            tkinter.messagebox.showerror("Importar", "El fichero no parece un data.json válido (se espera keys 'inventory' o 'events').")
            return

        DATA = Path.home() / ".hotel_planner" / "data.json"
        try:
            tmp = DATA.with_name(DATA.name + ".tmp")
            DATA.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            os.replace(str(tmp), str(DATA))
        except Exception as e:
            tkinter.messagebox.showerror("Importar", f"No se pudo escribir data.json: {e}")
            return

        # Reload into controller/scheduler
        try:
            data = unified_store.load_data(DATA)
            # refresh inventory in controller
            inv_payload = {"version": data.get("version", 1), "resources": (data.get("inventory") or {}).get("resources", [])}
            tmp_inv = None
            try:
                tmp_inv = Path(tempfile.gettempdir()) / f"hotel_planner_inv_{os.getpid()}.json"
                tmp_inv.write_text(json.dumps(inv_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                new_inv = inv_store.load_inventory_from_json(tmp_inv)
                # set inventory in scheduler/controller
                if hasattr(self.controller, "scheduler") and getattr(self.controller, "scheduler", None) is not None:
                    try:
                        setattr(self.controller.scheduler, "inventory", new_inv)
                    except Exception:
                        pass
                try:
                    setattr(self.controller, "inventory", new_inv)
                except Exception:
                    pass
            finally:
                try:
                    if tmp_inv and tmp_inv.exists():
                        tmp_inv.unlink()
                except Exception:
                    pass

            # reload events into controller/scheduler
            events = data.get("events", []) or []
            if hasattr(self.controller, "load_events"):
                try:
                    self.controller.load_events(events)
                except Exception:
                    pass
            elif hasattr(self.controller, "scheduler") and hasattr(self.controller.scheduler, "load_events_from_list"):
                try:
                    self.controller.scheduler.load_events_from_list(events)
                except Exception:
                    pass

            # notify views
            try:
                root = self
                root.event_generate("<<InventoryChanged>>", when="tail")
                root.event_generate("<<EventsChanged>>", when="tail")
            except Exception:
                pass

            tkinter.messagebox.showinfo("Importar", "Importación completada. Vistas actualizadas.")
        except Exception as e:
            tkinter.messagebox.showerror("Importar", f"Error al recargar datos: {e}")
            return

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
    # Ejecutar la App usando el flujo combinado (data.json).
    # No crear un controller externo: App() hará la carga unificada y creará controller/scheduler.
    app = App()
    app.mainloop()