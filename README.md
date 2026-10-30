# TeraPrint (fractionation-print)

Aplicación de escritorio para Windows desarrollada en Python, que expone un backend web con Flask para la impresión de fraccionamientos (likely Ticket/"fracción") e incluye utilidades para Chile como el manejo de RUT.

## Requisitos

- **Python 3.14** (probado con Python 3.14.0 en Windows 10)
- **Windows** (el proyecto depende de `pywin32` para interactuar con el sistema/imprersoras)
- PowerShell (para los comandos de ejemplo)

## Dependencias

Las dependencias están declaradas en `requirements.txt`:

| Paquete | Versión instalada | Uso |
| --- | --- | --- |
| pywin32 | 312 | Acceso a APIs de Windows (impresión, COM, etc.) |
| rut-chile | 2.0.1 | Validación y formateo de RUT chileno |
| flask | 3.1.3 | Framework web / backend local |
| flask-cors | 6.0.5 | Soporte CORS para el backend Flask |
| jinja2 | 3.1.6 | Motor de plantillas |
| werkzeug | 3.1.9 | Servidor WSGI |
| markupsafe | 3.0.4 | Escape seguro de HTML |
| itsdangerous | 2.2.0 | Firmas criptográficas (sesiones Flask) |
| click | 8.5.0 | Interfaz de línea de comandos |
| blinker | 1.9.0 | Señales de eventos (Flask) |
| colorama | 0.4.6 | Colores en consola de Windows |

## Instalación

1. Clona o copia el proyecto y sitúate en su carpeta:

   ```powershell
   cd C:\Users\<usuario>\Workspace\Projects\fractionation-print
   ```

2. Crea el entorno virtual (nota: es `python -m venv .venv`):

   ```powershell
   python -m venv .venv
   ```

3. Activa el entorno virtual en PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   > Si PowerShell bloquea el script, habilita temporalmente la ejecución con:
   > `Set-ExecutionPolicy -Scope Process RemoteSigned`

4. Instala las dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

## Compilar el ejecutable (PyInstaller)

El proyecto incluye un archivo de especificación `TeraPrint.spec` para generar un ejecutable standalone con PyInstaller (v6.22.3):

```powershell
pyinstaller --clean .\TeraPrint.spec
```

- El ejecutable resultante queda en `dist\TeraPrint.exe`.
- Los archivos intermedios de compilación se guardan en `build\TeraPrint\`.
- La opción `--clean` limpia la caché de PyInstaller antes de compilar.

> Nota: el log de compilación muestra advertencias no críticas (`Hidden import 'pkg_resources.py2_warn' not found`, `blinkercolorama not found`); no impiden generar el ejecutable.

## Uso

- **Modo desarrollo:** ejecuta el script principal dentro del entorno virtual activado (`python tu_script.py`).
- **Modo producción/distribución:** distribuye `dist\TeraPrint.exe`; no requiere Python instalado en la máquina destino.

## Pruebas de impresión

- **Probar código ZPL:** puedes visualizar y probar el código ZPL en línea usando [Labelary Viewer](https://labelary.com/viewer.html).
- **Probar el funcionamiento del programa:** ejecuta el programa y utiliza el archivo `testing.html` junto con una impresora Zebra virtual, como [Virtual-ZPL-Printer](https://github.com/porrey/Virtual-ZPL-Printer).

## Estructura del proyecto

```text
fractionation-print/
├── requirements.txt     # Dependencias del proyecto
├── tu_script.py        # Script principal
├── TeraPrint.spec      # Especificación de PyInstaller
├── build/              # Archivos intermedios de compilación
└── dist/
    └── TeraPrint.exe   # Ejecutable final
```