"""Modern event agenda card component."""

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import customtkinter as ctk


class EventAgendaCard(ctk.CTkFrame):
    """Card for a planned event with status, details, and actions."""

    def __init__(
        self,
        master,
        title: str,
        start: Any,
        end: Any,
        duration: str,
        resources_text: str,
        recurrence: str,
        notes: str,
        status_key: str,
        status_label: str,
        on_select: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_open: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_edit: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_delete: Optional[Callable[[Dict[str, Any]], None]] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.event_data = event_data or {}
        self.on_select = on_select
        self.on_open = on_open
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.status_key = status_key
        self._selected = False

        self.status_colors = {
            "upcoming": "#2563EB",
            "active": "#059669",
            "completed": "#6B7280",
        }
        self.status_bg = {
            "upcoming": ("#EFF6FF", "#1E293B"),
            "active": ("#ECFDF5", "#0F172A"),
            "completed": ("#F3F4F6", "#1F2937"),
        }

        self.configure(
            corner_radius=10,
            fg_color=("white", "#1E1E1E"),
            border_color=("#E5E7EB", "#2A2A2A"),
            border_width=1,
        )

        for widget in (self,):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._handle_select)

        self._build_ui(title, start, end, duration, resources_text, recurrence, notes, status_label)

    def _build_ui(self, title, start, end, duration, resources_text, recurrence, notes, status_label):
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=16, pady=14)

        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        title_lbl = ctk.CTkLabel(
            left,
            text=f"📅 {title}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1F2937", "#F3F4F6"),
        )
        title_lbl.pack(anchor="w")

        status_color = self.status_colors.get(self.status_key, "#6B7280")
        badge = ctk.CTkLabel(
            header,
            text=status_label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
            fg_color=status_color,
            corner_radius=5,
            padx=8,
            pady=2,
        )
        badge.pack(side="right")

        dates = ctk.CTkLabel(
            root,
            text=f"🕒 {self._fmt_dt(start)}  →  {self._fmt_dt(end)}",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#9CA3AF"),
        )
        dates.pack(anchor="w", pady=(0, 6))

        meta = ctk.CTkFrame(root, fg_color="transparent")
        meta.pack(fill="x", pady=(0, 8))

        meta_left = ctk.CTkLabel(
            meta,
            text=f"⏱️ {duration or '--'}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=status_color,
        )
        meta_left.pack(side="left")

        recur = recurrence or "none"
        meta_right = ctk.CTkLabel(
            meta,
            text=f"🔁 {recur}",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#9CA3AF"),
        )
        meta_right.pack(side="right")

        if resources_text:
            resources_lbl = ctk.CTkLabel(
                root,
                text=f"📦 {resources_text}",
                font=ctk.CTkFont(size=12),
                text_color=("#4B5563", "#D1D5DB"),
                justify="left",
                wraplength=300,
            )
            resources_lbl.pack(anchor="w", pady=(0, 8))

        if notes:
            notes_text = notes if len(notes) <= 110 else notes[:107] + "..."
            notes_lbl = ctk.CTkLabel(
                root,
                text=f"📝 {notes_text}",
                font=ctk.CTkFont(size=11),
                text_color=("#6B7280", "#9CA3AF"),
                justify="left",
                wraplength=300,
            )
            notes_lbl.pack(anchor="w", pady=(0, 8))

        actions = ctk.CTkFrame(root, fg_color="transparent")
        actions.pack(fill="x", pady=(6, 0))

        open_btn = ctk.CTkButton(
            actions,
            text="👁️ Ver",
            height=32,
            width=86,
            corner_radius=6,
            fg_color="#3B82F6",
            hover_color="#1D4ED8",
            command=self._handle_open,
        )
        open_btn.pack(side="left", padx=(0, 8))

        edit_btn = ctk.CTkButton(
            actions,
            text="✏️ Editar",
            height=32,
            width=94,
            corner_radius=6,
            fg_color="#059669",
            hover_color="#047857",
            command=self._handle_edit,
        )
        edit_btn.pack(side="left", padx=(0, 8))

        delete_btn = ctk.CTkButton(
            actions,
            text="🗑️ Borrar",
            height=32,
            width=94,
            corner_radius=6,
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self._handle_delete,
        )
        delete_btn.pack(side="left")

        for child in root.winfo_children():
            try:
                child.bind("<Button-1>", self._handle_select)
            except Exception:
                pass

    def _fmt_dt(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%y %H:%M")
        return str(value)

    def _handle_select(self, event=None):
        if self.on_select:
            self.on_select(self.event_data)
        return "break"

    def _handle_open(self):
        if self.on_open:
            self.on_open(self.event_data)

    def _handle_edit(self):
        if self.on_edit:
            self.on_edit(self.event_data)

    def _handle_delete(self):
        if self.on_delete:
            self.on_delete(self.event_data)

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.configure(border_color="#2563EB", border_width=2)
        else:
            self.configure(border_color=("#E5E7EB", "#2A2A2A"), border_width=1)

    def _on_enter(self, event=None):
        if not self._selected:
            self.configure(fg_color=("#F9FAFB", "#262626"))

    def _on_leave(self, event=None):
        if not self._selected:
            self.configure(fg_color=("white", "#1E1E1E"))
