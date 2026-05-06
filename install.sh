#!/bin/sh
# vMix Schedule 44 - Instalador Automático desde GitHub para TrueNAS
# Ejecutar: curl -fsSL https://raw.githubusercontent.com/ignacentenox/vmix-schedule-44/main/install.sh | sudo sh

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🚀 vMix Schedule 44 - Installer Automático                  ║"
echo "║     Sistema: TrueNAS / FreeBSD / Linux                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Verificar si se ejecuta con sudo
if [ "$(id -u)" -ne 0 ]; then 
    echo "ℹ️  Se necesitan permisos de root."
    echo "   Ejecuta: curl -fsSL https://raw.githubusercontent.com/ignacentenox/vmix-schedule-44/main/install.sh | sudo sh"
    exit 1
fi

REPO_URL="https://github.com/ignacentenox/vmix-schedule-44.git"
INSTALL_DIR="/opt/vmix-schedule-44"

# Detectar mejor ruta si /opt no es escribible
echo "[1/7] Detectando ruta de instalación..."
if ! mkdir -p "$INSTALL_DIR" 2>/dev/null || ! touch "$INSTALL_DIR/.test" 2>/dev/null; then
    echo "⚠️  /opt no escribible, intentando /mnt/..."
    INSTALL_DIR="/mnt/vmix-schedule-44"
    if ! mkdir -p "$INSTALL_DIR" 2>/dev/null; then
        echo "⚠️  /mnt no disponible, intentando /var/lib/..."
        INSTALL_DIR="/var/lib/vmix-schedule-44"
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR" || {
        echo "❌ No se pudo crear directorio en ninguna ruta"
        exit 1
    }
fi

rm -f "$INSTALL_DIR/.test" 2>/dev/null || true
mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/frontend"
cd "$INSTALL_DIR"

echo "✅ Instalando en: $INSTALL_DIR"
echo ""

echo "[2/7] Descargando desde GitHub..."
git clone --depth 1 $REPO_URL . 2>/dev/null || {
    echo "   Alternativa: wget..."
    cd /tmp
    rm -rf vmix-schedule-44-main vmix-schedule-44.tar.gz 2>/dev/null || true
    wget -q -O vmix-schedule-44.tar.gz https://github.com/ignacentenox/vmix-schedule-44/archive/refs/heads/main.tar.gz || {
        echo "❌ Error descargando. Verifica conexión a internet."
        exit 1
    }
    tar -xzf vmix-schedule-44.tar.gz
    cp -r vmix-schedule-44-main/* $INSTALL_DIR/ || exit 1
    cp -r vmix-schedule-44-main/.gitignore $INSTALL_DIR/ 2>/dev/null || true
    rm -rf vmix-schedule-44-main vmix-schedule-44.tar.gz
}

echo "[3/7] Instalando dependencias del sistema..."

# DEBUG: Mostrar qué se detecta
echo "   DEBUG: Buscando pkg..."
echo "      /usr/sbin/pkg existe: $(test -f /usr/sbin/pkg && echo 'SÍ' || echo 'NO')"
echo "      /usr/local/sbin/pkg existe: $(test -f /usr/local/sbin/pkg && echo 'SÍ' || echo 'NO')"
echo "      /usr/bin/apt-get existe: $(test -f /usr/bin/apt-get && echo 'SÍ' || echo 'NO')"
echo ""

# Detectar FreeBSD buscando pkg
if test -f /usr/sbin/pkg || test -f /usr/local/sbin/pkg; then
    echo "   ✅ Detectado: FreeBSD/TrueNAS (con pkg)"
    /usr/sbin/pkg install -y python39 py39-pip py39-venv nginx git 2>&1 | grep -E "(Installed|already)" || true
    PY_BIN="python3.9"
    USE_VENV=1
elif test -f /usr/bin/apt-get; then
    echo "   ⚠️  Detectado: Sistema con apt (No usar en TrueNAS!)"
    echo "   ⚠️  TrueNAS REQUIERE: sudo pkg install python39 py39-pip nginx git"
    echo "   ⚠️  O manualmente: pip3 install -r requirements.txt"
    echo ""
    echo "❌ ABORTANDO - No se debe usar apt en TrueNAS"
    exit 1
else
    echo "   ⚠️  No se detectó pkg ni apt. Intentando instalación manual..."
    # Buscar Python disponible
    if command -v python3.9 >/dev/null 2>&1; then
        echo "   ✅ Encontrado: python3.9"
        PY_BIN="python3.9"
        USE_VENV=0
    elif command -v python3 >/dev/null 2>&1; then
        echo "   ✅ Encontrado: python3"
        PY_BIN="python3"
        USE_VENV=0
    else
        echo "❌ No se encontró python. Instala manualmente:"
        echo "   En TrueNAS: sudo pkg install python39"
        exit 1
    fi
fi

echo "[4/7] Configurando Python..."
cd "$INSTALL_DIR"

if [ "$USE_VENV" = "1" ]; then
    # Crear virtual environment
    echo "   Creando venv..."
    $PY_BIN -m venv venv || {
        echo "❌ Error creando venv. Intenta: sudo pkg install py39-venv"
        exit 1
    }
    . venv/bin/activate
    echo "   ✅ Venv activado"
else
    # Instalar directo en sistema (sin venv)
    echo "   ⚠️  Instalando directo en sistema (sin venv)"
    PIP_CMD="$(which pip3 || which pip)"
    if [ -z "$PIP_CMD" ]; then
        echo "❌ pip no encontrado. Instala: sudo pkg install py39-pip"
        exit 1
    fi
fi

echo "[5/7] Instalando dependencias Python..."
if [ "$USE_VENV" = "1" ]; then
    pip install --upgrade pip 2>&1 | tail -1
    pip install -q -r requirements.txt || {
        echo "⚠️  Error con requirements.txt, intentando instalar individual..."
        pip install -q flask requests flask-cors gunicorn
    }
else
    # Sin venv, instalar en sistema
    $PIP_CMD install --user flask requests flask-cors gunicorn || {
        echo "⚠️  Error instalando dependencias con --user, intentando sin..."
        $PIP_CMD install flask requests flask-cors gunicorn
    }
fi
echo "   ✅ Dependencias instaladas"

echo "[5/7] Configurando Nginx..."
if [ -d /usr/local/etc/nginx ]; then
    # FreeBSD
    NGINX_CONF="/usr/local/etc/nginx/vmix-schedule-44.conf"
else
    # Linux
    NGINX_CONF="/etc/nginx/sites-available/vmix-schedule-44.conf"
    mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
fi

if [ -f "$INSTALL_DIR/deploy/nginx.conf" ]; then
    cp "$INSTALL_DIR/deploy/nginx.conf" "$NGINX_CONF"
    
    # Crear symlink en sites-enabled si es Linux
    if [ -d /etc/nginx/sites-enabled ]; then
        ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/vmix-schedule-44.conf
    fi
    echo "   ✅ Nginx configurado"
elif [ -f "$INSTALL_DIR/nginx.conf" ]; then
    cp "$INSTALL_DIR/nginx.conf" "$NGINX_CONF"
    echo "   ✅ Nginx configurado"
fi

echo "[6/7] Creando servicio systemd..."

# Configurar ExecStart según USE_VENV
if [ "$USE_VENV" = "1" ]; then
    EXEC_START="$INSTALL_DIR/venv/bin/gunicorn -b 127.0.0.1:5000 api:app"
else
    EXEC_START="$PY_BIN -m gunicorn -b 127.0.0.1:5000 api:app"
fi

cat > /etc/systemd/system/vmix-schedule-44.service << EOFSVC
[Unit]
Description=vMix Schedule 44 - Web API for vMix Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$EXEC_START
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/api.log
StandardError=append:$INSTALL_DIR/logs/api.log

[Install]
WantedBy=multi-user.target
EOFSVC

echo "   ✅ Servicio creado"

echo "[7/7] Iniciando servicios..."
systemctl daemon-reload
systemctl enable nginx vmix-schedule-44 2>/dev/null || true
systemctl start nginx 2>/dev/null || {
    echo "   ⚠️  Nginx puede estar corriendo ya"
}
systemctl start vmix-schedule-44 || {
    echo "   ⚠️  Error iniciando servicio. Ver logs:"
    echo "      tail -f $INSTALL_DIR/logs/api.log"
}

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 ACCESO WEB:    http://192.168.192.44/ui/"
echo "📍 UBICACIÓN:     $INSTALL_DIR"
echo "📊 LOGS:          tail -f $INSTALL_DIR/logs/api.log"
echo "⚙️  CONFIG:        $INSTALL_DIR/data/vMix_Schedule_44_Contenidos_Config.json"
echo ""
echo "Comandos útiles:"
echo "  Ver estado:      systemctl status vmix-schedule-44"
echo "  Reiniciar:       systemctl restart vmix-schedule-44"
echo "  Ver logs:        tail -f $INSTALL_DIR/logs/api.log"
echo ""
echo "Espera 3 segundos para que inicie..."
sleep 3

# Verificar que está corriendo
if systemctl is-active --quiet vmix-schedule-44; then
    echo "✅ Servicio corriendo correctamente"
else
    echo "⚠️  Servicio no está corriendo. Ver:"
    tail -20 $INSTALL_DIR/logs/api.log || echo "   (No hay logs aún)"
fi

echo ""
