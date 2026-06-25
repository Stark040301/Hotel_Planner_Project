import tkinter as tk
import tkinter.messagebox as msg
import json
import os
import tempfile
import uuid
from pathlib import Path
from hotel_planner.models import inventory_store as inv_store
import customtkinter as ctk
from typing import Optional, Dict, List, Any
from hotel_planner.models.resource import Resource, Room, Employee, Item
from hotel_planner.ui.components import InventoryCard


class EditResourceDialog(ctk.CTkToplevel):
    """Diálogo para editar un recurso existente (solo cantidad, atributos, requisitos y exclusiones)."""

    def __init__(self, parent, controller, resource_name: str):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.resource_name = resource_name
        self.resource = None
        self.inventory = None

        # Obtener el recurso del controlador
        try:
            if self.controller and hasattr(self.controller, "list_resources"):
                for r in self.controller.list_resources():
                    if getattr(r, "name", "") == resource_name:
                        self.resource = r
                        break
            if not self.resource:
                msg.showerror("Error", f"No se encontró el recurso '{resource_name}'")
                self.destroy()
                return

            # Obtener el inventario real para modificar
            if hasattr(self.controller, "scheduler") and hasattr(self.controller.scheduler, "inventory"):
                self.inventory = self.controller.scheduler.inventory
            else:
                # fallback: intentar obtener el inventario del controlador directamente
                self.inventory = getattr(self.controller, "inventory", None)

        except Exception as e:
            msg.showerror("Error", f"No se pudo cargar el recurso: {e}")
            self.destroy()
            return

        self.title(f"Editar recurso: {resource_name}")
        self.geometry("500x650")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Construir el formulario de edición."""
        padx, pady = 16, 12
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=padx, pady=pady)

        # Nombre (solo lectura)
        ctk.CTkLabel(main_frame, text="Nombre", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        name_entry = ctk.CTkEntry(main_frame, width=300)
        name_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=(0, 8))
        name_entry.insert(0, self.resource.name)
        name_entry.configure(state="disabled")  # No editable

        # Cantidad
        ctk.CTkLabel(main_frame, text="Cantidad", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.qty_var = tk.IntVar(value=getattr(self.resource, "quantity", 1))
        qty_spin = tk.Spinbox(main_frame, from_=0, to=9999, textvariable=self.qty_var, width=10)
        qty_spin.grid(row=1, column=1, sticky="w", padx=8, pady=(0, 8))

        # Atributos específicos según tipo
        self.specific_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.specific_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        if isinstance(self.resource, Room):
            self._build_room_fields()
        elif isinstance(self.resource, Employee):
            self._build_employee_fields()
        elif isinstance(self.resource, Item):
            self._build_item_fields()
        else:
            # Recurso genérico: solo descripción
            ctk.CTkLabel(self.specific_frame, text="Descripción", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
            self.desc_text = ctk.CTkTextbox(self.specific_frame, height=60, width=300)
            self.desc_text.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
            if hasattr(self.resource, "description"):
                self.desc_text.insert("1.0", self.resource.description)

        # Requisitos (separados por comas)
        ctk.CTkLabel(main_frame, text="Requisitos (separados por comas)", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", pady=(8, 4))
        self.requires_entry = ctk.CTkEntry(main_frame, width=300)
        self.requires_entry.grid(row=3, column=1, sticky="ew", padx=8, pady=(8, 8))
        self.requires_entry.insert(0, ", ".join(sorted(getattr(self.resource, "requires", set()))))

        # Exclusiones (separadas por comas)
        ctk.CTkLabel(main_frame, text="Exclusiones (separadas por comas)", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.excludes_entry = ctk.CTkEntry(main_frame, width=300)
        self.excludes_entry.grid(row=4, column=1, sticky="ew", padx=8, pady=(0, 8))
        self.excludes_entry.insert(0, ", ".join(sorted(getattr(self.resource, "excludes", set()))))

        # Exclusiones de categoría
        ctk.CTkLabel(main_frame, text="Exclus. Categorías (separadas por comas)", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w", pady=(0, 4))
        self.excl_cat_entry = ctk.CTkEntry(main_frame, width=300)
        self.excl_cat_entry.grid(row=5, column=1, sticky="ew", padx=8, pady=(0, 8))
        self.excl_cat_entry.insert(0, ", ".join(sorted(getattr(self.resource, "excludes_categories", set()))))

        # Botones
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(16, 0))

        ctk.CTkButton(btn_frame, text="Guardar", command=self._save_changes, width=100).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, width=100, fg_color="#999999", hover_color="#737373").pack(side="left", padx=8)

        # Configurar grid
        main_frame.grid_columnconfigure(1, weight=1)

    def _build_room_fields(self):
        """Campos específicos para Room."""
        row = 0
        ctk.CTkLabel(self.specific_frame, text="Capacidad", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        self.capacity_var = tk.IntVar(value=getattr(self.resource, "capacity", 0))
        ctk.CTkEntry(self.specific_frame, textvariable=self.capacity_var, width=80).grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        ctk.CTkLabel(self.specific_frame, text="Tipo de sala", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        self.room_type_var = tk.StringVar(value=getattr(self.resource, "room_type", ""))
        ctk.CTkEntry(self.specific_frame, textvariable=self.room_type_var, width=200).grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        ctk.CTkLabel(self.specific_frame, text="Interior", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        self.interior_var = tk.BooleanVar(value=getattr(self.resource, "interior", True))
        ctk.CTkCheckBox(self.specific_frame, text="Interior", variable=self.interior_var).grid(row=row, column=1, sticky="w", padx=8, pady=4)

    def _build_employee_fields(self):
        """Campos específicos para Employee."""
        row = 0
        ctk.CTkLabel(self.specific_frame, text="Rol", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        self.role_var = tk.StringVar(value=getattr(self.resource, "role", ""))
        ctk.CTkEntry(self.specific_frame, textvariable=self.role_var, width=200).grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        ctk.CTkLabel(self.specific_frame, text="Turno", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        self.shift_var = tk.StringVar(value=getattr(self.resource, "shift", ""))
        ctk.CTkEntry(self.specific_frame, textvariable=self.shift_var, width=200).grid(row=row, column=1, sticky="w", padx=8, pady=4)

    def _build_item_fields(self):
        """Campos específicos para Item."""
        row = 0
        ctk.CTkLabel(self.specific_frame, text="Descripción", font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w")
        self.desc_text = ctk.CTkTextbox(self.specific_frame, height=60, width=300)
        self.desc_text.grid(row=row+1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        if hasattr(self.resource, "description"):
            self.desc_text.insert("1.0", self.resource.description)

    def _parse_csv(self, s: str) -> set:
        """Convertir cadena separada por comas en conjunto de strings."""
        if not s:
            return set()
        return {x.strip() for x in s.split(",") if x.strip()}

    def _save_changes(self):
        """Aplicar los cambios al recurso y persistir."""
        try:
            # Modificar el objeto recurso en memoria
            resource = self.resource

            # Cantidad
            new_qty = self.qty_var.get()
            resource.quantity = new_qty

            # Atributos específicos
            if isinstance(resource, Room):
                resource.capacity = self.capacity_var.get()
                resource.room_type = self.room_type_var.get().strip()
                resource.interior = self.interior_var.get()
            elif isinstance(resource, Employee):
                resource.role = self.role_var.get().strip()
                resource.shift = self.shift_var.get().strip()
            elif isinstance(resource, Item):
                resource.description = self.desc_text.get("1.0", "end").strip()

            # Requisitos y exclusiones
            resource.requires = self._parse_csv(self.requires_entry.get())
            resource.excludes = self._parse_csv(self.excludes_entry.get())
            resource.excludes_categories = self._parse_csv(self.excl_cat_entry.get())

            # Persistir los cambios en el archivo JSON y recargar en el controlador
            self._persist_changes()

            msg.showinfo("Éxito", f"Recurso '{resource.name}' actualizado correctamente.")
            self.destroy()
            # Refrescar la vista padre
            if self.parent and hasattr(self.parent, "refresh"):
                self.parent.refresh()

        except Exception as e:
            msg.showerror("Error", f"No se pudo guardar los cambios: {e}")

    def _persist_changes(self):
        """Escribir el inventario actualizado al archivo JSON y actualizar el controlador."""
        # Obtener la lista de recursos serializados del inventario
        if not self.inventory:
            return

        # Serializar todos los recursos del inventario
        resources_data = [r.to_dict() for r in self.inventory.resources]

        # Leer el archivo data.json actual
        DATA = Path.home() / ".hotel_planner" / "data.json"
        try:
            if DATA.exists():
                payload = json.loads(DATA.read_text(encoding="utf-8"))
            else:
                payload = {"version": 1, "inventory": {"resources": []}, "events": []}
        except Exception:
            payload = {"version": 1, "inventory": {"resources": []}, "events": []}

        # Actualizar la sección de inventario
        payload["inventory"] = {"resources": resources_data}

        # Escribir de forma atómica
        tmp = DATA.with_name(DATA.name + ".tmp")
        DATA.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(str(tmp), str(DATA))

        # Notificar a la vista (ya se hará desde el diálogo)
        # También podemos actualizar el controlador si tiene algún método de recarga
        try:
            if self.controller and hasattr(self.controller, "load_events"):
                # Recargar eventos por si cambiaron nombres (aunque no cambiamos nombre)
                events = payload.get("events", [])
                self.controller.load_events(events)
        except Exception:
            pass

        # Emitir evento de cambio de inventario para refrescar otras vistas
        try:
            root = self.parent.winfo_toplevel() if self.parent else None
            if root:
                root.event_generate("<<InventoryChanged>>", when="tail")
        except Exception:
            pass


class InventoryView(ctk.CTkFrame):
    """
    Modern card-based inventory display.
    Displays resources as interactive cards organized by type.
    """
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        
        # Store resources and state
        self._all_resources: List[Dict[str, Any]] = []
        self._card_widgets: Dict[str, InventoryCard] = {}
        
        self._build_ui()
        
        # bind a virtual event so other views can notify us when inventory changed on disk
        try:
            root = self.winfo_toplevel()
            root.bind("<<InventoryChanged>>", lambda ev: self.refresh())
        except Exception:
            pass

    def _build_ui(self):
        """Build modern card-based UI without search/filters."""
        
        # Header with title (no add button)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))
        
        title = ctk.CTkLabel(
            header,
            text="🏨 Inventario del Hotel",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(side="left")
        
        # Simple total counter (replaces StatsDashboard)
        self.total_label = ctk.CTkLabel(
            self,
            text="Total recursos: 0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1F2937", "#E5E7EB")
        )
        self.total_label.pack(anchor="w", padx=16, pady=(0, 12))
        
        # Main scrollable content area
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        
        # Sections for each resource type
        self._sections: Dict[str, ctk.CTkFrame] = {}
        self._section_counts: Dict[str, ctk.CTkLabel] = {}
        self._resource_sections: Dict[str, ctk.CTkFrame] = {}
        
        for resource_type, emoji, label in [
            ("room", "🏠", "ESPACIOS"),
            ("employee", "👤", "EMPLEADOS"),
            ("item", "📦", "OBJETOS"),
        ]:
            section = self._create_section(resource_type, emoji, label)
            self._sections[resource_type] = section

    def _create_section(self, resource_type: str, emoji: str, label: str) -> ctk.CTkFrame:
        """Create a resource type section with header and card grid."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        section.pack(fill="x", pady=(0, 24))
        
        # Section header
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        
        section_title = ctk.CTkLabel(
            header,
            text=f"{emoji} {label}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1F2937", "#E5E7EB"),
        )
        section_title.pack(side="left")
        
        # Count badge
        count_label = ctk.CTkLabel(
            header,
            text="0 items",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#9CA3AF"),
        )
        count_label.pack(side="left", padx=(8, 0))
        self._section_counts[resource_type] = count_label
        
        # Cards grid
        cards_frame = ctk.CTkFrame(section, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        
        self._resource_sections[resource_type] = cards_frame
        
        return section

    def on_show(self):
        """Called when view is shown."""
        self.refresh()

    def refresh(self):
        """Refresh inventory display from controller."""
        if not self.controller or not hasattr(self.controller, "list_resources"):
            resources = []
        else:
            resources = list(self.controller.list_resources())

        # Clear existing cards
        for card in self._card_widgets.values():
            card.destroy()
        self._card_widgets.clear()
        
        # Convert resources to card data
        resources_by_type: Dict[str, List[Dict]] = {
            "room": [],
            "employee": [],
            "item": [],
        }
        
        for res in resources:
            category = getattr(res, "category", "") or ""
            name = getattr(res, "name", "")
            
            # Determine availability status (simplified)
            availability = self._get_availability_status(name, res)
            
            resource_data = {
                "name": name,
                "type": category,
                "status": availability,
                "details": self._extract_details(res, category),
            }
            
            if category == "room":
                resources_by_type["room"].append(resource_data)
            elif category == "employee":
                resources_by_type["employee"].append(resource_data)
            else:
                resources_by_type["item"].append(resource_data)
        
        # Update total counter
        total = len(resources)
        self.total_label.configure(text=f"Total recursos: {total}")
        
        # Display cards by type
        for resource_type, resources_list in resources_by_type.items():
            self._display_cards_for_type(resource_type, resources_list)
            
            # Update count badge
            if resource_type in self._section_counts:
                count_text = f"{len(resources_list)} item{'s' if len(resources_list) != 1 else ''}"
                self._section_counts[resource_type].configure(text=count_text)

    def _get_availability_status(self, name: str, res: Any) -> str:
        """Determine resource availability status (simplified)."""
        if hasattr(res, "available") and not res.available:
            return "in_use"
        return "available"

    def _extract_details(self, res: Any, category: str) -> Dict[str, Any]:
        """Extract key details to display in card."""
        details = {}
        
        if category == "room":
            if hasattr(res, "capacity"):
                details["Capacidad"] = res.capacity
            if hasattr(res, "room_type"):
                details["Tipo"] = res.room_type
            if hasattr(res, "interior"):
                details["Interior/Exterior"] = "Interior" if res.interior else "Exterior"
        
        elif category == "employee":
            if hasattr(res, "role"):
                details["Rol"] = res.role
            if hasattr(res, "shift"):
                details["Turno"] = res.shift
        
        # Common fields
        if hasattr(res, "quantity") and res.quantity:
            details["Cantidad"] = res.quantity
        
        if hasattr(res, "requires") and res.requires:
            details["Requiere"] = ", ".join(sorted(res.requires))
        
        return details

    def _display_cards_for_type(self, resource_type: str, resources_list: List[Dict]):
        """Display cards for a resource type in a grid."""
        if resource_type not in self._resource_sections:
            return
        
        cards_frame = self._resource_sections[resource_type]
        
        # Clear previous cards (just in case)
        for child in cards_frame.winfo_children():
            child.destroy()
        
        # Create cards in grid
        for idx, resource_data in enumerate(resources_list):
            card = InventoryCard(
                cards_frame,
                title=resource_data["name"],
                resource_type=resource_data["type"].capitalize(),
                details=resource_data["details"],
                status=resource_data["status"],
                on_edit=self._on_edit_resource,
                on_delete=self._on_delete_resource,
            )
            
            row = idx // 3
            col = idx % 3
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            
            # Configure grid weights for uniform distribution
            cards_frame.grid_rowconfigure(row, weight=1)
            for c in range(3):
                cards_frame.grid_columnconfigure(c, weight=1)
            
            self._card_widgets[resource_data["name"]] = card

    def _on_edit_resource(self, resource_name: str):
        """Handle edit button on card: open edit dialog."""
        try:
            dialog = EditResourceDialog(self, self.controller, resource_name)
            dialog.focus()
        except Exception as e:
            msg.showerror("Error", f"No se pudo abrir el editor: {e}")

    def _on_delete_resource(self, resource_name: str):
        """Handle delete button on card."""
        if not msg.askyesno("Confirmar eliminación", f"¿Eliminar recurso '{resource_name}' del inventario?"):
            return
        
        # Attempt deletion
        try:
            if self.controller and hasattr(self.controller, "remove_resource"):
                ok = self.controller.remove_resource(resource_name)
                if isinstance(ok, tuple):
                    ok = ok[0]
                if ok:
                    msg.showinfo("Ok", f"Recurso '{resource_name}' eliminado.")
                    self.refresh()
                    return
        except Exception:
            pass
        
        # Fallback to direct JSON manipulation (same as before)
        self._delete_resource_from_json(resource_name)

    def _delete_resource_from_json(self, name: str):
        """Delete resource directly from JSON data file."""
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
                msg.showwarning("No encontrado", f"No se encontró '{name}' en el inventario.")
                return
            
            payload["inventory"] = {"resources": resources}

            # Remove events using this resource
            evs = payload.get("events", []) or []
            keep = []
            removed_count = 0
            target = name.strip().lower()
            
            for ev in evs:
                try:
                    ev_resources = ev.get("resources", []) if isinstance(ev, dict) else []
                    used = any(
                        (er.get("name") if isinstance(er, dict) else getattr(er, "name", "")).strip().lower() == target
                        for er in ev_resources
                    )
                    if not used:
                        keep.append(ev)
                    else:
                        removed_count += 1
                except Exception:
                    keep.append(ev)
            
            if removed_count > 0:
                payload["events"] = keep

            # Write atomically
            tmp = DATA.with_name(DATA.name + ".tmp")
            DATA.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(str(tmp), str(DATA))

            # Reload inventory
            try:
                inv_payload = {"version": payload.get("version", 1), "resources": (payload.get("inventory") or {}).get("resources", [])}
                tmp_name = f"hotel_planner_inv_{os.getpid()}_{uuid.uuid4().hex}.json"
                tmp_path = Path(tempfile.gettempdir()) / tmp_name
                tmp_path.write_text(json.dumps(inv_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                try:
                    new_inv = inv_store.load_inventory_from_json(tmp_path)
                    if self.controller:
                        if hasattr(self.controller, "scheduler"):
                            setattr(self.controller.scheduler, "inventory", new_inv)
                        setattr(self.controller, "inventory", new_inv)
                except Exception:
                    pass
                finally:
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
            except Exception:
                pass

            # Notify listeners
            try:
                if removed_count > 0 and self.controller and hasattr(self.controller, "load_events"):
                    self.controller.load_events(payload.get("events", []))
                root = self.winfo_toplevel()
                root.event_generate("<<InventoryChanged>>", when="tail")
                if removed_count > 0:
                    root.event_generate("<<EventsChanged>>", when="tail")
            except Exception:
                pass

            msg.showinfo("Ok", f"Recurso '{name}' eliminado.")
            self.refresh()

        except Exception as e:
            msg.showerror("Error", f"No se pudo eliminar '{name}': {e}")