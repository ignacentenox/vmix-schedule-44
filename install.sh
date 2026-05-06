#!/bin/bash
# vMix Schedule 44 - Instalador Automático desde GitHub
# Ejecutar en TrueNAS: bash <(curl -fsSL https://raw.githubusercontent.com/ignaciomanuel/vmix-schedule-44/main/install.sh)

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🚀 vMix Schedule 44 - Installer Automático                  ║"
echo "║     Instalando desde GitHub...                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

REPO_URL="https://github.com/ignaciomanuel/vmix-schedule-44.git"
INSTALL_DIR="/opt/vmix-schedule-44"

echo "[1/7] Creando directorios..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/{data,logs,frontend}
cd $INSTALL_DIR

echo "[2/7] Descargando archivos desde GitHub..."
git clone --depth 1 $REPO_URL . || {
    echo "⚠️  Clone falló, intentando con wget..."
    cd /tmp
    wget -q -O vmix-schedule-44.tar.gz https://github.com/ignaciomanuel/vmix-schedule-44/archive/refs/heads/main.tar.gz
    tar -xzf vmix-schedule-44.tar.gz
    mv vmix-schedule-44-main/* $INSTALL_DIR/
    rm -rf vmix-schedule-44-main vmix-schedule-44.tar.gz
}

echo "[3/7] Instalando dependencias del sistema..."
if [ -f /usr/bin/pkg ]; then
    # FreeBSD (TrueNAS)
    pkg install -y python39 py39-pip nginx 2>/dev/null || true
    PY_BIN="python3.9"
elif [ -f /usr/bin/apt ]; then
    # Linux
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv nginx 2>/dev/null || true
    PY_BIN="python3"
else
    echo "❌ OS no soportado. Instala Python 3.9+ y Nginx manualmente."
    exit 1
fi

echo "[4/7] Creando entorno virtual Python..."
$PY_BIN -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate
pip install --upgrade pip 2>/dev/null
pip install -q -r $INSTALL_DIR/requirements.txt

echo "[5/7] Configurando Nginx..."
mkdir -p /usr/local/etc/nginx 2>/dev/null || mkdir -p /etc/nginx/sites-available 2>/dev/null || true
if [ -f $INSTALL_DIR/deploy/nginx.conf ]; then
    if [ -d /usr/local/etc/nginx ]; then
        sudo cp $INSTALL_DIR/deploy/nginx.conf /usr/local/etc/nginx/vmix-schedule-44.conf
    else
        sudo cp $INSTALL_DIR/deploy/nginx.conf /etc/nginx/sites-available/vmix-schedule-44.conf
        sudo ln -sf /etc/nginx/sites-available/vmix-schedule-44.conf /etc/nginx/sites-enabled/vmix-schedule-44.conf 2>/dev/null || true
    fi
fi

echo "[6/7] Creando servicio systemd..."
sudo bash -c 'cat > /etc/systemd/system/vmix-schedule-44.service << EOFSVC
[Unit]
Description=vMix Schedule 44 - Web API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory='$INSTALL_DIR'
ExecStart='$INSTALL_DIR'/venv/bin/gunicorn -b 127.0.0.1:5000 api:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSVC'

echo "[7/7] Inicializando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable nginx 2>/dev/null || true
sudo systemctl enable vmix-schedule-44 2>/dev/null || true
sudo systemctl start nginx 2>/dev/null || true
sudo systemctl start vmix-schedule-44 2>/dev/null || true

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Acceso:    http://192.168.192.44/ui/"
echo "📍 Ubicación: $INSTALL_DIR"
echo "🔧 Logs:      sudo tail -f $INSTALL_DIR/logs/api.log"
echo ""
echo "Verificar estado:"
echo "  sudo systemctl status vmix-schedule-44"
echo "  sudo systemctl status nginx"
echo ""
echo "Abrir en navegador: http://192.168.192.44/ui/"
echo ""
