#!/bin/sh
# vMix Schedule 44 - Instalador para TrueNAS / Linux
# Ejecutar: curl -fsSL https://raw.githubusercontent.com/ignacentenox/vmix-schedule-44/main/install.sh | sudo sh

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🚀 vMix Schedule 44 - Installer                             ║"
echo "║     TrueNAS / FreeBSD / Linux                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ─── Verificar root ────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Ejecutar con sudo:"
    echo "   curl -fsSL https://raw.githubusercontent.com/ignacentenox/vmix-schedule-44/main/install.sh | sudo sh"
    exit 1
fi

# ─── [1/6] Directorio de instalación ──────────────────────────────
echo "[1/6] Buscando directorio escribible..."
INSTALL_DIR=""
for dir in /mnt/vmix-schedule-44 /var/lib/vmix-schedule-44 /root/vmix-schedule-44; do
    if mkdir -p "$dir" 2>/dev/null && touch "$dir/.ok" 2>/dev/null; then
        rm -f "$dir/.ok"
        INSTALL_DIR="$dir"
        break
    fi
done
if [ -z "$INSTALL_DIR" ]; then
    echo "❌ No se encontró directorio escribible"
    exit 1
fi
mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs"
echo "   ✅ Usando: $INSTALL_DIR"

# ─── [2/6] Descargar código ────────────────────────────────────────
echo ""
echo "[2/6] Descargando desde GitHub..."
cd "$INSTALL_DIR"

if [ -f "$INSTALL_DIR/deploy/api.py" ]; then
    echo "   ✅ Código ya descargado, saltando..."
else
    # Intentar git clone
    git clone --depth 1 https://github.com/ignacentenox/vmix-schedule-44.git . 2>/dev/null && echo "   ✅ Clonado con git" || {
        echo "   Intentando wget..."
        wget -q -O /tmp/vmix.tar.gz "https://github.com/ignacentenox/vmix-schedule-44/archive/refs/heads/main.tar.gz" || {
            echo "❌ No se pudo descargar. Verifica internet."
            exit 1
        }
        tar -xzf /tmp/vmix.tar.gz -C /tmp/
        cp -r /tmp/vmix-schedule-44-main/. "$INSTALL_DIR/"
        rm -rf /tmp/vmix.tar.gz /tmp/vmix-schedule-44-main
        echo "   ✅ Descargado con wget"
    }
fi

# ─── [3/6] Detectar Python ────────────────────────────────────────
echo ""
echo "[3/6] Detectando Python..."
PY_CMD=""
for py in python3.11 python3.10 python3.9 python3; do
    if command -v "$py" >/dev/null 2>&1; then
        PY_CMD="$py"
        echo "   ✅ Encontrado: $PY_CMD ($($py --version 2>&1))"
        break
    fi
done
if [ -z "$PY_CMD" ]; then
    echo "❌ Python3 no encontrado."
    echo "   En TrueNAS: Apps → instalar o pkg install python39"
    exit 1
fi

# ─── [4/6] Instalar dependencias ─────────────────────────────────
echo ""
echo "[4/6] Instalando dependencias Python..."

PKGS="flask requests flask-cors gunicorn"
LIB_DIR="$INSTALL_DIR/lib"
mkdir -p "$LIB_DIR"

# Verificar si pip module está disponible
if ! $PY_CMD -m pip --version >/dev/null 2>&1; then
    echo "   pip module no encontrado, descargando get-pip.py..."
    wget -q -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py 2>/dev/null || \
    curl -fsSL -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py || {
        echo "❌ No se pudo descargar get-pip.py"
        exit 1
    }
    $PY_CMD /tmp/get-pip.py --target="$LIB_DIR" 2>&1 | tail -2
    rm -f /tmp/get-pip.py
fi

# Instalar dependencias con --target (no necesita permisos del sistema)
# Usar PYTHONPATH para que pip recién instalado sea encontrado
echo "   Instalando en: $LIB_DIR"
PYTHONPATH="$LIB_DIR" $PY_CMD -m pip install --target="$LIB_DIR" --quiet $PKGS 2>&1 | grep -E "(Successfully|already|error|ERROR)" || true

# Verificar que flask quedó instalado
if PYTHONPATH="$LIB_DIR" $PY_CMD -c "import flask" 2>/dev/null; then
    echo "   ✅ Dependencias instaladas correctamente"
else
    echo "❌ Error instalando dependencias. Salida completa:"
    PYTHONPATH="$LIB_DIR" $PY_CMD -m pip install --target="$LIB_DIR" $PKGS
    exit 1
fi
if [ -z "$GUNICORN_CMD" ]; then
    GUNICORN_CMD="$PY_CMD -m gunicorn"
fi
echo "   gunicorn: $GUNICORN_CMD"

# ─── [5/6] Configurar Nginx ───────────────────────────────────────
echo ""
echo "[5/6] Configurando Nginx..."

# Buscar nginx config dir
NGINX_CONF_DIR=""
for d in /etc/nginx/conf.d /usr/local/etc/nginx/conf.d /etc/nginx/sites-available; do
    if [ -d "$d" ]; then
        NGINX_CONF_DIR="$d"
        break
    fi
done

if [ -n "$NGINX_CONF_DIR" ]; then
    SRC=""
    [ -f "$INSTALL_DIR/deploy/nginx.conf" ] && SRC="$INSTALL_DIR/deploy/nginx.conf"
    [ -f "$INSTALL_DIR/nginx.conf" ] && SRC="$INSTALL_DIR/nginx.conf"
    if [ -n "$SRC" ]; then
        cp "$SRC" "$NGINX_CONF_DIR/vmix-schedule-44.conf"
        [ -d /etc/nginx/sites-enabled ] && ln -sf "$NGINX_CONF_DIR/vmix-schedule-44.conf" /etc/nginx/sites-enabled/vmix-schedule-44.conf 2>/dev/null || true
        echo "   ✅ Nginx configurado en $NGINX_CONF_DIR"
    fi
else
    echo "   ⚠️  Nginx no encontrado, saltando configuración"
fi

# ─── [6/6] Servicio systemd ───────────────────────────────────────
echo ""
echo "[6/6] Creando servicio systemd..."

API_FILE=""
[ -f "$INSTALL_DIR/deploy/api.py" ] && API_FILE="$INSTALL_DIR/deploy/api.py"
[ -f "$INSTALL_DIR/api.py" ] && API_FILE="$INSTALL_DIR/api.py"

if [ -n "$API_FILE" ]; then
    API_DIR="$(dirname $API_FILE)"
    API_MOD="api"

    cat > /etc/systemd/system/vmix-schedule-44.service << EOF
[Unit]
Description=vMix Schedule 44 - Web API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$API_DIR
Environment=PYTHONPATH=$LIB_DIR
ExecStart=$PY_CMD -m gunicorn -b 127.0.0.1:5000 $API_MOD:app
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/api.log
StandardError=append:$INSTALL_DIR/logs/api.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable vmix-schedule-44 2>/dev/null || true
    systemctl start vmix-schedule-44 && echo "   ✅ Servicio iniciado" || {
        echo "   ⚠️  No se pudo iniciar. Ver logs:"
        echo "      tail -f $INSTALL_DIR/logs/api.log"
    }
else
    echo "   ⚠️  api.py no encontrado, servicio no creado"
fi

# Nginx
nginx -t 2>/dev/null && (systemctl restart nginx 2>/dev/null || true) && echo "   ✅ Nginx reiniciado" || true

# ─── RESULTADO ────────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Web:     http://192.168.192.44/ui/"
echo "📍 Dir:     $INSTALL_DIR"
echo "📊 Logs:    tail -f $INSTALL_DIR/logs/api.log"
echo ""
echo "Estado:  systemctl status vmix-schedule-44"
echo "Reiniciar: systemctl restart vmix-schedule-44"
echo ""

sleep 2
systemctl is-active --quiet vmix-schedule-44 \
    && echo "✅ Servicio corriendo OK" \
    || echo "⚠️  Servicio no activo. Ver: tail -f $INSTALL_DIR/logs/api.log"
