"""Modern inventory card component for displaying resources in card format."""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, Dict, Any


class InventoryCard(ctk.CTkFrame):
    """
    Modern card component for displaying a single inventory resource.
    
    Features:
    - Clean, professional appearance with status indicator
    - Hover effects (shadow, background color change)
    - Status colors (Available/In Use/Unavailable)
    - Quick action buttons (Edit, Delete)
    - Smooth animations on interaction
    """

    def __init__(
        self,
        master,
        title: str,
        resource_type: str,
        details: Dict[str, Any],
        status: str = "available",
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self.title = title
        self.resource_type = resource_type
        self.details = details
        self.status = status
        self.on_edit = on_edit
        self.on_delete = on_delete

        # Status colors
        self.status_colors = {
            "available": "#059669",    # Green
            "in_use": "#D97706",       # Amber
            "unavailable": "#DC2626",  # Red
        }

        # Type icons
        self.type_icons = {
            "Room": "🏠",
            "Employee": "👤",
            "Item": "📦",
        }

        # Configure card appearance
        self.configure(
            corner_radius=8,
            fg_color=("white", "#1E1E1E"),
            border_color=("#E5E7EB", "#2A2A2A"),
            border_width=1,
        )

        # Bind hover events for smooth effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        self._is_hovered = False
        self._build_ui()

    def _build_ui(self):
        """Build the card UI structure."""
        
        # Main content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        # Header: Icon + Title + Status Badge
        header = ctk.CTkFrame(content, fg_color="transparent", height=40)
        header.pack(fill="x", pady=(0, 12))
        header.pack_propagate(False)

        # Type icon + title
        left_side = ctk.CTkFrame(header, fg_color="transparent")
        left_side.pack(side="left", fill="x", expand=True)

        icon = self.type_icons.get(self.resource_type, "📦")
        title_text = f"{icon} {self.title}"
        
        title_label = ctk.CTkLabel(
            left_side,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1F2937", "#F3F4F6"),
        )
        title_label.pack(side="left", anchor="w")

        # Status badge (right side)
        status_badge = self._create_status_badge(header)
        status_badge.pack(side="right", padx=(8, 0))

        # Details section
        details_frame = ctk.CTkFrame(content, fg_color="transparent")
        details_frame.pack(fill="x", pady=(0, 12))

        # Show key details (quantity, capacity, role, etc.)
        details_text = self._format_details()
        if details_text:
            details_label = ctk.CTkLabel(
                details_frame,
                text=details_text,
                font=ctk.CTkFont(size=12),
                text_color=("#6B7280", "#9CA3AF"),
                justify="left",
            )
            details_label.pack(fill="x", anchor="w")

        # Action buttons
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", pady=(8, 0))

        edit_btn = ctk.CTkButton(
            button_frame,
            text="✏️  Editar",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=6,
            fg_color="#3B82F6",
            hover_color="#1D4ED8",
            command=self._on_edit_click,
        )
        edit_btn.pack(side="left", padx=(0, 8))

        delete_btn = ctk.CTkButton(
            button_frame,
            text="🗑️  Borrar",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=6,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self._on_delete_click,
        )
        delete_btn.pack(side="left")

    def _create_status_badge(self, parent) -> ctk.CTkLabel:
        """Create a status badge label."""
        status_color = self.status_colors.get(self.status, "#6B7280")
        status_text_map = {
            "available": "Disponible",
            "in_use": "En Uso",
            "unavailable": "No Disponible",
        }
        status_text = status_text_map.get(self.status, "Desconocido")

        badge = ctk.CTkLabel(
            parent,
            text=status_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
            fg_color=status_color,
            corner_radius=4,
            padx=8,
            pady=2,
        )
        return badge

    def _format_details(self) -> str:
        """Format details for display in card."""
        lines = []
        
        # Show up to 3 key details
        for key, value in list(self.details.items())[:3]:
            if value and key not in ["id", "resource_id"]:
                # Format key name (convert snake_case to Title Case)
                label = key.replace("_", " ").title()
                lines.append(f"• {label}: {value}")

        return "\n".join(lines)

    def _on_enter(self, event=None):
        """Handle mouse enter event - show hover effect."""
        if not self._is_hovered:
            self._is_hovered = True
            # Subtle background color change on hover
            self.configure(
                fg_color=("#F9FAFB", "#262626"),
                border_color=("#3B82F6", "#3B82F6"),
                border_width=2,
            )

    def _on_leave(self, event=None):
        """Handle mouse leave event - remove hover effect."""
        self._is_hovered = False
        self.configure(
            fg_color=("white", "#1E1E1E"),
            border_color=("#E5E7EB", "#2A2A2A"),
            border_width=1,
        )

    def _on_edit_click(self):
        """Handle edit button click."""
        if self.on_edit:
            self.on_edit(self.title)

    def _on_delete_click(self):
        """Handle delete button click."""
        if self.on_delete:
            self.on_delete(self.title)

    def set_status(self, status: str):
        """Update card status (available/in_use/unavailable)."""
        if status in self.status_colors:
            self.status = status
            # Refresh to show new status badge
            self._build_ui()
