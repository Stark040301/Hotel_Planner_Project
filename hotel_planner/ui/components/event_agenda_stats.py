"""Statistics dashboard for planned events."""

from typing import Dict

import customtkinter as ctk


class EventAgendaStats(ctk.CTkFrame):
    """Overview cards for event counts."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.total = 0
        self.upcoming = 0
        self.active = 0
        self.completed = 0
        self.configure(fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        title = ctk.CTkLabel(
            self,
            text="📊 RESUMEN DE EVENTOS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1F2937", "#E5E7EB"),
        )
        title.pack(anchor="w", padx=16, pady=(12, 8))

        self.cards = ctk.CTkFrame(self, fg_color="transparent")
        self.cards.pack(fill="x", padx=16, pady=(0, 12))

        self._card_defs = [
            ("Total", "total", "#6B7280"),
            ("Próximos", "upcoming", "#2563EB"),
            ("En curso", "active", "#059669"),
            ("Finalizados", "completed", "#6B7280"),
        ]
        self._labels: Dict[str, ctk.CTkLabel] = {}

        for label, key, color in self._card_defs:
            card = ctk.CTkFrame(
                self.cards,
                fg_color=("#F3F4F6", "#2A2A2A"),
                corner_radius=6,
                border_color=("#E5E7EB", "#3A3A3A"),
                border_width=1,
            )
            card.pack(side="left", fill="both", expand=True, padx=6)

            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#6B7280", "#9CA3AF"),
            ).pack(pady=(8, 4), padx=12)

            value = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=color,
            )
            value.pack(pady=(0, 8), padx=12)
            self._labels[key] = value

    def update_stats(self, total: int, upcoming: int, active: int, completed: int):
        self.total = total
        self.upcoming = upcoming
        self.active = active
        self.completed = completed
        self._labels["total"].configure(text=str(total))
        self._labels["upcoming"].configure(text=str(upcoming))
        self._labels["active"].configure(text=str(active))
        self._labels["completed"].configure(text=str(completed))
