╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║         🚀 DEPLOY vMix Schedule 44 EN TRUENAS - GUÍA COMPLETA           ║
║                                                                          ║
║         http://192.168.192.44/ui/                                        ║
║         Usuario: truenas_admin | Contraseña: 44947                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝


📋 OPCIÓN 1: DEPLOY AUTOMÁTICO (RECOMENDADO - 1 COMANDO)
════════════════════════════════════════════════════════════════════════════

Ejecuta desde tu Mac (en la carpeta deploy/):

  bash deploy_to_truenas.sh truenas_admin 44947 192.168.192.44

¿Qué hace?
  ✅ Verifica archivos locales
  ✅ Se conecta a TrueNAS vía SSH
  ✅ Transfiere todos los archivos
  ✅ Ejecuta instalación automática
  ✅ Configura Nginx + Python + Flask
  ✅ Crea servicio systemd

Resultado: La app corre en http://192.168.192.44/ui/

Requisitos en Mac:
  • sshpass instalado: brew install sshpass


════════════════════════════════════════════════════════════════════════════
📋 OPCIÓN 2: DEPLOY MANUAL (PASO A PASO)
════════════════════════════════════════════════════════════════════════════

Si el deploy automático falla, hazlo manual:

PASO 1: Conectar a TrueNAS
─────────────────────────
Desde Mac o terminal:
  
  ssh truenas_admin@192.168.192.44
  (Password: 44947)


PASO 2: Crear directorio de destino
───────────────────────────────────
En TrueNAS (como root):

  sudo mkdir -p /opt/vmix-schedule-44
  sudo mkdir -p /opt/vmix-schedule-44/data
  sudo mkdir -p /opt/vmix-schedule-44/logs


PASO 3: Transferir archivos desde Mac
──────────────────────────────────────
En otra ventana terminal (en tu Mac):

  # Copiar archivos
  scp -r deploy/api.py truenas_admin@192.168.192.44:/tmp/
  scp -r deploy/requirements.txt truenas_admin@192.168.192.44:/tmp/
  scp -r deploy/frontend truenas_admin@192.168.192.44:/tmp/
  scp -r deploy/nginx.conf truenas_admin@192.168.192.44:/tmp/
  scp -r deploy/deploy.sh truenas_admin@192.168.192.44:/tmp/

  # O todo junto (más rápido):
  scp -r deploy/ truenas_admin@192.168.192.44:/tmp/


PASO 4: Mover archivos al destino
──────────────────────────────────
De vuelta en TrueNAS (SSH):

  sudo mv /tmp/deploy/api.py /opt/vmix-schedule-44/
  sudo mv /tmp/deploy/requirements.txt /opt/vmix-schedule-44/
  sudo mv /tmp/deploy/frontend/* /opt/vmix-schedule-44/frontend/
  sudo mv /tmp/deploy/nginx.conf /opt/vmix-schedule-44/


PASO 5: Ejecutar deploy.sh
──────────────────────────
En TrueNAS (como root):

  sudo bash /tmp/deploy/deploy.sh

O:
  
  cd /tmp/deploy
  sudo bash deploy.sh


PASO 6: Verificar instalación
─────────────────────────────
  sudo systemctl status vmix-schedule-44
  sudo systemctl status nginx


════════════════════════════════════════════════════════════════════════════
🎮 USAR LA APLICACIÓN
════════════════════════════════════════════════════════════════════════════

Una vez instalada:

1. INICIAR SERVICIOS (en TrueNAS):
   ─────────────────────────────
   sudo systemctl start vmix-schedule-44
   sudo systemctl start nginx

   Para autostart al reiniciar:
   sudo systemctl enable vmix-schedule-44
   sudo systemctl enable nginx


2. ACCEDER A LA WEB:
   ──────────────────
   Desde cualquier navegador:
   http://192.168.192.44/ui/

   O desde el servidor:
   http://localhost/ui/


3. MONITOR DE ESTADO:
   ──────────────────
   • Entrada actual de vMix
   • Estado de automatización (ON/OFF)
   • Próximos eventos
   • Conexión a vMix


4. AGREGAR EVENTOS:
   ────────────────
   • Click en tab "Eventos"
   • Seleccionar fecha y hora
   • Ingresar ID de input vMix
   • Click "Agregar Evento"

   Automáticamente ejecuta a esa hora


════════════════════════════════════════════════════════════════════════════
🔧 CONFIGURACIÓN
════════════════════════════════════════════════════════════════════════════

Archivo de configuración:
/opt/vmix-schedule-44/data/vMix_Schedule_44_Contenidos_Config.json

Ejemplo:
{
  "VMIX_IP": "192.168.192.140:8098",
  "INICIO_PUBLIS_INPUT": "14",
  "PUBLIS_LISTA_ID": "15",
  "CIERRE_PUBLIS_INPUT": "16",
  "PUBLIS_POR_BLOQUE": 4
}

Para cambiar:
  1. Edita el archivo JSON
  2. Reinicia servicio: sudo systemctl restart vmix-schedule-44


════════════════════════════════════════════════════════════════════════════
📝 LOGS Y DEBUGGING
════════════════════════════════════════════════════════════════════════════

Ver logs en tiempo real:

  # Logs de la API
  sudo tail -f /opt/vmix-schedule-44/logs/api.log

  # Logs de Nginx
  sudo tail -f /var/log/nginx/vmix-schedule-44-access.log
  sudo tail -f /var/log/nginx/vmix-schedule-44-error.log

  # Estado del servicio
  sudo systemctl status vmix-schedule-44
  sudo journalctl -u vmix-schedule-44 -f


════════════════════════════════════════════════════════════════════════════
🔄 RESTART Y ACTUALIZACIONES
════════════════════════════════════════════════════════════════════════════

Reiniciar servicio:
  sudo systemctl restart vmix-schedule-44

Detener:
  sudo systemctl stop vmix-schedule-44

Ver estado:
  sudo systemctl status vmix-schedule-44

Actualizar código (si cambias api.py):
  1. Reemplaza /opt/vmix-schedule-44/api.py
  2. sudo systemctl restart vmix-schedule-44


════════════════════════════════════════════════════════════════════════════
⚠️ TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════

❌ "Conexión rechazada en puerto 22"
   → Verifica que SSH esté habilitado en TrueNAS
   → Revisa firewall (puerto 22 debe estar abierto)

❌ "Python no encontrado"
   → El script instalará Python automáticamente
   → Si falla, instala manualmente: pkg install python39

❌ "Nginx no inicia"
   → Verifica sintaxis: sudo nginx -t
   → Ve los logs: sudo tail -f /var/log/nginx/error.log

❌ "API no responde"
   → Verifica: sudo systemctl status vmix-schedule-44
   → Ver logs: sudo tail -f /opt/vmix-schedule-44/logs/api.log
   → Verifica conectividad a vMix: ping 192.168.192.140

❌ "No se conecta a vMix"
   → Verifica IP de vMix en config.json
   → Asegúrate que vMix esté en puerto 8098
   → Verifica conectividad: ping 192.168.192.140


════════════════════════════════════════════════════════════════════════════
📊 ARQUITECTURA
════════════════════════════════════════════════════════════════════════════

          [Mac/Windows/Linux]
               Browser
                 ↓
          [TrueNAS Nginx]
          192.168.192.44:80
                 ↓
    ┌────────────────────────────┐
    │                            │
    ├─→ /ui/         → Frontend  │
    │                (index.html) │
    │                            │
    ├─→ /api/*       → Backend   │
    │                (Flask API) │
    │    ↓ HTTP                  │
    │    ↓ Port 5000             │
    │                            │
    └────────────────────────────┘
                 ↓
          [vMix HTTP API]
          192.168.192.140:8098
          (Automatización)


════════════════════════════════════════════════════════════════════════════
✅ CHECKLIST POST-DEPLOY
════════════════════════════════════════════════════════════════════════════

□ SSH conecta a TrueNAS
□ Archivos transferidos a /opt/vmix-schedule-44/
□ Python 3 instalado
□ Dependencias instaladas (Flask, requests, cors)
□ Nginx funciona (http://192.168.192.44)
□ API responde (http://192.168.192.44/api/status)
□ Frontend carga (http://192.168.192.44/ui/)
□ Se conecta a vMix (estado muestra "Conectado")
□ Autostart habilitado (systemctl enable)
□ Logs limpios sin errores


════════════════════════════════════════════════════════════════════════════
📞 SOPORTE
════════════════════════════════════════════════════════════════════════════

Si algo falla:

1. Verifica logs: sudo tail -f /opt/vmix-schedule-44/logs/api.log
2. Reinicia servicio: sudo systemctl restart vmix-schedule-44
3. Verifica conectividad: ping 192.168.192.140
4. Revisa config.json
5. Chequea permisos: ls -la /opt/vmix-schedule-44/


════════════════════════════════════════════════════════════════════════════

🎬 Powered by IGNACE
   vMix Schedule 44 - Versión 1.0 TrueNAS

════════════════════════════════════════════════════════════════════════════
