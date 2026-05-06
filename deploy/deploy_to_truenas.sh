#!/bin/bash
#
# Deploy automático para vMix Schedule 44 en TrueNAS
# Uso: bash deploy_to_truenas.sh <usuario> <password> <ip>
#

set -e

# Parámetros
TRUENAS_USER="${1:-truenas_admin}"
TRUENAS_PASS="${2:-44947}"
TRUENAS_IP="${3:-192.168.192.44}"
SSH_PORT="${4:-22}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 Deploy vMix Schedule 44 a TrueNAS                         ║"
echo "║                                                                ║"
echo "║  Usuario:  $TRUENAS_USER"
echo "║  IP:       $TRUENAS_IP:$SSH_PORT"
echo "║  Destino:  /opt/vmix-schedule-44"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que tenemos sshpass
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass no instalado"
    echo "   Instala con: brew install sshpass"
    exit 1
fi

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/5] Verificando archivos locales..."
[ -f "$DEPLOY_DIR/api.py" ] || { echo "❌ Falta api.py"; exit 1; }
[ -d "$DEPLOY_DIR/frontend" ] || { echo "❌ Falta directorio frontend"; exit 1; }
[ -f "$DEPLOY_DIR/requirements.txt" ] || { echo "❌ Falta requirements.txt"; exit 1; }
[ -f "$DEPLOY_DIR/nginx.conf" ] || { echo "❌ Falta nginx.conf"; exit 1; }
[ -f "$DEPLOY_DIR/deploy.sh" ] || { echo "❌ Falta deploy.sh"; exit 1; }
echo "✅ Todos los archivos locales están presentes"
echo ""

echo "[2/5] Verificando conexión a TrueNAS..."
sshpass -p "$TRUENAS_PASS" ssh -P "$SSH_PORT" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$TRUENAS_USER@$TRUENAS_IP" "echo '✅ Conexión OK'" || {
    echo "❌ No se puede conectar a $TRUENAS_IP:$SSH_PORT"
    echo "   Verifica credenciales o conectividad"
    exit 1
}
echo "✅ Conexión establecida"
echo ""

echo "[3/5] Transfiriendo archivos..."
sshpass -p "$TRUENAS_PASS" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no -r "$DEPLOY_DIR/api.py" "$TRUENAS_USER@$TRUENAS_IP:/root/deploy/" || echo "⚠️  Error transfiriendo api.py"
sshpass -p "$TRUENAS_PASS" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no -r "$DEPLOY_DIR/requirements.txt" "$TRUENAS_USER@$TRUENAS_IP:/root/deploy/" || echo "⚠️  Error transfiriendo requirements.txt"
sshpass -p "$TRUENAS_PASS" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no -r "$DEPLOY_DIR/nginx.conf" "$TRUENAS_USER@$TRUENAS_IP:/root/deploy/" || echo "⚠️  Error transfiriendo nginx.conf"
sshpass -p "$TRUENAS_PASS" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no -r "$DEPLOY_DIR/frontend" "$TRUENAS_USER@$TRUENAS_IP:/root/deploy/" || echo "⚠️  Error transfiriendo frontend"
echo "✅ Archivos transferidos a /root/deploy/"
echo ""

echo "[4/5] Preparando script de deploy..."
sshpass -p "$TRUENAS_PASS" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no "$DEPLOY_DIR/deploy.sh" "$TRUENAS_USER@$TRUENAS_IP:/root/" || {
    echo "❌ Error transfiriendo deploy.sh"
    exit 1
}
sshpass -p "$TRUENAS_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$TRUENAS_USER@$TRUENAS_IP" "chmod +x /root/deploy.sh"
echo "✅ Script de deploy preparado"
echo ""

echo "[5/5] Ejecutando deploy en TrueNAS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sshpass -p "$TRUENAS_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$TRUENAS_USER@$TRUENAS_IP" "bash /root/deploy.sh"
DEPLOY_RESULT=$?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $DEPLOY_RESULT -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                 ✅ DEPLOY COMPLETADO EXITOSAMENTE             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 ACCESO:"
    echo "   URL: http://$TRUENAS_IP/ui/"
    echo ""
    echo "🔧 PRÓXIMOS PASOS EN TRUENAS:"
    echo "   1. SSH: sshpass -p '$TRUENAS_PASS' ssh $TRUENAS_USER@$TRUENAS_IP"
    echo "   2. Inicia servicio: systemctl start vmix-schedule-44"
    echo "   3. Verifica estado: systemctl status vmix-schedule-44"
    echo "   4. Inicia nginx: systemctl start nginx"
    echo "   5. Abre: http://$TRUENAS_IP/ui/"
    echo ""
    echo "📝 LOGS:"
    echo "   tail -f /opt/vmix-schedule-44/logs/api.log"
    echo ""
else
    echo "❌ Deploy falló"
    exit 1
fi
