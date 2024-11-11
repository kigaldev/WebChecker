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
    
    def _setup_bindings(self):
        """Configura los bindings de eventos."""
        self.master.bind('<Return>', lambda e: self._check_website())
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_closing(self):
        """Maneja el evento de cierre de la ventana."""
        if self._refresh_job:
            self.master.after_cancel(self._refresh_job)
        self.master.destroy()
    
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
            self.url_history.add(url)
            self._update_url_combo()
            self._save_url_history()
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al verificar el sitio: {str(e)}"
            )
            self.status_var.set("Estado: Error al verificar el sitio")
    
    def _clear_url(self):
        """Limpia el campo de URL."""
        self.url_var.set("")
        
    def _add_to_history(self, url: str, status: str, result):
        """Agrega una entrada al historial."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response_time = f"{result.response_time:.2f}ms" if result.response_time > 0 else "N/A"
        
        self.history_tree.insert(
            "",
            0,
            values=(url, status, response_time, timestamp)
        )
    
    def _update_details(self, result):
        """Actualiza el panel de detalles con los resultados."""
        self.details_vars['response_time'].set(f"{result.response_time:.2f}ms")
        self.details_vars['content_type'].set(result.content_type or "N/A")
        self.details_vars['server'].set(result.server or "N/A")
        
        ssl_status = "Seguro (HTTPS)" if result.ssl_info else "No seguro (HTTP)"
        self.details_vars['ssl_status'].set(ssl_status)
    
    def _toggle_auto_refresh(self):
        """Activa/desactiva el auto-refresh."""
        if self.auto_refresh_var.get():
            try:
                interval = int(self.refresh_interval_var.get())
                if interval < 1:
                    raise ValueError("El intervalo debe ser mayor a 0")
                self._schedule_refresh()
            except ValueError as e:
                messagebox.showerror(
                    "Error",
                    f"Intervalo inválido: {str(e)}"
                )
                self.auto_refresh_var.set(False)
        else:
            if hasattr(self, '_refresh_job'):
                self.master.after_cancel(self._refresh_job)
    
    def _schedule_refresh(self):
        """Programa la próxima actualización."""
        if self.auto_refresh_var.get():
            interval = int(self.refresh_interval_var.get()) * 60 * 1000  # convertir a ms
            self._check_website()
            self._refresh_job = self.master.after(interval, self._schedule_refresh)
    
    def _toggle_theme(self):
        """Cambia entre tema claro y oscuro."""
        if self.dark_mode_var.get():
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self):
        """Aplica el tema oscuro."""
        self.style.configure('.', background='#2b2b2b', foreground='white')
        self.style.configure('TLabel', background='#2b2b2b', foreground='white')
        self.style.configure('TFrame', background='#2b2b2b')
        self.style.configure('TLabelframe', background='#2b2b2b')
        self.style.configure('TLabelframe.Label', background='#2b2b2b', foreground='white')
        self.style.configure('Treeview', background='#3b3b3b', foreground='white', fieldbackground='#3b3b3b')
        self.master.configure(bg='#2b2b2b')
    
    def _apply_light_theme(self):
        """Aplica el tema claro."""
        self.style.configure('.', background='system', foreground='system')
        self.style.configure('TLabel', background='system', foreground='system')
        self.style.configure('TFrame', background='system')
        self.style.configure('TLabelframe', background='system')
        self.style.configure('TLabelframe.Label', background='system', foreground='system')
        self.style.configure('Treeview', background='system', foreground='system', fieldbackground='system')
        self.master.configure(bg='system')
    
    def _toggle_details(self):
        """Muestra/oculta el panel de detalles."""
        if self.show_details_var.get():
            self.details_frame.grid()
        else:
            self.details_frame.grid_remove()
    
    def _show_context_menu(self, event):
        """Muestra el menú contextual."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _copy_selected_url(self):
        """Copia la URL seleccionada al portapapeles."""
        selected = self.history_tree.selection()
        if not selected:
            return
            
        url = self.history_tree.item(selected[0])['values'][0]
        self.master.clipboard_clear()
        self.master.clipboard_append(url)
    
    def _recheck_selected(self):
        """Vuelve a verificar la URL seleccionada."""
        selected = self.history_tree.selection()
        if not selected:
            return
            
        url = self.history_tree.item(selected[0])['values'][0]
        self.url_var.set(url)
        self._check_website()
    
    def _delete_selected(self):
        """Elimina la entrada seleccionada del historial."""
        selected = self.history_tree.selection()
        if not selected:
            return
            
        self.history_tree.delete(selected[0])
    
    def _show_chart(self, chart_type: str):
        """Muestra un gráfico específico."""
        chart_window = tk.Toplevel(self.master)
        chart_window.title(f"Gráfico - {chart_type.replace('_', ' ').title()}")
        chart_window.geometry("800x600")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == 'response_time':
            self._plot_response_times(ax)
        elif chart_type == 'status':
            self._plot_status_distribution(ax)
        elif chart_type == 'availability':
            self._plot_availability(ax)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _plot_response_times(self, ax):
        """Dibuja el gráfico de tiempos de respuesta."""
        times = []
        labels = []
        
        for item in self.history_tree.get_children():
            values = self.history_tree.item(item)['values']
            try:
                response_time = float(values[2].replace('ms', ''))
                times.append(response_time)
                labels.append(values[3])  # timestamp
            except (ValueError, AttributeError):
                continue
        
        if times:
            ax.plot(labels, times, marker='o')
            ax.set_xlabel('Fecha/Hora')
            ax.set_ylabel('Tiempo de Respuesta (ms)')
            ax.set_title('Tiempos de Respuesta')
            plt.xticks(rotation=45)
            plt.tight_layout()
    
    def _plot_status_distribution(self, ax):
        """Dibuja el gráfico de distribución de estados."""
        status_count = {}
        
        for item in self.history_tree.get_children():
            status = self.history_tree.item(item)['values'][1]
            status_count[status] = status_count.get(status, 0) + 1
        
        if status_count:
            statuses = list(status_count.keys())
            counts = list(status_count.values())
            
            ax.bar(statuses, counts)
            ax.set_xlabel('Estado')
            ax.set_ylabel('Cantidad')
            ax.set_title('Distribución de Estados')
            plt.tight_layout()
    
    def _plot_availability(self, ax):
        """Dibuja el gráfico de disponibilidad."""
        available = 0
        total = 0
        
        for item in self.history_tree.get_children():
            status = self.history_tree.item(item)['values'][1]
            total += 1
            if status == "Disponible":
                available += 1
        
        if total:
            availability = (available / total) * 100
            unavailability = 100 - availability
            
            ax.pie(
                [availability, unavailability],
                labels=['Disponible', 'No Disponible'],
                autopct='%1.1f%%',
                colors=['#2ecc71', '#e74c3c']
            )
            ax.set_title('Disponibilidad General')
            plt.tight_layout()
    
    def _export_csv(self):
        """Exporta el historial a CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            initialfile=f'website_checker_history_{datetime.now():%Y%m%d_%H%M}.csv'
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['URL', 'Estado', 'Tiempo de Respuesta', 'Fecha/Hora'])
                    
                    for item in self.history_tree.get_children():
                        writer.writerow(self.history_tree.item(item)['values'])
                        
                messagebox.showinfo(
                    "Éxito",
                    f"Historial exportado exitosamente a {filename}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al exportar el historial: {str(e)}"
                )
    
    def _export_json(self):
        """Exporta el historial a JSON."""
        filename = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            initialfile=f'website_checker_history_{datetime.now():%Y%m%d_%H%M}.json'
        )
        
        if filename:
            try:
                data = []
                for item in self.history_tree.get_children():
                    values = self.history_tree.item(item)['values']
                    data.append({
                        'url': values[0],
                        'status': values[1],
                        'response_time': values[2],
                        'timestamp': values[3]
                    })
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                messagebox.showinfo(
                    "Éxito",
                    f"Historial exportado exitosamente a {filename}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al exportar el historial: {str(e)}"
                )
    
    def _clear_history(self):
        """Limpia el historial de verificaciones."""
        if messagebox.askyesno(
            "Confirmar",
            "¿Estás seguro de que deseas limpiar todo el historial?"
        ):
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
                
    def _show_settings(self):
        """Muestra la ventana de configuración."""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Configuración")
        settings_window.geometry("400x300")
        settings_window.transient(self.master)
        settings_window.grab_set()
        
        # Aquí puedes agregar más opciones de configuración
        ttk.Label(
            settings_window,
            text="Configuración adicional próximamente..."
        ).pack(padx=20, pady=20)
    
    def _show_statistics(self):
        """Muestra la ventana de estadísticas."""
        stats_window = tk.Toplevel(self.master)
        stats_window.title("Estadísticas")
        stats_window.geometry("600x400")
        stats_window.transient(self.master)
        stats_window.grab_set()
        
        # Aquí puedes agregar las estadísticas detalladas
        ttk.Label(
            stats_window,
            text="Estadísticas detalladas próximamente..."
        ).pack(padx=20, pady=20)
    
    def _show_docs(self):
        """Abre la documentación en el navegador."""
        webbrowser.open("https://github.com/kigaldev/WebChecker/blob/main/README.md")
    
    def _show_about(self):
        """Muestra el diálogo 'Acerca de'."""
        about_text = """
        Website Checker v1.0.0
        
        Una aplicación para verificar el estado
        de sitios web y su disponibilidad.
        
        Desarrollado con Python y Tkinter.
        """
        messagebox.showinfo("Acerca de Website Checker", about_text)
    
    def load_url_history(self):
        """Carga el historial de URLs desde un archivo."""
        try:
            with open('url_history.json', 'r') as f:
                self.url_history = set(json.load(f))
            self._update_url_combo()
        except FileNotFoundError:
            self.url_history = set()
        except Exception as e:
            print(f"Error cargando historial de URLs: {e}")
            self.url_history = set()
    
    def _update_url_combo(self):
        """Actualiza el combobox con el historial de URLs."""
        self.url_combo['values'] = list(self.url_history)
    
    def _save_url_history(self):
        """Guarda el historial de URLs en un archivo."""
        try:
            with open('url_history.json', 'w') as f:
                json.dump(list(self.url_history), f)
        except Exception as e:
            print(f"Error guardando historial de URLs: {e}")