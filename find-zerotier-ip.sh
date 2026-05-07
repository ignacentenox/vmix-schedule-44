#!/bin/bash
# Script para encontrar IP de ZeroTier en TrueNAS
# Ejecutar: bash find-zerotier-ip.sh

echo "🔍 Buscando IP de ZeroTier en esta máquina..."
echo ""

# Buscar interfaces ZeroTier
if command -v zerotier-cli >/dev/null 2>&1; then
    echo "📡 ZeroTier CLI encontrado:"
    zerotier-cli info
    echo ""
    echo "🌐 Miembros de la red ZeroTier:"
    zerotier-cli listmembers | grep -v "^MEMBER" || echo "   (sin membresías activas)"
else
    echo "⚠️  zerotier-cli no encontrado"
fi

echo ""
echo "📋 Interfaces de red:"
if command -v ip >/dev/null 2>&1; then
    # Linux
    ip addr show | grep -E "^[0-9]+:|inet " | grep -A1 zt
else
    # FreeBSD/macOS
    ifconfig | grep -A4 zt || ifconfig | grep -A4 zerotier || true
fi

echo ""
echo "💡 Tip: Si no ves ZeroTier, verifica:"
echo "   - ZeroTier está instalado"
echo "   - Servicio está corriendo (systemctl status zerotier-one)"
echo "   - Estás unido a la red correcta"
