#!/usr/bin/env python3
"""
Web Checker - Aplicación para verificar el estado de sitios web
"""

import sys
import tkinter as tk
from src.gui.main_window import MainWindow
from src.core.checker import WebsiteChecker
from src.utils.validators import URLValidator

def main():
    try:
        # Inicializar el checker y el validador
        checker = WebsiteChecker()
        validator = URLValidator()
        
        # Crear la ventana principal
        root = tk.Tk()
        root.title("Website Checker")
        
        # Configurar el tamaño mínimo de la ventana
        root.minsize(400, 300)
        
        # Centrar la ventana en la pantalla
        window_width = 500
        window_height = 400
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Inicializar la ventana principal con las dependencias
        app = MainWindow(
            master=root,
            checker=checker,
            validator=validator
        )
        
        # Iniciar el loop principal de la aplicación
        root.mainloop()
        
    except Exception as e:
        print(f"Error al iniciar la aplicación: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()