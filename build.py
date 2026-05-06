#!/usr/bin/env python3
"""
Build script para crear .exe portátil en Windows
Ejecutar: python build.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step_num, message):
    print(f"\n[{step_num}/5] {message}")
    print("-" * 60)

def run_command(cmd, description):
    """Ejecuta comando y muestra resultado."""
    print(f"  Ejecutando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✅ {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"  ❌ Comando no encontrado. ¿Está instalado?")
        return False

def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   vMix Schedule 44 - EXE Builder (Windows)             ║
    ║   Creará un .exe portátil independiente                ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Verificar Python
    print_step(1, "Verificando requisitos")
    print(f"  Python: {sys.version}")
    if sys.version_info < (3, 8):
        print("  ❌ Se requiere Python 3.8+")
        return False
    print("  ✅ Python 3.8+ detectado")
    
    # Crear venv
    print_step(2, "Creando entorno virtual")
    venv_path = Path("venv")
    if venv_path.exists():
        print("  ✅ Entorno virtual ya existe")
    else:
        if not run_command([sys.executable, "-m", "venv", "venv"], 
                          "Entorno virtual creado"):
            return False
    
    # Detectar python del venv
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Instalar dependencias
    print_step(3, "Instalando dependencias")
    deps = ["--upgrade", "pip", "setuptools", "wheel", "pyinstaller", "requests", "PySide6"]
    if not run_command([str(pip_exe)] + deps, "Dependencias instaladas"):
        print("  ⚠️ Algunos errores, intentando continuar...")
    
    # Limpiar builds anteriores
    print_step(4, "Compilando .exe")
    print("  Limpiando builds anteriores...")
    for folder in ["build", "dist", "__pycache__"]:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"    Removido: {folder}")
    
    # Construir con PyInstaller
    spec_command = [
        str(python_exe),
        "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--name", "vMix_Schedule_44",
        "--clean",
        "main_windows.py"
    ]
    
    if not run_command(spec_command, ".exe compilado"):
        print("  ❌ Error en compilación")
        return False
    
    # Resultado final
    print_step(5, "Finalizando")
    exe_path = Path("dist") / "vMix_Schedule_44" / "vMix_Schedule_44.exe"
    if exe_path.exists():
        print(f"  ✅ .exe creado: {exe_path}")
    else:
        print(f"  ❌ .exe no encontrado en {exe_path}")
        return False
    
    # Resumen
    print(f"""
    ╔════════════════════════════════════════════════════════╗
    ║   ✅ COMPILACIÓN EXITOSA                               ║
    ╠════════════════════════════════════════════════════════╣
    ║   .exe portátil: dist/vMix_Schedule_44/               ║
    ║                                                        ║
    ║   Próximos pasos:                                      ║
    ║   1. Copia carpeta 'dist/vMix_Schedule_44' a lugar    ║
    ║      seguro o USB                                      ║
    ║   2. Ejecuta vMix_Schedule_44.exe                      ║
    ║   3. Asegúrate que vMix esté en:                       ║
    ║      http://192.168.192.140:8098                       ║
    ║                                                        ║
    ║   El programa es TOTALMENTE PORTÁTIL                   ║
    ║   (Funciona en cualquier Windows 10/11)                ║
    ╚════════════════════════════════════════════════════════╝
    """)
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Compilación cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
