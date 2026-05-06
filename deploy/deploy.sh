#!/bin/bash
#
# vMix Schedule 44 - Script de Deploy para TrueNAS
# Ejecutar como: bash deploy.sh
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🎬 vMix Schedule 44 - DEPLOY EN TRUENAS                    ║"
echo "║                                                               ║"
echo "║   Instalará la app en: /opt/vmix-schedule-44                 ║"
echo "║   Acceso: http://192.168.192.44/ui/                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Detectar sistema operativo
OS_TYPE=$(uname -s)
echo "[1/8] Sistema detectado: $OS_TYPE"

# Verificar si ejecuta como root
if [ "$EUID" -ne 0 ]; then
   echo "❌ Este script debe ejecutarse con sudo"
   exit 1
fi

echo "✅ Ejecutando como root"
echo ""

# --- PASO 2: INSTALAR DEPENDENCIAS ---
echo "[2/8] Instalando dependencias del sistema..."

if [ "$OS_TYPE" = "FreeBSD" ]; then
    # TrueNAS corre FreeBSD
    pkg update
    pkg install -y python39 py39-pip py39-virtualenv nginx
    PYTHON_BIN=python3.9
    PIP_BIN=pip3.9
elif [ "$OS_TYPE" = "Linux" ]; then
    # Para sistemas Linux
    apt-get update 2>/dev/null || yum update 2>/dev/null
    apt-get install -y python3 python3-pip python3-venv nginx 2>/dev/null || yum install -y python3 python3-pip nginx 2>/dev/null
    PYTHON_BIN=python3
    PIP_BIN=pip3
else
    echo "❌ Sistema operativo no soportado: $OS_TYPE"
    exit 1
fi

echo "✅ Dependencias instaladas"
echo ""

# --- PASO 3: CREAR DIRECTORIO ---
echo "[3/8] Creando directorios..."
mkdir -p /opt/vmix-schedule-44/data
mkdir -p /opt/vmix-schedule-44/logs
mkdir -p /opt/vmix-schedule-44/frontend

echo "✅ Directorios creados"
echo ""

# --- PASO 4: COPIAR ARCHIVOS ---
echo "[4/8] Copiando archivos de aplicación..."

# Este script asume que los archivos ya están en el servidor
# Si necesitas transferirlos, usa SCP o SFTP primero
if [ -f "/root/deploy/api.py" ]; then
    cp /root/deploy/api.py /opt/vmix-schedule-44/
    cp /root/deploy/requirements.txt /opt/vmix-schedule-44/
    cp -r /root/deploy/frontend/* /opt/vmix-schedule-44/frontend/
    echo "✅ Archivos copiados desde /root/deploy"
elif [ -f "./api.py" ]; then
    cp ./api.py /opt/vmix-schedule-44/
    cp ./requirements.txt /opt/vmix-schedule-44/
    cp -r ./frontend/* /opt/vmix-schedule-44/frontend/
    echo "✅ Archivos copiados desde directorio actual"
else
    echo "⚠️  Archivos no encontrados en ubicaciones esperadas"
    echo "Asegúrate de que api.py y frontend/ existan"
fi

echo ""

# --- PASO 5: CREAR ENTORNO VIRTUAL ---
echo "[5/8] Creando entorno virtual Python..."

cd /opt/vmix-schedule-44
$PYTHON_BIN -m venv venv
source venv/bin/activate

echo "✅ Entorno virtual creado"
echo ""

# --- PASO 6: INSTALAR DEPENDENCIAS PYTHON ---
echo "[6/8] Instalando dependencias Python..."

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencias Python instaladas"
echo ""

# --- PASO 7: CONFIGURAR NGINX ---
echo "[7/8] Configurando Nginx..."

# Copiar configuración de Nginx
cp /opt/vmix-schedule-44/nginx.conf /etc/nginx/sites-available/vmix-schedule-44 2>/dev/null || \
cp /opt/vmix-schedule-44/nginx.conf /usr/local/etc/nginx/sites-available/vmix-schedule-44

# Crear enlace simbólico
ln -sf /etc/nginx/sites-available/vmix-schedule-44 /etc/nginx/sites-enabled/ 2>/dev/null || \
ln -sf /usr/local/etc/nginx/sites-available/vmix-schedule-44 /usr/local/etc/nginx/sites-enabled/ 2>/dev/null

# Probar configuración
if command -v nginx &> /dev/null; then
    nginx -t
    echo "✅ Nginx configurado"
else
    echo "⚠️  Nginx no encontrado, continuando sin web server"
fi

echo ""

# --- PASO 8: CREAR SERVICIO SYSTEMD/INIT ---
echo "[8/8] Creando servicio de sistema..."

cat > /etc/systemd/system/vmix-schedule-44.service << 'EOF'
[Unit]
Description=vMix Schedule 44 - API Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vmix-schedule-44
Environment="PATH=/opt/vmix-schedule-44/venv/bin"
ExecStart=/opt/vmix-schedule-44/venv/bin/python /opt/vmix-schedule-44/api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

chmod 644 /etc/systemd/system/vmix-schedule-44.service
systemctl daemon-reload

echo "✅ Servicio creado"
echo ""

# --- FINALIZACIÓN ---
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ INSTALACIÓN COMPLETADA                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 UBICACIÓN DE LA APP:     /opt/vmix-schedule-44"
echo "🌐 ACCESO WEB:             http://192.168.192.44/ui/"
echo "🔧 CONFIG:                 /opt/vmix-schedule-44/data/"
echo "📝 LOGS:                   /opt/vmix-schedule-44/logs/"
echo ""
echo "🚀 INICIAR SERVICIO:"
echo "   systemctl start vmix-schedule-44"
echo "   systemctl status vmix-schedule-44"
echo ""
echo "📋 INICIAR NGINX:"
echo "   systemctl start nginx"
echo "   systemctl status nginx"
echo ""
echo "🔄 COMANDOS ÚTILES:"
echo "   systemctl enable vmix-schedule-44    # Autostart al reiniciar"
echo "   systemctl restart vmix-schedule-44   # Reiniciar servicio"
echo "   tail -f /opt/vmix-schedule-44/logs/api.log"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   1. Ajusta la IP de vMix en /opt/vmix-schedule-44/data/config.json"
echo "   2. Asegúrate que vMix sea accesible desde TrueNAS (ping 192.168.192.140)"
echo ""
