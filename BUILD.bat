@echo off
REM Build script para crear .exe portátil en Windows
REM Asegúrate de tener Python 3.8+ instalado

echo ==================================================
echo   vMix Schedule 44 - Builder (Windows)
echo ==================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH
    echo Descarga Python desde: https://www.python.org/downloads/
    echo Asegúrate de seleccionar "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/5] Python detectado. Creando entorno virtual...
if not exist "venv" (
    python -m venv venv
) else (
    echo       Entorno virtual ya existe
)

echo [2/5] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [3/5] Instalando dependencias...
pip install --upgrade pip setuptools wheel
pip install pyinstaller requests PySide6

echo [4/5] Construyendo .exe...
pyinstaller --onedir --windowed --name "vMix_Schedule_44" ^
    --icon=app.ico ^
    --add-data "vMix_Schedule_44_Contenidos_DB.json;." ^
    --add-data "vMix_Schedule_44_Contenidos_Config.json;." ^
    main_windows.py

echo [5/5] Limpiando archivos temporales...
rmdir /s /q build
del vMix_Schedule_44.spec

echo.
echo ==================================================
echo   ✅ CONSTRUCCIÓN COMPLETADA
echo ==================================================
echo.
echo El .exe portátil está en: dist\vMix_Schedule_44\
echo.
echo Para ejecutar:
echo   1. Copia la carpeta "dist\vMix_Schedule_44" a cualquier lugar
echo   2. Ejecuta "vMix_Schedule_44.exe"
echo.
echo Requisitos:
echo   - Windows 10 / Windows 11
echo   - Conexión a vMix (http://192.168.192.140:8098)
echo.
pause
