#!/usr/bin/env python3
"""
🎨 Conversor PNG → ICO y Builder de .exe
Convierte el logo PNG a ICO y compila el .exe con branding de 44 Contenidos
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def convert_png_to_ico():
    """Convierte app_icon.png a app.ico usando PIL"""
    print_section("1️⃣  CONVIRTIENDO LOGO PNG → ICO")
    
    try:
        from PIL import Image
        
        png_path = Path("app_icon.png")
        ico_path = Path("app.ico")
        
        if not png_path.exists():
            print("❌ No se encontró app_icon.png")
            return False
        
        print(f"  📂 PNG origen: {png_path.name} ({png_path.stat().st_size / 1024:.1f} KB)")
        
        # Abrir imagen PNG
        img = Image.open(png_path)
        print(f"  📏 Dimensiones originales: {img.size}")
        
        # Redimensionar a tamaño estándar para ICO
        size = (256, 256)
        img_resized = img.resize(size, Image.Resampling.LANCZOS)
        print(f"  ✂️  Redimensionado a: {size}")
        
        # Convertir a RGB si tiene canal alfa
        if img_resized.mode == 'RGBA':
            print(f"  🎨 Convertiendo RGBA → RGB")
            background = Image.new('RGB', size, (255, 255, 255))
            background.paste(img_resized, mask=img_resized.split()[3] if len(img_resized.split()) > 3 else None)
            img_resized = background
        
        # Guardar como ICO
        img_resized.save(ico_path, format='ICO')
        print(f"  ✅ ICO creado: {ico_path.name} ({ico_path.stat().st_size / 1024:.1f} KB)")
        
        return True
    
    except ImportError:
        print("❌ Pillow no instalada. Instalando...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
            return convert_png_to_ico()  # Reintentar
        except:
            print("❌ Error instalando Pillow")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def install_dependencies():
    """Instala dependencias necesarias"""
    print_section("2️⃣  INSTALANDO DEPENDENCIAS")
    
    deps = ["pyinstaller", "requests", "PySide6", "Pillow"]
    print(f"  📦 Paquetes a instalar: {', '.join(deps)}\n")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade"] + deps,
            check=True
        )
        print("\n  ✅ Todas las dependencias instaladas")
        return True
    except Exception as e:
        print(f"\n  ❌ Error instalando dependencias: {e}")
        return False

def cleanup_builds():
    """Limpia builds anteriores"""
    print_section("3️⃣  LIMPIANDO BUILDS ANTERIORES")
    
    folders_to_remove = ["build", "dist", "__pycache__", "*.spec"]
    
    for pattern in folders_to_remove:
        if "*" in pattern:
            # Buscar archivos con patrón
            import glob
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                    print(f"  🗑️  Removido: {file}")
                except:
                    pass
        else:
            # Remover carpeta
            if Path(pattern).exists():
                shutil.rmtree(pattern)
                print(f"  🗑️  Removido: {pattern}/")
    
    print("  ✅ Limpieza completada")

def build_exe():
    """Compila el .exe con PyInstaller"""
    print_section("4️⃣  COMPILANDO .EXE CON PYINSTALLER")
    
    ico_path = Path("app.ico")
    if not ico_path.exists():
        print("  ⚠️  app.ico no encontrado, compilando sin icono")
        icon_arg = []
    else:
        icon_arg = ["--icon", str(ico_path)]
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--name", "vMix_Schedule_44",
        "--add-data", "app_icon.png:.",
        "--add-data", "vMix_Schedule_44_Contenidos_DB.json:.",
        "--add-data", "vMix_Schedule_44_Contenidos_Config.json:.",
        "--console",  # Mostrar consola para debugging
        "--clean",
    ] + icon_arg + [
        "main_windows.py"
    ]
    
    print(f"  🔨 Comando: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n  ✅ .exe compilado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n  ❌ Error en compilación: {e}")
        return False
    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        return False

def verify_exe():
    """Verifica que el .exe se haya creado correctamente"""
    print_section("5️⃣  VERIFICANDO RESULTADO")
    
    exe_path = Path("dist") / "vMix_Schedule_44" / "vMix_Schedule_44.exe"
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ .exe encontrado: {exe_path}")
        print(f"  📊 Tamaño: {size_mb:.1f} MB")
        
        # Contar archivos en dist
        dist_path = Path("dist") / "vMix_Schedule_44"
        file_count = len(list(dist_path.glob("**/*")))
        print(f"  📁 Archivos incluidos: {file_count}")
        
        return True
    else:
        print(f"  ❌ .exe no encontrado en {exe_path}")
        return False

def print_summary(success):
    """Imprime resumen final"""
    if success:
        print_section("✅ COMPILACIÓN COMPLETADA CON ÉXITO")
        
        summary = """
╔════════════════════════════════════════════════════════════╗
║          🎉 vMix SCHEDULE 44 - EXE PORTABLE              ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  📂 Ubicación:  dist/vMix_Schedule_44/                    ║
║  🎯 Ejecutable: vMix_Schedule_44.exe                      ║
║  🎨 Logo:       44 Contenidos (integrado)                ║
║  📋 Título:     vMix Schedule 44 - Powered by IGNACE      ║
║                                                            ║
║  ✨ El programa es 100% PORTABLE                          ║
║     (Funciona en cualquier Windows 10/11)                 ║
║                                                            ║
║  📋 Próximos pasos:                                        ║
║     1. Copia la carpeta 'dist/vMix_Schedule_44' a tu PC   ║
║     2. O comprime en ZIP para distribuir                  ║
║     3. Ejecuta vMix_Schedule_44.exe                       ║
║     4. El programa buscará vMix en:                        ║
║        http://192.168.192.140:8098                        ║
║                                                            ║
║  💡 VENTAJAS:                                              ║
║     ✅ Sin instalación                                    ║
║     ✅ Sin dependencias                                   ║
║     ✅ Funciona en USB                                    ║
║     ✅ Se lleva los datos con la carpeta                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        """
        print(summary)
    else:
        print_section("❌ ERROR EN LA COMPILACIÓN")
        print("  Verifica los errores arriba")

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   vMix Schedule 44 - EXE BUILDER                           ║
    ║   Powered by IGNACE                                        ║
    ║   Logo: 44 Contenidos                                      ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 1. Convertir PNG a ICO
        if not convert_png_to_ico():
            print("  ⚠️  Continuando sin icono...")
        
        # 2. Instalar dependencias
        if not install_dependencies():
            return False
        
        # 3. Limpiar builds anteriores
        cleanup_builds()
        
        # 4. Compilar .exe
        if not build_exe():
            return False
        
        # 5. Verificar resultado
        if not verify_exe():
            return False
        
        # 6. Resumen
        print_summary(True)
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ Compilación cancelada por usuario")
        return False
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
