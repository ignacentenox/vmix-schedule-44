#!/bin/bash
# Diagnóstico de conexión a vMix desde TrueNAS

VMIX_URL="http://192.168.192.140:8098/"
VMIX_HOST="192.168.192.140"
VMIX_PORT="8098"

echo "🔍 Diagnóstico de conectividad a vMix"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: DNS/IP
echo "1️⃣  Resolviendo DNS: $VMIX_HOST"
if ping -c 1 -W 2 "$VMIX_HOST" >/dev/null 2>&1; then
    echo "   ✓ IP accesible (ping respondió)"
else
    echo "   ✗ IP NO accesible (ping sin respuesta)"
    echo "   ⚠️  Verifica firewall o que esté en la misma VPN/red"
fi
echo ""

# Test 2: Puerto abierto
echo "2️⃣  Probando puerto TCP $VMIX_PORT"
if command -v nc >/dev/null 2>&1; then
    if nc -z -w 2 "$VMIX_HOST" "$VMIX_PORT" 2>/dev/null; then
        echo "   ✓ Puerto $VMIX_PORT abierto"
    else
        echo "   ✗ Puerto $VMIX_PORT NO responde"
    fi
elif command -v timeout >/dev/null 2>&1; then
    timeout 2 bash -c "cat < /dev/null > /dev/tcp/$VMIX_HOST/$VMIX_PORT" 2>/dev/null && \
        echo "   ✓ Puerto $VMIX_PORT abierto" || \
        echo "   ✗ Puerto $VMIX_PORT NO responde"
else
    echo "   ⚠️  nc/timeout no disponible, saltando test"
fi
echo ""

# Test 3: HTTP GET
echo "3️⃣  GET a URL raíz: $VMIX_URL"
if command -v curl >/dev/null 2>&1; then
    RESPONSE=$(curl -s -w "\n%{http_code}" -m 3 "$VMIX_URL" 2>&1 | tail -1)
    if [ "$RESPONSE" = "200" ]; then
        echo "   ✓ HTTP 200 - Servidor responde"
    else
        echo "   ⚠️  HTTP $RESPONSE"
    fi
    
    # Mostrar respuesta (primeras 200 chars)
    BODY=$(curl -s -m 3 "$VMIX_URL" 2>&1 | head -c 200)
    if [ ! -z "$BODY" ]; then
        echo "   Respuesta: ${BODY:0:100}..."
    fi
else
    echo "   ⚠️  curl no disponible"
fi
echo ""

# Test 4: GetStatus
echo "4️⃣  GET con Function=GetStatus"
if command -v curl >/dev/null 2>&1; then
    RESPONSE=$(curl -s -m 3 "${VMIX_URL}?Function=GetStatus" 2>&1)
    if echo "$RESPONSE" | grep -q "xml\|XML\|version"; then
        echo "   ✓ Respuesta XML válida"
        echo "   Primeras líneas:"
        echo "$RESPONSE" | head -3 | sed 's/^/     /'
    else
        echo "   Respuesta:"
        echo "$RESPONSE" | head -c 150 | sed 's/^/     /'
    fi
else
    echo "   ⚠️  curl no disponible"
fi
echo ""

# Test 5: Logs de la API
echo "5️⃣  Últimos errores en logs de la API:"
LOGFILE="/mnt/vmix-schedule-44/logs/api.log"
if [ -f "$LOGFILE" ]; then
    echo "   Últimas 5 líneas:"
    tail -5 "$LOGFILE" | sed 's/^/     /'
else
    echo "   ⚠️  Archivo de log no encontrado: $LOGFILE"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Si todo está ✓ pero sigue sin conectar:"
echo "  - Verifica que vMix esté corriendo en Windows"
echo "  - Confirma IP de VPN (ejecuta en Windows: ipconfig)"
echo "  - Reinicia servicio: systemctl restart vmix-schedule-44"
echo "  - Ver logs: tail -f /mnt/vmix-schedule-44/logs/api.log"
