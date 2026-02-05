from typing import Iterable, List, Set, Tuple, Dict, Union

class Resource:
    """
    Clase base para todos los recursos del hotel.
    Representa cualquier activo limitado que puede ser asignado a un evento.

    Nuevas capacidades:
      - requires: nombres de recursos que deben acompañar a este recurso.
      - excludes: nombres de recursos que no pueden coexistir con este recurso.
      - excludes_categories: categorías que no pueden coexistir con este recurso.
    """
    def __init__(
        self,
        name: str,
        category: str,
        quantity: int = 1,
        *,
        requires: Iterable[str] = None,
        excludes: Iterable[str] = None,
        excludes_categories: Iterable[str] = None
    ):
        if not name or not isinstance(name, str):
            raise ValueError("name debe ser un string no vacío")
        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError("quantity debe ser int >= 0")
        self.name = name
        self.category = category  # 'room', 'employee', o 'item'
        self._quantity = quantity
        self.available = quantity > 0

        # metadata de restricciones (normalizado a lower-case strings)
        self.requires: Set[str] = set(
            n.strip().lower() for n in (requires or []) if n and isinstance(n, str)
        )
        self.excludes: Set[str] = set(
            n.strip().lower() for n in (excludes or []) if n and isinstance(n, str)
        )
        self.excludes_categories: Set[str] = set(
            n.strip().lower() for n in (excludes_categories or []) if n and isinstance(n, str)
        )

    def mark_unavailable(self):
        """Marca el recurso como no disponible."""
        self.available = False

    def mark_available(self):
        """Marca el recurso como disponible."""
        self.available = True

    @property
    def is_available(self):
        return self.available

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("quantity debe ser int >= 0")
        self._quantity = value
        self.available = self._quantity > 0

    def __repr__(self):
        estado = "Disponible" if self.available else "Ocupado"
        return f"<{self.__class__.__name__}: {self.name} ({estado})>"

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "category": self.category,
            "quantity": self._quantity,
            "available": self.available,
            "requires": sorted(self.requires),
            "excludes": sorted(self.excludes),
            "excludes_categories": sorted(self.excludes_categories),
        }

# -------------------------------------------------------------------
# 🏨 ESPACIOS FÍSICOS
# -------------------------------------------------------------------
class Room(Resource):
    """
    Representa un espacio físico dentro del hotel (interior o exterior).
    """
    def __init__(self, name, capacity, room_type="estándar", interior=True):
        super().__init__(name, category="room", quantity=1)
        if not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity debe ser int >= 1")
        self.capacity = capacity
        self.room_type = room_type
        self.interior = bool(interior)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "capacity": self.capacity,
            "room_type": self.room_type,
            "interior": self.interior
        })
        return data

# -------------------------------------------------------------------
# 👨‍💼 PERSONAL
# -------------------------------------------------------------------
class Employee(Resource):
    """
    Representa a un miembro del personal del hotel.
    """
    def __init__(self, name, role, shift="diurno"):
        super().__init__(name, category="employee", quantity=1)
        if not role or not isinstance(role, str):
            raise ValueError("role debe ser un string no vacío")
        self.role = role
        self.shift = shift

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "role": self.role,
            "shift": self.shift
        })
        return data

# -------------------------------------------------------------------
# 🎛️ EQUIPOS Y MATERIALES
# -------------------------------------------------------------------
class Item(Resource):
    """
    Representa un equipo o material del inventario.
    """
    def __init__(self, name, description=None, quantity=1, **kwargs):
        super().__init__(name, category="item", quantity=quantity, **kwargs)
        self.description = description

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "description": self.description
        })
        return data

# -------------------------
# Helpers de validación
# -------------------------
def _norm_name(n: Union[str, 'Resource']) -> str:
    return n.name.strip().lower() if hasattr(n, "name") else str(n).strip().lower()


def validate_resource_constraints(
    selected: Iterable[Union['Resource', str]],
    all_resources: Iterable['Resource']
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Valida restricciones de co-requisito y exclusión mutua para una selección de recursos.

    Returns:
      - (True, {}) si OK
      - (False, errors) donde errors puede contener:
          "missing_requires": {resource_name: [missing_required_names, ...], ...}
          "mutual_exclusion": [{ "resource": r, "conflicts_with": [other_names...] }, ...]
    """
    name_map: Dict[str, Resource] = {res.name.strip().lower(): res for res in all_resources}
    sel_names: Set[str] = set(_norm_name(s) for s in selected)

    errors: Dict[str, List] = {}
    missing = {}
    conflicts = []

    # Co-requisite check
    for nm in list(sel_names):
        res = name_map.get(nm)
        if not res:
            continue
        for req in res.requires:
            if req not in sel_names:
                missing.setdefault(res.name, []).append(req)

    if missing:
        errors["missing_requires"] = missing

    # Mutual exclusion check
    for nm in list(sel_names):
        res = name_map.get(nm)
        if not res:
            continue
        violated = []
        # excludes by name
        for ex in res.excludes:
            if ex in sel_names and ex in name_map:
                violated.append(name_map[ex].name)
        # excludes by category
        if res.excludes_categories:
            for other_nm in sel_names:
                other = name_map.get(other_nm)
                if other and other.category and other.category.strip().lower() in res.excludes_categories:
                    violated.append(other.name)
        if violated:
            conflicts.append({"resource": res.name, "conflicts_with": sorted(set(violated))})

    if conflicts:
        errors["mutual_exclusion"] = conflicts

    if errors:
        return (False, errors)
    return (True, {})
