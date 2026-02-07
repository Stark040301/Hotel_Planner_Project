import json
import os
import tempfile
import uuid
import tkinter as tk
import tkinter.messagebox as msg
import tkinter.ttk as ttk
import customtkinter as ctk
from pathlib import Path
from typing import Optional

from hotel_planner.models import inventory_store as inv_store

class AddRemoveResourceView(ctk.CTkFrame):
    """Pantalla para añadir recursos al inventario."""
    def __init__(self, master, controller: Optional[object] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        self.title = ctk.CTkLabel(self, text="Añadir Recurso", font=ctk.CTkFont(size=18, weight="bold"))
        self.title.pack(anchor="nw", padx=16, pady=12)

        form = ctk.CTkFrame(self)
        form.pack(anchor="nw", padx=16, pady=8, fill="x")

        # Tipo (Room / Employee / Item)
        ctk.CTkLabel(form, text="Tipo").grid(row=0, column=0, sticky="w")
        self.type_var = tk.StringVar(value="Item")
        ttk.Combobox(form, textvariable=self.type_var, values=["Room", "Employee", "Item"], state="readonly", width=18).grid(row=0, column=1, padx=8, pady=6, sticky="w")

        # Nombre
        ctk.CTkLabel(form, text="Nombre").grid(row=1, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self.name_var, width=480).grid(row=1, column=1, columnspan=3, padx=8, pady=6, sticky="w")

        # Cantidad
        ctk.CTkLabel(form, text="Cantidad").grid(row=2, column=0, sticky="w")
        self.qty_var = tk.IntVar(value=1)
        tk.Spinbox(form, from_=0, to=9999, textvariable=self.qty_var, width=8).grid(row=2, column=1, padx=8, pady=6, sticky="w")

        # Descripción / rol / capacity
        ctk.CTkLabel(form, text="Descripción / Atributos").grid(row=3, column=0, sticky="nw")
        self.desc_txt = tk.Text(form, height=4, width=60)
        self.desc_txt.grid(row=3, column=1, columnspan=3, padx=8, pady=6, sticky="w")

        # Campos específicos para Room / Employee hints
        ctk.CTkLabel(form, text="Room: capacity, room_type, interior (ej: 120,recepción,True)").grid(row=4, column=1, columnspan=3, sticky="w", padx=8)

        ctk.CTkLabel(form, text="Employee: role, shift (ej: recepción,rotativo)").grid(row=5, column=1, columnspan=3, sticky="w", padx=8)

        # Requires / Excludes (comma separated)
        ctk.CTkLabel(form, text="Requires (comma separated)").grid(row=6, column=0, sticky="w")
        self.requires_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self.requires_var, width=480).grid(row=6, column=1, columnspan=3, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Excludes (comma separated)").grid(row=7, column=0, sticky="w")
        self.excludes_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self.excludes_var, width=480).grid(row=7, column=1, columnspan=3, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Excludes categories (comma separated)").grid(row=8, column=0, sticky="w")
        self.excl_cat_var = tk.StringVar()
        ctk.CTkEntry(form, textvariable=self.excl_cat_var, width=480).grid(row=8, column=1, columnspan=3, padx=8, pady=6, sticky="w")

        # actions
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=16, pady=(8,12))
        save_btn = ctk.CTkButton(actions, text="Guardar recurso", command=self._on_save, width=160)
        save_btn.pack(side="right", padx=6)
        cancel_btn = ctk.CTkButton(actions, text="Cancelar", command=self._on_cancel, width=120, fg_color="#999")
        cancel_btn.pack(side="right", padx=6)

    def _on_cancel(self):
        self.name_var.set("")
        self.qty_var.set(1)
        self.desc_txt.delete("1.0", "end")
        self.requires_var.set("")
        self.excludes_var.set("")
        self.excl_cat_var.set("")
        self.type_var.set("Item")

    def _parse_csv(self, s: str):
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    def _build_resource_dict(self):
        typ = self.type_var.get()
        base = {
            "type": typ,
            "category": "item" if typ == "Item" else ("room" if typ == "Room" else "employee"),
            "name": self.name_var.get().strip(),
            "quantity": int(self.qty_var.get() or 0),
        }
        desc = self.desc_txt.get("1.0", "end").strip()
        if typ == "Room":
            # allow user to include "capacity,room_type,interior" in desc first line if provided
            parts = [p.strip() for p in desc.split(",")]
            if parts and parts[0].isdigit():
                base["capacity"] = int(parts[0])
            if len(parts) > 1 and parts[1]:
                base["room_type"] = parts[1]
            if len(parts) > 2:
                base["interior"] = parts[2].lower() in ("1", "true", "yes")
        elif typ == "Employee":
            parts = [p.strip() for p in desc.split(",")]
            if parts and parts[0]:
                base["role"] = parts[0]
            if len(parts) > 1 and parts[1]:
                base["shift"] = parts[1]
        else:
            if desc:
                base["description"] = desc
        reqs = self._parse_csv(self.requires_var.get())
        exs = self._parse_csv(self.excludes_var.get())
        excats = self._parse_csv(self.excl_cat_var.get())
        if reqs:
            base["requires"] = reqs
        if exs:
            base["excludes"] = exs
        if excats:
            base["excludes_categories"] = excats
        return base

    def _write_working_inventory(self, resource_dict):
        # always write to single combined file ~/.hotel_planner/data.json
        COMBINED = Path.home() / ".hotel_planner" / "data.json"
        try:
            try:
                payload = json.loads(COMBINED.read_text(encoding="utf-8")) if COMBINED.exists() else {"version": 1, "inventory": {"resources": []}, "events": []}
            except Exception:
                payload = {"version": 1, "inventory": {"resources": []}, "events": []}
            inv = payload.get("inventory") or {"resources": []}
            resources = inv.get("resources", [])
            resources.append(resource_dict)
            payload["inventory"] = {"resources": resources}
            tmp = COMBINED.with_name(COMBINED.name + ".tmp")
            COMBINED.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(str(tmp), str(COMBINED))
        except Exception as e:
            raise

    def _on_save(self):
        name = self.name_var.get().strip()
        if not name:
            msg.showerror("Error", "El recurso necesita un nombre.")
            return
        r = self._build_resource_dict()

        # --- comprobación: no permitir duplicados por nombre (case-insensitive) ---
        existing_names = set()
        try:
            if self.controller and hasattr(self.controller, "list_resources"):
                for res in list(self.controller.list_resources()):
                    if isinstance(res, dict):
                        n = res.get("name")
                    else:
                        n = getattr(res, "name", None)
                    if n:
                        existing_names.add(n.strip().lower())
        except Exception:
            existing_names = set()

        # fallback: leer combined data.json si controller no devolvió nada
        if not existing_names:
            try:
                COMBINED = Path.home() / ".hotel_planner" / "data.json"
                if COMBINED.exists():
                    payload = json.loads(COMBINED.read_text(encoding="utf-8") or "{}")
                    resources_list = (payload.get("inventory") or {}).get("resources", []) or []
                    for rr in resources_list:
                        n = rr.get("name") if isinstance(rr, dict) else getattr(rr, "name", None)
                        if n:
                            existing_names.add(str(n).strip().lower())
            except Exception:
                pass

        if name.strip().lower() in existing_names:
            msg.showerror("Error", f"Ya existe un recurso con el nombre '{name}'. Elige otro nombre o elimina el existente.")
            return
        # --- fin comprobación ---

        # try controller API first
        try:
            if self.controller:
                # prefer a generic add_resource or type-specific methods
                if hasattr(self.controller, "add_resource"):
                    ok, info = self.controller.add_resource(r)
                    if ok:
                        msg.showinfo("Ok", "Recurso añadido.")
                        return
                    else:
                        msg.showerror("Error", f"No se pudo añadir: {info}")
                        return
                # fallbacks
                if hasattr(self.controller, "add_item") and r.get("type") == "Item":
                    ok, info = self.controller.add_item(**r)
                    if ok:
                        msg.showinfo("Ok", "Item añadido.")
                        return
                if hasattr(self.controller, "add_room") and r.get("type") == "Room":
                    ok, info = self.controller.add_room(**r)
                    if ok:
                        msg.showinfo("Ok", "Room añadido.")
                        return
                if hasattr(self.controller, "add_employee") and r.get("type") == "Employee":
                    ok, info = self.controller.add_employee(**r)
                    if ok:
                        msg.showinfo("Ok", "Employee añadido.")
                        return
        except Exception:
            pass

        # fallback: write directly to combined data.json
        try:
            self._write_working_inventory(r)

            # reload combined inventory and update runtime objects so UI sees change immediately
            COMBINED = Path.home() / ".hotel_planner" / "data.json"
            new_inv = None
            try:
                if COMBINED.exists():
                    payload = json.loads(COMBINED.read_text(encoding="utf-8") or "{}")
                    inv_payload = {"version": payload.get("version", 1), "resources": (payload.get("inventory") or {}).get("resources", [])}
                    # write ephemeral file and load via inv_store to get Inventory object
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

            # try to update controller/scheduler in-memory inventory
            try:
                if self.controller and new_inv is not None:
                    # scheduler preferred
                    if hasattr(self.controller, "scheduler") and getattr(self.controller, "scheduler", None) is not None:
                        try:
                            setattr(self.controller.scheduler, "inventory", new_inv)
                        except Exception:
                            pass
                    # also set top-level controller.inventory if present
                    try:
                        setattr(self.controller, "inventory", new_inv)
                    except Exception:
                        pass
            except Exception:
                pass

            # notify UI: refresh resource-name caches and broadcast event so views refresh
            try:
                # update combobox caches in this view
                self._refresh_resource_names()
            except Exception:
                pass

            try:
                root = self.winfo_toplevel()
                # broadcast custom virtual event; InventoryView binds to this and will refresh
                root.event_generate("<<InventoryChanged>>", when="tail")
            except Exception:
                pass

            msg.showinfo("Ok", "Recurso añadido al inventario.")
            # clear form
            self._on_cancel()
        except Exception as e:
            msg.showerror("Error", f"No se pudo guardar recurso: {e}")
            return

    def on_show(self):
        # no-op but could refresh suggestions/autocompletes
        pass