"""Modern search and filter bar for inventory."""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, List


class SearchBar(ctk.CTkFrame):
    """
    Modern search and filter interface for inventory.
    
    Features:
    - Real-time search with live filtering
    - Status filter buttons (Available, In Use, Unavailable)
    - Sort options
    - Clear filters button
    - Keyboard support (Ctrl+F to focus, etc.)
    """

    def __init__(
        self,
        master,
        on_search: Optional[Callable[[str], None]] = None,
        on_filter_status: Optional[Callable[[str], None]] = None,
        on_sort: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self.on_search = on_search
        self.on_filter_status = on_filter_status
        self.on_sort = on_sort

        self.current_status_filter = "all"
        self.current_sort = "name"

        self.configure(
            fg_color="transparent",
            corner_radius=0,
        )

        self._build_ui()

    def _build_ui(self):
        """Build search bar UI."""
        
        # Search input section
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=12)

        # Search icon + input
        search_input_frame = ctk.CTkFrame(
            search_frame,
            fg_color=("#F3F4F6", "#2A2A2A"),
            border_color=("#E5E7EB", "#3A3A3A"),
            border_width=1,
            corner_radius=6,
        )
        search_input_frame.pack(side="left", fill="x", expand=True, padx=(0, 12))

        search_label = ctk.CTkLabel(
            search_input_frame,
            text="🔍",
            font=ctk.CTkFont(size=16),
        )
        search_label.pack(side="left", padx=12, pady=8)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        search_entry = ctk.CTkEntry(
            search_input_frame,
            textvariable=self.search_var,
            placeholder_text="Buscar recursos...",
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=13),
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)

        # Filter buttons section
        filter_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        filter_frame.pack(side="left", fill="x")

        # Status filter buttons
        self.status_buttons = {}
        for status, emoji, label in [
            ("all", "🔹", "Todos"),
            ("available", "🟢", "Disponible"),
            ("in_use", "🟡", "En Uso"),
            ("unavailable", "🔴", "No Disponible"),
        ]:
            btn = ctk.CTkButton(
                filter_frame,
                text=f"{emoji} {label}",
                font=ctk.CTkFont(size=11, weight="bold"),
                height=32,
                corner_radius=6,
                width=110,
                fg_color="#E5E7EB" if status == "all" else "#F3F4F6",
                text_color="#1F2937",
                hover_color="#D1D5DB",
                command=lambda s=status: self._on_filter_click(s),
            )
            btn.pack(side="left", padx=4)
            self.status_buttons[status] = btn

        # Highlight "all" button initially
        self.status_buttons["all"].configure(
            fg_color="#3B82F6",
            text_color="white",
            hover_color="#1D4ED8",
        )

    def _on_search_change(self, *args):
        """Handle search input change."""
        search_text = self.search_var.get()
        if self.on_search:
            self.on_search(search_text)

    def _on_filter_click(self, status: str):
        """Handle filter button click."""
        # Update button styles
        for btn_status, btn in self.status_buttons.items():
            if btn_status == status:
                btn.configure(
                    fg_color="#3B82F6",
                    text_color="white",
                    hover_color="#1D4ED8",
                )
            else:
                btn.configure(
                    fg_color="#F3F4F6",
                    text_color="#1F2937",
                    hover_color="#D1D5DB",
                )

        self.current_status_filter = status
        if self.on_filter_status:
            self.on_filter_status(status)

    def get_search_text(self) -> str:
        """Get current search text."""
        return self.search_var.get()

    def clear_search(self):
        """Clear search text."""
        self.search_var.set("")

    def set_filter_status(self, status: str):
        """Programmatically set filter status."""
        if status in self.status_buttons:
            self._on_filter_click(status)

    def focus_search(self):
        """Focus search input for keyboard shortcuts."""
        # Find the entry widget and focus it
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkEntry):
                        child.focus()
                        return
