# 🌐 Website Checker

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 🚀 Una poderosa herramienta de monitoreo de sitios web con interfaz gráfica, desarrollada en Python.
>
> _Proyecto generado utilizando Claude 3.5 Sonnet_

## 📋 Características

- ✨ **Interfaz Gráfica Intuitiva**
  - Panel de control centralizado
  - Tema claro/oscuro
  - Visualización de estadísticas en tiempo real
  - Gráficos interactivos

- 🔍 **Monitoreo Avanzado**
  - Verificación de disponibilidad
  - Tiempos de respuesta
  - Análisis de certificados SSL
  - Estado de servidores
  - Códigos de respuesta HTTP

- 📊 **Análisis y Reportes**
  - Estadísticas detalladas
  - Histórico de verificaciones
  - Exportación a CSV/JSON
  - Gráficos de rendimiento

- ⚡ **Características Técnicas**
  - Verificaciones asíncronas
  - Sistema de caché
  - Validación de URLs
  - Manejo de errores robusto
  - Soporte para múltiples protocolos

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/kigaldev/WebChecker
cd website-checker
```

2. **Crear entorno virtual**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Unix/MacOS
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

## 🚀 Uso

1. **Iniciar la aplicación**
```bash
python webchecker.py
```

2. **Verificar un sitio web**
   - Ingresa la URL en el campo de texto
   - Haz clic en "Verificar"
   - Observa los resultados en tiempo real

3. **Características adicionales**
   - Activar auto-refresh para monitoreo continuo
   - Exportar datos para análisis
   - Visualizar estadísticas y gráficos
   - Configurar notificaciones

## 📁 Estructura del Proyecto

```
website_checker/
│
├── src/
│   ├── gui/                 # Interfaz gráfica
│   │   ├── main_window.py   # Ventana principal
│   │
│   ├── core/               # Lógica principal
│   │   ├── checker.py      # Verificador de sitios
│   │
│   └── utils/              # Utilidades
│       ├── validators.py   # Validación de URLs
│
├── tests/                  # Pruebas unitarias
├── requirements.txt        # Dependencias
└── webchecker.py          # Punto de entrada
```

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
pytest

# Pruebas con cobertura
pytest --cov=src

# Reporte HTML de cobertura
pytest --cov=src --cov-report=html
```

## 📋 Requisitos

- Python 3.8 o superior
- Dependencias listadas en `requirements.txt`

## 🔧 Dependencias Principales

- **GUI**: `tkinter`
- **Networking**: `aiohttp`, `urllib3`
- **Testing**: `pytest`, `pytest-cov`
- **Visualización**: `matplotlib`
- **Validación**: `validators`

## 🎯 Características Futuras

- [ ] Monitoreo de múltiples URLs en paralelo
- [ ] Sistema de notificaciones (email, desktop)
- [ ] API REST
- [ ] Dashboard web
- [ ] Integración con servicios de monitoreo
- [ ] Análisis de contenido y cambios
- [ ] Soporte para autenticación
- [ ] Exportación de reportes PDF

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Autores

- [KIGALDEV](https://github.com/kigaldev)
  - Asistido por Claude 3.5 Sonnet

## 🙏 Agradecimientos

- Claude 3.5 Sonnet por la asistencia en el desarrollo
- [Python](https://www.python.org/) por el lenguaje de programación
- La comunidad de código abierto por las herramientas y librerías utilizadas

---

<p align="center">
  Desarrollado con ❤️ y ☕
</p>