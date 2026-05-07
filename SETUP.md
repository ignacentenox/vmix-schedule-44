# vMix Schedule 44 - Setup Guide

## 🚀 Instalación en TrueNAS SCALE

### Opción 1: Instalación automática
```bash
curl -sSL https://raw.githubusercontent.com/ignacentenox/vmix-schedule-44/main/install.sh | sudo bash
```

El script automáticamente:
- Crea directorio `/mnt/vmix-schedule-44`
- Instala dependencias Python necesarias
- Configura servicio systemd para auto-inicio
- Inicia Flask en `http://192.168.192.44:8080`

### Opción 2: Instalación manual
```bash
# 1. Clonar repo
sudo git clone https://github.com/ignacentenox/vmix-schedule-44.git /mnt/vmix-schedule-44

# 2. Bootstrap pip (TrueNAS SCALE bloquea apt/pkg)
cd /mnt/vmix-schedule-44/deploy
python3.11 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')"
python3.11 /tmp/get-pip.py --target=./lib

# 3. Instalar dependencias
PYTHONPATH=./lib python3.11 -m pip install --target=./lib flask flask-cors gunicorn requests

# 4. Crear servicio systemd
sudo tee /etc/systemd/system/vmix-schedule-44.service > /dev/null <<EOF
[Unit]
Description=vMix Schedule 44 REST API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/mnt/vmix-schedule-44/deploy
Environment=PYTHONPATH=/mnt/vmix-schedule-44/deploy/lib
ExecStart=/usr/bin/python3.11 -m gunicorn -b 0.0.0.0:8080 api:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 5. Iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable vmix-schedule-44
sudo systemctl restart vmix-schedule-44
```

---

## ⚙️ Configuración de vMix

### 1. Acceder a la interfaz web
Abre en el navegador: **http://192.168.192.44:8080**

### 2. Configurar URL de vMix

1. **Campo "📡 VMIX URL"** - Ingresa la dirección de tu servidor vMix:
   - ✅ Correcto: `http://192.168.192.140:8098/`
   - ❌ Incorrecto: `http://192.168.192.140:8098/api/` (sin /api/)
   - Donde `192.168.192.140` es la IP de tu servidor vMix
   - Puerto típico: `8098` (vMix API HTTP)

2. **Encontrar IP correcta de vMix:**
   - Abre vMix en Windows/Linux
   - Menu → `Tools` → `Web Controller`
   - Verás algo como: `http://localhost:8098` o `http://192.168.x.x:8098`
   - Copia esa dirección (sin `/api/`)

3. **Presiona APLICAR** - Se guardará automáticamente

### 3. Verificar conectividad
- Presiona el botón **🔧 TEST** en configuración
- Si dice "✅ Conectado" → ¡Listo!
- Si dice "❌ No conecta" → Revisa logs o ejecuta diagnóstico

---

## 📋 Configuración adicional

Puedes editar en el panel:
- **SPOTS** - Cantidad de publicidades por bloque (default: 4)
- **JINGLE IN** - Input ID para jingle de inicio (default: 14)
- **JINGLE OUT** - Input ID para jingle de cierre (default: 16)

Luego presiona **APLICAR** para guardar.

---

## 🔍 Monitoreo

### Ver logs en tiempo real
```bash
sudo journalctl -u vmix-schedule-44 -f
```

### Verificar que servicio esté corriendo
```bash
sudo systemctl status vmix-schedule-44
sudo ss -tlnp | grep 8080
```

### Probar endpoint API
```bash
curl http://192.168.192.44:8080/api/status
```

---

## 🛠️ Troubleshooting

### Diagnóstico automático completo
```bash
# Ejecutar script en TrueNAS (SSH)
bash /mnt/vmix-schedule-44/test-vmix-connection.sh
```

### vMix no conecta
1. Verifica que vMix esté ejecutándose en Windows/Linux
2. Confirma la URL correcta (sin `/api/`):
   ```bash
   curl http://192.168.192.140:8098/?Function=GetStatus
   ```
3. Si eso devuelve XML → IP/puerto correctos, verifica firewall/VPN
4. Si dice "No suitable Function" → URL tiene `/api/`, quítalo

### Cambiar URL de vMix
- Simplemente ingresa la nueva URL en el campo "📡 VMIX URL"
- Presiona APLICAR
- No necesita reiniciar nada

### Puerto 8080 no responde
```bash
# Verificar si el servicio está activo
sudo systemctl restart vmix-schedule-44
sudo systemctl status vmix-schedule-44

# Ver logs en tiempo real
sudo journalctl -u vmix-schedule-44 -f
```

---

## 📊 Base de datos de programación

La base de datos se importa automáticamente desde `vMix_Schedule_44_Contenidos_DB.json` en el directorio raíz.

Ver programas en: **http://192.168.192.44:8080** → Tab **PROGRAMAS**

---

## 🚀 APIs disponibles

- `GET /api/status` - Estado general del sistema
- `GET /api/config` - Obtener configuración actual
- `POST /api/config` - Guardar configuración
- `GET /api/vmix/test` - Probar conectividad a vMix
- `GET /api/events/<tipo>/<dia>` - Obtener eventos del día
- `GET /api/logs` - Ver últimos logs

---

**Creado con 💙 por IGNACE**
