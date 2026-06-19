import customtkinter as ctk
from typing import List, Callable, Optional

class VerticalSegmentedButton(ctk.CTkFrame):
    """
    Simple segmented control vertical hecho con CTkButton.
    Uso:
      vs = VerticalSegmentedButton(parent, ["A","B","C"], command=callback)
      vs.pack(...)
      vs.set("B")
      v = vs.get()
    """
    def __init__(
        self,
        master,
        values: List[str],
        command: Optional[Callable[[str], None]] = None,
        width: int = 160,
        btn_height: int = 36,
        corner_radius: int = 8,
        fg_active: str = "#005f73",
        fg_inactive: str = None,
        text_color_active: str = "white",
        text_color_inactive: str = None,
        *args, **kwargs
    ):
        super().__init__(master, *args, **kwargs)
        self._values = list(values)
        self._command = command
        self._buttons = {}
        self._selected = None
        self._width = width
        self._btn_height = btn_height
        self._corner_radius = corner_radius
        self._fg_active = fg_active
        # fg_color del frame sí suele existir; si no, usar None
        try:
            self._fg_inactive = fg_inactive or self.cget("fg_color")
        except Exception:
            self._fg_inactive = fg_inactive or None
        self._text_active = text_color_active
        # obtener color de texto por defecto desde un widget que soporte text_color (CTkLabel),
        # con fallback a negro si algo falla
        if text_color_inactive:
            self._text_inactive = text_color_inactive
        else:
            try:
                tmp = ctk.CTkLabel(self)
                self._text_inactive = tmp.cget("text_color")
                tmp.destroy()
            except Exception:
                self._text_inactive = "black"

        # crear botones verticalmente
        for i, v in enumerate(self._values):
            b = ctk.CTkButton(
                master=self,
                text=str(v),
                width=self._width,
                height=self._btn_height,
                corner_radius=self._corner_radius,
                command=lambda _v=v: self._on_click(_v),
            )
            b.pack(side="top", fill="x", padx=0, pady=(0 if i==0 else 6))
            self._buttons[v] = b

        # seleccionar el primero por defecto
        if self._values:
            self.set(self._values[0])

    def _on_click(self, value: str):
        self.set(value)
        if self._command:
            try:
                self._command(value)
            except Exception:
                pass

    def set(self, value: str):
        """Selecciona un valor (actualiza estilos)."""
        if value not in self._buttons:
            return
        self._selected = value
        for v, btn in self._buttons.items():
            if v == value:
                btn.configure(fg_color=self._fg_active, text_color=self._text_active)
            else:
                btn.configure(fg_color=self._fg_inactive, text_color=self._text_inactive)

    def get(self) -> Optional[str]:
        return self._selected

    def values(self) -> List[str]:
        return list(self._values)