class Resource:
    """
    Clase base para todos los recursos del hotel.
    Representa cualquier activo limitado que puede ser asignado a un evento.
    """
    def __init__(self, name, category, quantity = 1):
        if not name or not isinstance(name, str):
            raise ValueError("El nombre del recurso debe ser una cadena no vacía.")
        if quantity < 1:
            raise ValueError("La cantidad de un recurso debe ser al menos 1.")
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
        if value < 0:
            raise ValueError("La cantidad no puede ser negativa")
        self._quantity = value
        self.available = value > 0

    def __repr__(self):
        estado = "Disponible" if self.available else "Ocupado"
        return f"<{self.__class__.__name__}: {self.name} ({estado})>"
    
    def to_dict(self):
        """Convierte el recurso a un diccionario serializable."""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
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
        super().__init__(name, category="room")
        self.capacity = capacity
        self.room_type = room_type
        self.interior = interior  # True = interior, False = exterior

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
        super().__init__(name, category="employee")
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
    def __init__(self, name, description=None):
        super().__init__(name, category="item")
        self.description = description
        
    def to_dict(self):
        data = super().to_dict()
        data.update({"description": self.description})
        return data
