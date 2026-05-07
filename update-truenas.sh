#!/bin/bash
# Script para actualizar vMix Schedule 44 en TrueNAS sin reinstalar

set -e

INSTALL_DIR="/mnt/vmix-schedule-44"
DEPLOY_DIR="$INSTALL_DIR/deploy"

echo "📦 Actualizando vMix Schedule 44..."

# 1. Actualizar código desde GitHub
echo "🔄 Descargando cambios..."
cd "$INSTALL_DIR"
git pull origin main

# 2. Copiar archivos al directorio de deploy si es necesario
echo "📋 Sincronizando archivos..."
if [ -f "vMix_Schedule_44_Contenidos_DB.json" ]; then
    cp vMix_Schedule_44_Contenidos_DB.json "$DEPLOY_DIR/data/" 2>/dev/null || true
fi

# 3. Instalar dependencias nuevas (si las hay)
echo "📚 Verificando dependencias..."
export PYTHONPATH="$DEPLOY_DIR/lib"
python3.11 -m pip install --target="$DEPLOY_DIR/lib" --upgrade flask flask-cors gunicorn requests 2>&1 | grep -i "successfully\|already" || true

# 4. Reiniciar servicio
echo "🔄 Reiniciando servicio..."
systemctl restart vmix-schedule-44

# 5. Verificar que está corriendo
sleep 2
if systemctl is-active --quiet vmix-schedule-44; then
    echo "✅ Servicio reiniciado correctamente"
    echo "🌐 Accede a: http://192.168.192.44:8080"
else
    echo "❌ Error al reiniciar servicio"
    systemctl status vmix-schedule-44
    exit 1
fi
