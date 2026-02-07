import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

def write_default_if_missing(default_path: Path, content: Dict[str, Any]):
    default_path.parent.mkdir(parents=True, exist_ok=True)
    if not default_path.exists():
        with default_path.open("w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

def ensure_working_copy(default_path: Path, working_path: Path) -> Path:
    working_path.parent.mkdir(parents=True, exist_ok=True)

    def _is_valid_json(p: Path) -> bool:
        try:
            with p.open("r", encoding="utf-8") as fh:
                json.load(fh)
            return True
        except Exception:
            return False

    if not working_path.exists():
        shutil.copyfile(str(default_path), str(working_path))
        return working_path

    if not _is_valid_json(working_path):
        shutil.copyfile(str(default_path), str(working_path))
    return working_path

def load_events_from_json(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("events", [])

def save_events_to_json(events: List[Dict[str, Any]], path: Path):
    payload = {"version": 1, "events": events}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)