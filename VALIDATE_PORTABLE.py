#!/usr/bin/env python3
"""
Validador de Portabilidad - vMix Schedule 44 para Windows
Verifica que TODO está listo para compilar a .exe
"""

import os
import sys
import json
from pathlib import Path

def check_file(path, description):
    """Verifica si un archivo existe y muestra estado."""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    size_info = f" ({os.path.getsize(path)/1024:.1f} KB)" if exists else ""
    print(f"{status} {description}{size_info}")
    return exists

def check_content(filepath, search_str, description):
    """Verifica que un archivo contiene cierto contenido."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            found = search_str in content
            status = "✅" if found else "❌"
            print(f"{status} {description}")
            return found
    except Exception as e:
        print(f"❌ Error leyendo {filepath}: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("  🔍 VALIDACIÓN: vMix Schedule 44 - PORTABLE PARA WINDOWS")
    print("="*70 + "\n")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    all_ok = True
    
    # ========== ARCHIVOS CRÍTICOS ==========
    print("📋 ARCHIVOS CRÍTICOS:")
    critical_files = {
        "BUILD_BRANDED.bat": "Script compilación one-click para Windows",
        "build_branded.py": "Builder Python (alternativa)",
        "main_windows.py": "Código fuente (DEBE tener rutas portables)",
        "app_icon.png": "Logo 44 Contenidos para .exe",
        "requirements.txt": "Dependencias Python",
    }
    
    for filename, description in critical_files.items():
        all_ok &= check_file(filename, f"  {description}")
    
    # ========== VERIFICAR main_windows.py ==========
    print("\n🔧 VERIFICACIÓN main_windows.py (PORTABILIDAD):")
    all_ok &= check_content(
        "main_windows.py",
        "if getattr(sys, 'frozen', False):",
        "  Detección de .exe (sys.frozen)"
    )
    all_ok &= check_content(
        "main_windows.py",
        "BASE_DIR = os.path.dirname(sys.executable)",
        "  Ruta para .exe (relativa)"
    )
    all_ok &= check_content(
        "main_windows.py",
        "BASE_DIR = os.path.dirname(os.path.abspath(__file__))",
        "  Ruta para script Python (relativa)"
    )
    all_ok &= check_content(
        "main_windows.py",
        "vMix Schedule 44 - Powered by IGNACE",
        "  Título branding correcto"
    )
    
    # ========== ARCHIVOS DE CONFIGURACIÓN ==========
    print("\n📊 ARCHIVOS DE DATOS (Se crean automáticamente):")
    check_file(
        "vMix_Schedule_44_Contenidos_Config.json",
        "  Configuración (se crea en primera ejecución)"
    )
    check_file(
        "vMix_Schedule_44_Contenidos_DB.json",
        "  Base de datos eventos (se crea en primera ejecución)"
    )
    
    # ========== DOCUMENTACIÓN ==========
    print("\n📚 DOCUMENTACIÓN PARA USUARIO WINDOWS:")
    docs = [
        "GENERAR_EXE_WINDOWS.txt",
        "CHECKLIST_WINDOWS.txt",
        "README_POINT_ENTRADA.md",
    ]
    for doc in docs:
        check_file(doc, f"  {doc}")
    
    # ========== VERIFICAR contenido BUILD_BRANDED.bat ==========
    print("\n⚙️  VERIFICACIÓN BUILD_BRANDED.bat:")
    all_ok &= check_content(
        "BUILD_BRANDED.bat",
        "python --version",
        "  Verifica Python instalado"
    )
    all_ok &= check_content(
        "BUILD_BRANDED.bat",
        "python -m venv venv",
        "  Crea entorno virtual"
    )
    all_ok &= check_content(
        "BUILD_BRANDED.bat",
        "python build_branded.py",
        "  Ejecuta builder Python"
    )
    
    # ========== VERIFICAR app_icon.png ==========
    print("\n🎨 VERIFICACIÓN LOGO:")
    if check_file("app_icon.png", "  Logo PNG (68 KB)"):
        try:
            from PIL import Image
            img = Image.open("app_icon.png")
            print(f"    Resolución: {img.width}x{img.height}")
            print(f"    Modo: {img.mode}")
            if img.mode == "RGBA":
                print("    ✅ Transparencia detectada (PNG con alpha)")
            print("    ✅ PIL/Pillow disponible (conversión PNG→ICO posible)")
        except ImportError:
            print("    ⚠️  PIL no instalado (se instalará durante build)")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # ========== RESULTADO FINAL ==========
    print("\n" + "="*70)
    
    if all_ok:
        print("✅ TODO LISTO PARA COMPILAR A .EXE EN WINDOWS")
        print("\nPRÓXIMOS PASOS:")
        print("  1. Comprimir carpeta 'scheduletv' en ZIP")
        print("  2. Enviar a usuario Windows")
        print("  3. Usuario ejecuta: BUILD_BRANDED.bat")
        print("  4. Esperar 5-10 minutos")
        print("  5. ¡Obtener dist/vMix_Schedule_44/vMix_Schedule_44.exe!")
    else:
        print("❌ FALTAN ARCHIVOS O CONFIGURACIÓN INCOMPLETA")
        print("\nVerifica los elementos marcados con ❌ arriba")
    
    print("\n" + "="*70)
    print("🎬 vMix Schedule 44 - Powered by IGNACE")
    print("   Logo: 44 Contenidos")
    print("="*70 + "\n")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
