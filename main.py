import sys
import os

# Añadir el directorio raíz al PYTHONPATH para que los imports funcionen
# Esto permite que 'from hotel_planner.ui.app import App' se resuelva correctamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel_planner.ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()