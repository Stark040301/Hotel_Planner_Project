"""
Form validation utilities for Hotel Event Manager UI.
Provides visual feedback for form field validation.
"""

import customtkinter as ctk
from typing import Optional, Callable, Any
from datetime import datetime

class ValidatedEntry(ctk.CTkEntry):
    """
    Enhanced CTkEntry with visual validation feedback.
    Shows green border for valid input, red for invalid.
    """
    
    def __init__(self, master, validator: Optional[Callable[[str], bool]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.validator = validator
        self._original_border_color = None
        self.is_valid = True
        
        # Bind to text changes for real-time validation
        if self.validator:
            self.bind("<KeyRelease>", self._on_text_change)
    
    def _on_text_change(self, event=None):
        """Check validation on each keystroke."""
        if self.validator:
            self.is_valid = self.validator(self.get())
            self._update_border()
    
    def _update_border(self):
        """Update border color based on validation state."""
        if self.is_valid:
            # Valid: green border
            self.configure(border_color="#10B981")
        else:
            # Invalid: red border
            self.configure(border_color="#EF4444")
    
    def validate(self) -> bool:
        """Manually validate the current input."""
        if self.validator:
            self.is_valid = self.validator(self.get())
            self._update_border()
            return self.is_valid
        return True
    
    def reset(self):
        """Reset to neutral state."""
        self.is_valid = True
        self.delete(0, "end")
        self.configure(border_color="#E2E8F0")


class FormValidator:
    """
    Centralized form validation with visual feedback.
    """
    
    @staticmethod
    def is_not_empty(value: str) -> bool:
        """Check if value is not empty."""
        return value.strip() != ""
    
    @staticmethod
    def is_positive_number(value: str) -> bool:
        """Check if value is a positive number."""
        try:
            return int(value) > 0
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_iso_datetime(value: str) -> bool:
        """Check if value is valid ISO format datetime (YYYY-MM-DDTHH:MM)."""
        if not value.strip():
            return True  # Allow empty (optional field)
        try:
            datetime.fromisoformat(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def is_valid_email(value: str) -> bool:
        """Check if value looks like an email."""
        if not value.strip():
            return True  # Allow empty (optional field)
        return "@" in value and "." in value
    
    @staticmethod
    def validate_form_field(field_name: str, value: str, field_type: str = "text") -> tuple[bool, str]:
        """
        Validate a form field and return (is_valid, error_message).
        
        Args:
            field_name: Display name of the field
            value: The value to validate
            field_type: Type of field ("text", "number", "datetime", "email")
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value.strip():
            return False, f"{field_name} no puede estar vacío"
        
        if field_type == "number":
            try:
                int_val = int(value)
                if int_val < 0:
                    return False, f"{field_name} debe ser un número positivo"
                return True, ""
            except ValueError:
                return False, f"{field_name} debe ser un número"
        
        elif field_type == "datetime":
            try:
                datetime.fromisoformat(value)
                return True, ""
            except (ValueError, AttributeError):
                return False, f"{field_name} debe estar en formato ISO (YYYY-MM-DDTHH:MM)"
        
        elif field_type == "email":
            if "@" in value and "." in value:
                return True, ""
            return False, f"{field_name} debe ser un correo válido"
        
        return True, ""


class ValidationFeedback(ctk.CTkFrame):
    """
    Visual feedback display for form validation.
    Shows error/success messages with appropriate colors.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.message_label = ctk.CTkLabel(
            self,
            text="",
            text_color="white",
            font=ctk.CTkFont(size=11, weight="bold"),
            wraplength=300,
            justify="left"
        )
        self.message_label.grid(row=0, column=0, sticky="w", padx=12, pady=8)
        
        self._current_type = None
    
    def show_error(self, message: str):
        """Display error message in red."""
        self.configure(fg_color="#FEE2E2")
        self.message_label.configure(text_color="#DC2626")
        self.message_label.configure(text=f"❌ {message}")
        self._current_type = "error"
    
    def show_success(self, message: str):
        """Display success message in green."""
        self.configure(fg_color="#D1FAE5")
        self.message_label.configure(text_color="#059669")
        self.message_label.configure(text=f"✓ {message}")
        self._current_type = "success"
    
    def show_warning(self, message: str):
        """Display warning message in amber."""
        self.configure(fg_color="#FEF3C7")
        self.message_label.configure(text_color="#D97706")
        self.message_label.configure(text=f"⚠ {message}")
        self._current_type = "warning"
    
    def show_info(self, message: str):
        """Display info message in blue."""
        self.configure(fg_color="#DBEAFE")
        self.message_label.configure(text_color="#1D4ED8")
        self.message_label.configure(text=f"ℹ {message}")
        self._current_type = "info"
    
    def clear(self):
        """Clear the feedback message."""
        self.message_label.configure(text="")
        self.configure(fg_color="transparent")
        self._current_type = None
