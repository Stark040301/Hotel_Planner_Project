"""Search and filter toolbar for planned events."""

from typing import Callable, Optional

import tkinter as tk
import customtkinter as ctk


class EventAgendaToolbar(ctk.CTkFrame):
    """Toolbar with search, status filters, and actions."""

    def __init__(
        self,
        master,
        on_search: Optional[Callable[[str], None]] = None,
        on_filter_status: Optional[Callable[[str], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_search = on_search
        self.on_filter_status = on_filter_status
        self.on_clear = on_clear
        self.current_status_filter = "all"
        self.status_buttons = {}
        self._entry = None
        self.configure(fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        search_box = ctk.CTkFrame(
            row,
            fg_color=("#F3F4F6", "#2A2A2A"),
            border_color=("#E5E7EB", "#3A3A3A"),
            border_width=1,
            corner_radius=6,
        )
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkLabel(search_box, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=12, pady=8)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._emit_search)
        self._entry = ctk.CTkEntry(
            search_box,
            textvariable=self.search_var,
            placeholder_text="Buscar eventos, recursos o notas...",
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=13),
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)

        buttons = ctk.CTkFrame(row, fg_color="transparent")
        buttons.pack(side="left")

        for key, emoji, label in [
            ("all", "🔹", "Todos"),
            ("upcoming", "🟦", "Próximos"),
            ("active", "🟢", "En curso"),
            ("completed", "⚪", "Finalizados"),
        ]:
            btn = ctk.CTkButton(
                buttons,
                text=f"{emoji} {label}",
                font=ctk.CTkFont(size=11, weight="bold"),
                height=32,
                width=116,
                corner_radius=6,
                fg_color=("#2563EB" if key == "all" else "#F3F4F6"),
                text_color=("white" if key == "all" else "#1F2937"),
                hover_color=("#1D4ED8" if key == "all" else "#E5E7EB"),
                command=lambda s=key: self._set_filter(s),
            )
            btn.pack(side="left", padx=4)
            self.status_buttons[key] = btn

        clear_btn = ctk.CTkButton(
            row,
            text="↺ Limpiar",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            width=98,
            corner_radius=6,
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=self._clear_all,
        )
        clear_btn.pack(side="right")

    def _emit_search(self, *args):
        if self.on_search:
            self.on_search(self.search_var.get())

    def _set_filter(self, status: str):
        self.current_status_filter = status
        for key, btn in self.status_buttons.items():
            if key == status:
                btn.configure(fg_color="#2563EB", text_color="white", hover_color="#1D4ED8")
            else:
                btn.configure(fg_color="#F3F4F6", text_color="#1F2937", hover_color="#E5E7EB")
        if self.on_filter_status:
            self.on_filter_status(status)

    def _clear_all(self):
        self.search_var.set("")
        self._set_filter("all")
        if self.on_clear:
            self.on_clear()

    def get_search_text(self) -> str:
        return self.search_var.get()

    def focus_search(self):
        if self._entry is not None:
            self._entry.focus()
