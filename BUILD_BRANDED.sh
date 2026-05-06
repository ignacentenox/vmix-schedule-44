#!/bin/bash
# ================================================================
# vMix Schedule 44 - EXE Builder (Mac/Linux)
# Logo: 44 Contenidos
# Título: vMix Schedule 44 - Powered by IGNACE
# ================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   vMix SCHEDULE 44 - BRANDED EXE BUILDER (Mac/Linux)      ║"
echo "║   Logo: 44 Contenidos                                      ║"
echo "║   Título: vMix Schedule 44 - Powered by IGNACE             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar Python
echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    echo "📥 Instala desde: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION detectado"
echo ""

# Crear venv si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ venv creado"
else
    echo "✅ venv ya existe"
fi

echo ""

# Activar venv y ejecutar builder
source venv/bin/activate

echo "🚀 Iniciando compilación..."
echo ""

python3 build_branded.py

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   ✅ COMPILACIÓN EXITOSA                                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📍 El .exe está en:  dist/vMix_Schedule_44/"
    echo ""
    echo "🎯 Próximos pasos:"
    echo ""
    echo "   1. Copia la carpeta 'dist/vMix_Schedule_44' a tu USB"
    echo "   2. O comprime en ZIP para distribuir"
    echo "   3. Ejecuta desde Windows: vMix_Schedule_44.exe"
    echo ""
    echo "💡 El programa es TOTALMENTE PORTABLE"
    echo "   (Funciona sin instalar nada en Windows 10/11)"
    echo ""
else
    echo ""
    echo "❌ Error en la compilación"
    echo "   Verifica los errores arriba"
    exit 1
fi
