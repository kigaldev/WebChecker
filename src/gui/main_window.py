"""
Main Window Module
----------------
Implementa la interfaz gráfica principal de Website Checker.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Callable, Optional
from datetime import datetime
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv

class MainWindow(ttk.Frame):
    """Ventana principal de la aplicación Website Checker."""
    
    def __init__(self, master: tk.Tk, checker: object, validator: object):
        """
        Inicializa la ventana principal.
        
        Args:
            master: Ventana raíz de Tkinter
            checker: Instancia del verificador de sitios web
            validator: Instancia del validador de URLs
        """
        super().__init__(master)
        self.master = master
        self.checker = checker
        self.validator = validator
        
        # Variables de control
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Estado: Esperando URL...")
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.refresh_interval_var = tk.StringVar(value="5")
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.show_details_var = tk.BooleanVar(value=True)
        
        # Configurar estilo
        self.style = ttk.Style()
        self._setup_styles()
        
        # Inicializar UI
        self._init_ui()
        self._create_menu()
        
        # Eventos
        self._setup_bindings()
        
        # Historial de URLs
        self.url_history = set()
        self.load_url_history()
        
        # Variable para el job de auto-refresh
        self._refresh_job = None
        
    def _setup_styles(self):
        """Configura los estilos de la aplicación."""
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 10))
        self.style.configure('URL.TCombobox', font=('Helvetica', 10))
        
    def _init_ui(self):
        """Inicializa todos los elementos de la interfaz."""
        # Configurar el grid principal
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        
        # URL Entry y botones
        self._create_url_frame(main_frame)
        
        # Panel de estado y detalles
        self._create_status_frame(main_frame)
        
        # Historial
        self._create_history_frame(main_frame)
        
        # Panel de configuración
        self._create_settings_frame(main_frame)
        
        # Panel de gráficos
        self._create_charts_frame(main_frame)
    
    def _create_url_frame(self, parent):
        """Crea el frame para la entrada de URL."""
        url_frame = ttk.LabelFrame(parent, text="URL", padding="5")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        url_frame.columnconfigure(0, weight=1)
        
        # Combobox para URLs con autocompletado
        self.url_combo = ttk.Combobox(
            url_frame,
            textvariable=self.url_var,
            style='URL.TCombobox'
        )
        self.url_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Botones
        buttons_frame = ttk.Frame(url_frame)
        buttons_frame.grid(row=0, column=1, sticky=(tk.E))
        
        ttk.Button(
            buttons_frame,
            text="Verificar",
            command=self._check_website
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            buttons_frame,
            text="Limpiar",
            command=self._clear_url
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_status_frame(self, parent):
        """Crea el frame para mostrar el estado y detalles."""
        status_frame = ttk.LabelFrame(parent, text="Resultado", padding="5")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(0, weight=1)
        
        # Estado básico
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style='Status.TLabel',
            wraplength=350
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Frame para detalles
        self.details_frame = ttk.Frame(status_frame)
        self.details_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Variables para detalles
        self.details_vars = {
            'response_time': tk.StringVar(),
            'content_type': tk.StringVar(),
            'server': tk.StringVar(),
            'ssl_status': tk.StringVar()
        }
        
        # Etiquetas de detalles
        for i, (key, var) in enumerate(self.details_vars.items()):
            ttk.Label(
                self.details_frame,
                text=f"{key.replace('_', ' ').title()}:",
                style='Header.TLabel'
            ).grid(row=i, column=0, sticky=tk.W, padx=5)
            
            ttk.Label(
                self.details_frame,
                textvariable=var,
                style='Status.TLabel'
            ).grid(row=i, column=1, sticky=tk.W, padx=5)
    
    def _create_history_frame(self, parent):
        """Crea el frame para el historial."""
        history_frame = ttk.LabelFrame(parent, text="Historial", padding="5")
        history_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Crear Treeview
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("url", "status", "response_time", "timestamp"),
            show="headings",
            selectmode="browse"
        )
        
        # Configurar columnas
        self.history_tree.heading("url", text="URL")
        self.history_tree.heading("status", text="Estado")
        self.history_tree.heading("response_time", text="Tiempo de Respuesta")
        self.history_tree.heading("timestamp", text="Fecha/Hora")
        
        self.history_tree.column("url", width=200)
        self.history_tree.column("status", width=100)
        self.history_tree.column("response_time", width=100)
        self.history_tree.column("timestamp", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            history_frame,
            orient=tk.VERTICAL,
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Colocar elementos
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Menú contextual
        self._create_context_menu()
    
    def _create_settings_frame(self, parent):
        """Crea el frame de configuración."""
        settings_frame = ttk.LabelFrame(parent, text="Configuración", padding="5")
        settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Auto-refresh
        refresh_frame = ttk.Frame(settings_frame)
        refresh_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(
            refresh_frame,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            refresh_frame,
            text="Intervalo (min):"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Entry(
            refresh_frame,
            textvariable=self.refresh_interval_var,
            width=5
        ).pack(side=tk.LEFT, padx=5)
        
        # Opciones adicionales
        options_frame = ttk.Frame(settings_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Checkbutton(
            options_frame,
            text="Modo oscuro",
            variable=self.dark_mode_var,
            command=self._toggle_theme
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(
            options_frame,
            text="Mostrar detalles",
            variable=self.show_details_var,
            command=self._toggle_details
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_charts_frame(self, parent):
        """Crea el frame para gráficos."""
        charts_frame = ttk.LabelFrame(parent, text="Gráficos", padding="5")
        charts_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Botones para diferentes tipos de gráficos
        ttk.Button(
            charts_frame,
            text="Tiempos de Respuesta",
            command=lambda: self._show_chart('response_time')
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            charts_frame,
            text="Estados",
            command=lambda: self._show_chart('status')
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            charts_frame,
            text="Disponibilidad",
            command=lambda: self._show_chart('availability')
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_menu(self):
        """Crea la barra de menú."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Exportar CSV", command=self._export_csv)
        file_menu.add_command(label="Exportar JSON", command=self._export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Limpiar Historial", command=self._clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.master.quit)
        
        # Menú Ver
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ver", menu=view_menu)
        view_menu.add_checkbutton(
            label="Modo Oscuro",
            variable=self.dark_mode_var,
            command=self._toggle_theme
        )
        view_menu.add_checkbutton(
            label="Mostrar Detalles",
            variable=self.show_details_var,
            command=self._toggle_details
        )
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Configuración", command=self._show_settings)
        tools_menu.add_command(label="Estadísticas", command=self._show_statistics)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Documentación", command=self._show_docs)
        help_menu.add_command(label="Acerca de", command=self._show_about)
    
    def _create_context_menu(self):
        """Crea el menú contextual para el historial."""
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(
            label="Copiar URL",
            command=self._copy_selected_url
        )
        self.context_menu.add_command(
            label="Volver a verificar",
            command=self._recheck_selected
        )
        self.context_menu.add_command(
            label="Eliminar entrada",
            command=self._delete_selected
        )
        
        self.history_tree.bind(
            "<Button-3>",
            lambda e: self._show_context_menu(e)
        )
    
    def _check_website(self):
        """Verifica el estado del sitio web ingresado."""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning(
                "URL vacía",
                "Por favor, ingrese una URL para verificar."
            )
            return
        
        if not self.validator.is_valid_url(url):
            messagebox.showerror(
                "URL inválida",
                "Por favor, ingrese una URL válida (ejemplo: https://www.ejemplo.com)"
            )
            return
        
        try:
            self.status_var.set("Estado: Verificando...")
            self.master.update_idletasks()
            
            result = self.checker.check_website(url)
            
            # Actualizar estado
            if result.status_code == 200:
                self.status_var.set(f"Estado: Sitio web disponible (código {result.status_code})")
                status = "Disponible"
            else:
                self.status_var.set(
                    f"Estado: Sitio web no disponible (código {result.status_code})"
                )
                status = "No disponible"
            
            # Actualizar detalles
            self._update_details(result)
            
            # Agregar al historial
            self._add_to_history(url, status, result)
            
            # Actualizar URL history
            self