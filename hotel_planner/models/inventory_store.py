import json, shutil
from pathlib import Path
from typing import Dict, Any
from .inventory import Inventory
from .resource import Room, Employee, Item, Resource

def write_default_if_missing(default_path: Path, content: Dict[str, Any]):
    default_path.parent.mkdir(parents=True, exist_ok=True)
    if not default_path.exists():
        with default_path.open("w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

def ensure_working_copy(default_path: Path, working_path: Path) -> Path:
    working_path.parent.mkdir(parents=True, exist_ok=True)
    if not working_path.exists():
        shutil.copyfile(str(default_path), str(working_path))
    return working_path

def load_inventory_from_json(path: Path) -> Inventory:
    inv = Inventory()
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    for rd in payload.get("resources", []):
        rtype = rd.get("type", "").lower()
        name = rd.get("name")
        qty = int(rd.get("quantity", 1))
        requires = rd.get("requires", []) or []
        excludes = rd.get("excludes", []) or []
        excat = rd.get("excludes_categories", []) or []
        try:
            if rtype == "room" or rd.get("category","").lower()=="room":
                r = Room(name, int(rd.get("capacity",1)), room_type=rd.get("room_type","estándar"), interior=bool(rd.get("interior",True)))
                r.quantity = qty
            elif rtype == "employee" or rd.get("category","").lower()=="employee":
                r = Employee(name, rd.get("role",""), shift=rd.get("shift","diurno"))
                r.quantity = qty
            else:
                r = Item(name, description=rd.get("description"), quantity=qty)
        except Exception:
            r = Resource(name=name, category=rd.get("category","item"), quantity=qty)
        # aplicar metadatos (normalización en Resource)
        try:
            r.requires.update(n.strip().lower() for n in requires if n)
            r.excludes.update(n.strip().lower() for n in excludes if n)
            r.excludes_categories.update(n.strip().lower() for n in excat if n)
        except Exception:
            pass
        inv.add_resource(r)
    return inv

def save_inventory_to_json(inv: Inventory, path: Path):
    payload = {"version": 1, "resources": [r.to_dict() for r in getattr(inv, "resources", [])]}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)