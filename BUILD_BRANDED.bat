@echo off
REM ================================================================
REM   vMix Schedule 44 - EXE Builder (Windows) - Branded Edition
REM   Logo: 44 Contenidos
REM   Título: vMix Schedule 44 - Powered by IGNACE
REM ================================================================

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   vMix SCHEDULE 44 - BRANDED EXE BUILDER                  ║
echo ║   Logo: 44 Contenidos                                      ║
echo ║   Título: vMix Schedule 44 - Powered by IGNACE             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar Python
echo [1/1] Verificando requisitos...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo.
    echo 📥 Descarga Python desde: https://www.python.org/downloads/
    echo.
    echo ✅ Durante la instalación, MARCA "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Crear venv si no existe
if not exist "venv" (
    echo [2/1] Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Error creando venv
        pause
        exit /b 1
    )
    echo ✅ venv creado
) else (
    echo ✅ venv ya existe
)

echo.
echo [3/1] Iniciando compilación...
echo.

REM Activar venv y ejecutar builder
call venv\Scripts\activate.bat

REM Ejecutar el builder branded
python build_branded.py

if errorlevel 1 (
    echo.
    echo ❌ Error en la compilación
    echo.
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   ✅ COMPILACIÓN EXITOSA                                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📍 El .exe está en:  dist\vMix_Schedule_44\
echo.
echo 🎯 Próximos pasos:
echo.
echo    1. Abre el explorador: dist\vMix_Schedule_44\
echo    2. Copia esta carpeta a tu PC o USB
echo    3. Ejecuta: vMix_Schedule_44.exe
echo.
echo 💡 El programa es TOTALMENTE PORTABLE
echo    (Funciona sin instalar nada)
echo.
pause
