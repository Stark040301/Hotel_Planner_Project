import json, shutil, os
from pathlib import Path
from typing import Dict, Any, Tuple

def write_default_if_missing(default_path: Path, content: Dict[str, Any]):
    default_path.parent.mkdir(parents=True, exist_ok=True)
    if not default_path.exists():
        with default_path.open("w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

def ensure_working_copy(default_path: Path, working_path: Path) -> Path:
    working_path.parent.mkdir(parents=True, exist_ok=True)
    if not working_path.exists():
        shutil.copyfile(str(default_path), str(working_path))
    else:
        # comprobar JSON válido
        try:
            with working_path.open("r", encoding="utf-8") as fh:
                json.load(fh)
        except Exception:
            shutil.copyfile(str(default_path), str(working_path))
    return working_path

def load_data(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    # normalizar estructura: permitir antiguos formatos
    out = {"version": payload.get("version", 1), "inventory": None, "events": []}
    if "inventory" in payload or "resources" in payload:
        # combined format or partial
        if "inventory" in payload:
            inv = payload["inventory"]
        else:
            inv = {"resources": payload.get("resources", [])}
        out["inventory"] = inv
    if "events" in payload:
        out["events"] = payload["events"] or []
    # fallback: if file only had events or only had resources, caller handles
    return out

def save_data(payload: Dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(str(tmp), str(path))

def migrate_from_separate(inventory_path: Path, events_path: Path, target_path: Path) -> Path:
    data = {"version": 1, "inventory": {"resources": []}, "events": []}
    if inventory_path.exists():
        try:
            with inventory_path.open("r", encoding="utf-8") as f:
                inv = json.load(f)
                data["inventory"]["resources"] = inv.get("resources", [])
        except Exception:
            pass
    if events_path.exists():
        try:
            with events_path.open("r", encoding="utf-8") as f:
                ev = json.load(f)
                data["events"] = ev.get("events", [])
        except Exception:
            pass
    save_data(data, target_path)
    return target_path