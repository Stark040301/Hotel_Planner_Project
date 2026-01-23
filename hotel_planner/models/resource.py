class Resource:
    """
    Clase base para todos los recursos del hotel.
    Representa cualquier activo limitado que puede ser asignado a un evento.
    """
    def __init__(self, name, category, quantity = 1):
        if not name or not isinstance(name, str):
            raise ValueError("name debe ser un string no vacío")
        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError("quantity debe ser int >= 0")
        self.name = name
        self.category = category  # 'room', 'employee', o 'item'
        self._quantity = quantity
        self.available = quantity > 0

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
            "available": self.available
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
    def __init__(self, name, description=None, quantity=1):
        super().__init__(name, category="item", quantity=quantity)
        self.description = description
        
    def to_dict(self):
        data = super().to_dict()
        data.update({
            "description": self.description
        })
        return data
