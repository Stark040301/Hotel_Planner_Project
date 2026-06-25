"""Inventory statistics dashboard component."""

import customtkinter as ctk
from typing import Dict, Optional


class StatsDashboard(ctk.CTkFrame):
    """
    Dashboard showing inventory overview statistics.
    
    Displays:
    - Total items count
    - Available count
    - In use count
    - Unavailable count
    - Visual progress indicators
    """

    def __init__(
        self,
        master,
        total: int = 0,
        available: int = 0,
        in_use: int = 0,
        unavailable: int = 0,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self.total = total
        self.available = available
        self.in_use = in_use
        self.unavailable = unavailable

        self.configure(
            fg_color="transparent",
            corner_radius=0,
        )

        self._build_ui()

    def _build_ui(self):
        """Build statistics dashboard."""
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="📊 RESUMEN DEL INVENTARIO",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1F2937", "#E5E7EB"),
        )
        title.pack(anchor="w", padx=16, pady=(12, 8))

        # Stats container
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=16, pady=(0, 12))

        # Create stat cards
        stats = [
            ("Total", self.total, "#6B7280"),
            ("Disponibles", self.available, "#059669"),
            ("En Uso", self.in_use, "#D97706"),
            ("No Disponibles", self.unavailable, "#DC2626"),
        ]

        for label, count, color in stats:
            self._create_stat_card(stats_frame, label, count, color)

    def _create_stat_card(self, parent, label: str, count: int, color: str):
        """Create a single stat card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=("#F3F4F6", "#2A2A2A"),
            corner_radius=6,
            border_color=("#E5E7EB", "#3A3A3A"),
            border_width=1,
        )
        card.pack(side="left", fill="both", expand=True, padx=6)

        # Label
        label_widget = ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#6B7280", "#9CA3AF"),
        )
        label_widget.pack(pady=(8, 4), padx=12)

        # Count (colored)
        count_widget = ctk.CTkLabel(
            card,
            text=str(count),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=color,
        )
        count_widget.pack(pady=(0, 8), padx=12)

    def update_stats(
        self,
        total: int,
        available: int,
        in_use: int,
        unavailable: int,
    ):
        """Update statistics and refresh display."""
        self.total = total
        self.available = available
        self.in_use = in_use
        self.unavailable = unavailable

        # Clear and rebuild
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
