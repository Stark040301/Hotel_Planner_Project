import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from PIL import Image, ImageTk  # pillow debe estar instalado

class App(ctk.CTk):
    """
    Ventana principal minimal: sidebar con botones (placeholders),
    área principal con imagen de fondo y título, y status bar.
    """

    def __init__(self, controller=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller  # opcional, será usado más adelante
        self.title("Hotel Management Simulator — Menu principal")
        self.geometry("1000x640")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        # Guardar referencia a la imagen para evitar que sea recolectada
        self._bg_photo = None

        self._build_layout()

    def _build_layout(self):
        # Contenedor principal
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Main area
        main_area = ctk.CTkFrame(container)
        main_area.pack(side="left", fill="both", expand=True)

        # Intentar cargar imagen de fondo desde assets y dibujar texto en un Canvas (sin fondo detrás del texto)
        assets_dir = Path(__file__).resolve().parent / "assets"
        bg_path = assets_dir / "bg.jpeg"  # coloca tu imagen aquí
        if bg_path.exists():
            try:
                img = Image.open(bg_path)
                # keep original PIL image and create a Canvas that will resize with the window
                self._bg_image = img
                # store original image size
                self._bg_image_size = self._bg_image.size  # (orig_w, orig_h)
                # track last requested size to avoid thrash
                self._last_request_size = None
                canvas = tk.Canvas(main_area, highlightthickness=0)
                canvas.pack(fill="both", expand=True)

                # initial image (will be updated on first <Configure>)
                w_init, h_init = 800, 560
                resized = self._bg_image.resize((w_init, h_init), Image.LANCZOS)
                self._bg_photo = ImageTk.PhotoImage(resized)
                # create image centered so repositioning is stable
                self._bg_img_id = canvas.create_image(w_init//2, h_init//2, image=self._bg_photo, anchor="center")

                # create text items and keep their ids so we can reposition later
                # create tk Font objects so we can change size dynamically
                title_size = 36
                subtitle_size = 18
                self._title_font = tkfont.Font(family="Quicksand", size=title_size, weight="bold")
                self._subtitle_font = tkfont.Font(family="Quicksand", size=subtitle_size, slant="italic")
                # left-aligned text: use a left margin and anchor="w"
                left_margin = max(24, int(w_init * 0.06))
                self._title_id = canvas.create_text(left_margin, int(h_init * 0.06),
                                                    text="Hotel Management Simulator",
                                                    fill="#e9d8a6", font=self._title_font, anchor="w")
                self._subtitle_id = canvas.create_text(left_margin, int(h_init * 0.12),
                                                       text="Gestión de eventos y recursos",
                                                       fill="#005f73", font=self._subtitle_font, anchor="w")

                # store canvas reference and bind debounced resize handler
                self._canvas = canvas

                # --- draw-buttons-on-canvas helper (rounded corners) ---
                btn_font = tkfont.Font(family="Quicksand", size=12, weight="bold")

                def _create_canvas_button(c, x, y, w, h, text, callback,
                                          fill="#005f73", hover="#0a9396", text_color="white", radius=8):
                    """Draw a rounded-rect button composed of shapes + text. Returns dict with part ids."""
                    left, top = x, y
                    right, bottom = x + w, y + h
                    r = radius
                    parts = []
                    # central rectangles (body)
                    parts.append(c.create_rectangle(left + r, top, right - r, bottom, fill=fill, outline=""))
                    parts.append(c.create_rectangle(left, top + r, right, bottom - r, fill=fill, outline=""))
                    # corner circles
                    parts.append(c.create_oval(left, top, left + 2 * r, top + 2 * r, fill=fill, outline=""))
                    parts.append(c.create_oval(right - 2 * r, top, right, top + 2 * r, fill=fill, outline=""))
                    parts.append(c.create_oval(left, bottom - 2 * r, left + 2 * r, bottom, fill=fill, outline=""))
                    parts.append(c.create_oval(right - 2 * r, bottom - 2 * r, right, bottom, fill=fill, outline=""))
                    # text
                    txt_id = c.create_text(left + w / 2, top + h / 2, text=text, fill=text_color, font=btn_font)
                    parts.append(txt_id)

                    group = {"parts": parts, "fill": fill, "hover": hover, "text_id": txt_id}

                    def _on_enter(e):
                        for pid in parts[:-1]:
                            c.itemconfig(pid, fill=hover)

                    def _on_leave(e):
                        for pid in parts[:-1]:
                            c.itemconfig(pid, fill=fill)

                    def _on_click(e):
                        try:
                            callback()
                        except Exception:
                            pass

                    # bind events to all parts of the button
                    for pid in parts:
                        c.tag_bind(pid, "<Enter>", _on_enter)
                        c.tag_bind(pid, "<Leave>", _on_leave)
                        c.tag_bind(pid, "<Button-1>", _on_click)

                    return group

                # create canvas-drawn buttons (positions updated later in _do_resize)
                self._canvas_buttons = {}
                left_margin = max(24, int(w_init * 0.06))
                y_start = int(h_init * 0.25)
                btn_w = 220
                btn_h = 44
                spacing = max(40, int(h_init * 0.10))
                self._canvas_buttons["create"] = _create_canvas_button(canvas, left_margin, y_start + 0 * spacing, btn_w, btn_h,
                                                                       "Crear nuevo evento", self.on_create)
                self._canvas_buttons["edit_events"] = _create_canvas_button(canvas, left_margin, y_start + 1 * spacing, btn_w, btn_h,
                                                                            "Editar eventos", self.on_edit_events)
                self._canvas_buttons["view_resources"] = _create_canvas_button(canvas, left_margin, y_start + 2 * spacing, btn_w, btn_h,
                                                                                "Ver Recursos", self.on_view_resources)
                self._canvas_buttons["edit_resources"] = _create_canvas_button(canvas, left_margin, y_start + 3 * spacing, btn_w, btn_h,
                                                                                "Editar recursos", self.on_edit_resources)

                 # debounce: schedule actual work after a short delay to avoid thrash
                self._resize_after_id = None
                canvas.bind("<Configure>", self._on_canvas_configure)
            except Exception:
                pass
        else:
            # si no hay imagen, puedes crear el canvas vacío o usar CTkLabel normal
            pass

        # Barra de estado en la parte inferior
        self.status_lbl = ctk.CTkLabel(self, text="Listo", anchor="w")
        self.status_lbl.pack(fill="x", side="bottom", padx=8, pady=(0,8))

    # ---------- placeholders de acción (ahora solo actualizan status) ----------
    def on_create(self):
        # abrir diálogo modal para crear evento; _on_event_created se ejecuta si se crea
        try:
            CreateEventDialog(self, self.controller, on_created=self._on_event_created)
        except Exception as exc:
            self.status_lbl.configure(text=f"Error al abrir formulario: {exc}")

    def _on_event_created(self, event_dict):
        self.status_lbl.configure(text="Abrir pantalla: Crear eventos")

    def on_edit_events(self):
        # aquí abrirás la pantalla de edición de eventos
        self.status_lbl.configure(text="Abrir pantalla: Editar eventos")

    def on_view_resources(self):
        # aquí mostrarás la lista de recursos
        self.status_lbl.configure(text="Abrir pantalla: Ver recursos")

    def on_edit_resources(self):
        # aquí abrirás la edición de recursos
        self.status_lbl.configure(text="Abrir pantalla: Editar recursos")

    def _on_canvas_configure(self, event):
        """Debounced wrapper for resize: schedule a single update after 150ms.
           Ignore tiny changes (threshold) to avoid unnecessary resizes."""
        try:
            w, h = max(1, event.width), max(1, event.height)
            # ignore tiny fluctuations (<8 px)
            last = getattr(self, "_last_request_size", None)
            if last:
                lw, lh = last
                if abs(w - lw) < 8 and abs(h - lh) < 8:
                    return
            self._last_request_size = (w, h)

            if getattr(self, "_resize_after_id", None):
                try:
                    self.after_cancel(self._resize_after_id)
                except Exception:
                    pass
            # increase debounce to 150ms to reduce thrash
            self._resize_after_id = self.after(150, lambda: self._do_resize(w, h))
        except Exception:
            pass

    def _do_resize(self, w, h):
        """Perform image/font resize and reposition. Runs on the main thread (after).
           Resize preserving aspect ratio (cover) to avoid jitter."""
        try:
            orig_w, orig_h = getattr(self, "_bg_image_size", self._bg_image.size)
            # compute scale to cover the canvas (no empty bars)
            scale = max(w / orig_w, h / orig_h)
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))

            # if the requested size is the same as last applied, skip
            last_applied = getattr(self, "_last_applied_size", None)
            if last_applied and abs(last_applied[0] - new_w) < 4 and abs(last_applied[1] - new_h) < 4:
                # still reposition text though (use left margin, no centrado)
                try:
                    left_margin = max(24, int(w * 0.06))
                    self._canvas.coords(self._title_id, left_margin, int(h * 0.05))
                    self._canvas.coords(self._subtitle_id, left_margin, int(h * 0.12))
                except Exception:
                    pass
                return

            resized = self._bg_image.resize((new_w, new_h), Image.LANCZOS)
            self._bg_photo = ImageTk.PhotoImage(resized)
            self._canvas.itemconfig(self._bg_img_id, image=self._bg_photo)
            # center the image (canvas coords are center)
            self._canvas.coords(self._bg_img_id, w // 2, h // 2)

            # reposition texts (centered horizontally, relative vertical positions)
            # position texts using a left margin and keep them left-aligned
            left_margin = max(24, int(w * 0.06))
            self._canvas.coords(self._title_id, left_margin, int(h * 0.05))
            self._canvas.coords(self._subtitle_id, left_margin, int(h * 0.12))

            # adjust font sizes proportionally
            base = min(w, h)
            new_title_size = max(12, int(base * 0.06))
            new_subtitle_size = max(9, int(base * 0.03))
            try:
                self._title_font.configure(size=new_title_size)
                self._subtitle_font.configure(size=new_subtitle_size)
            except Exception:
                pass

            # remember applied size
            self._last_applied_size = (new_w, new_h)
        except Exception:
            pass

        # reposition buttons on the left of the canvas
        try:
            # update positions and sizes of canvas-drawn rounded buttons
            y_start = int(h * 0.25)
            spacing = max(40, int(h * 0.08))
            btn_w = 220
            btn_h = 44
            left_margin = max(24, int(w * 0.06))
            idx = 0
            for key in ("create", "edit_events", "view_resources", "edit_resources"):
                group = self._canvas_buttons.get(key)
                if not group:
                    idx += 1
                    continue
                parts = group["parts"]
                r = 8
                left = left_margin
                top = y_start + idx * spacing
                right = left + btn_w
                bottom = top + btn_h
                try:
                    # rect middle 1
                    self._canvas.coords(parts[0], left + r, top, right - r, bottom)
                    # rect middle 2
                    self._canvas.coords(parts[1], left, top + r, right, bottom - r)
                    # ovals (TL, TR, BL, BR)
                    self._canvas.coords(parts[2], left, top, left + 2 * r, top + 2 * r)
                    self._canvas.coords(parts[3], right - 2 * r, top, right, top + 2 * r)
                    self._canvas.coords(parts[4], left, bottom - 2 * r, left + 2 * r, bottom)
                    self._canvas.coords(parts[5], right - 2 * r, bottom - 2 * r, right, bottom)
                    # text
                    self._canvas.coords(parts[6], left + btn_w / 2, top + btn_h / 2)
                except Exception:
                    pass
                idx += 1
        except Exception:
            pass


if __name__ == "__main__":
    # solo para probar la plantilla rápidamente
    app = App()
    app.mainloop()