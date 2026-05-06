#!/bin/bash
# Deploy vMix Schedule 44 a TrueNAS - Script Todo-en-Uno
# Ejecutar desde Shell de TrueNAS (http://192.168.192.44 > Sistema > Shell)

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🚀 Instalando vMix Schedule 44 en TrueNAS                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Crear directorio base
mkdir -p /opt/vmix-schedule-44/{data,logs}
cd /opt/vmix-schedule-44

echo "[1/6] Creando estructura de directorios..."
mkdir -p data logs frontend

# ============================================================================
# CREAR api.py
# ============================================================================
echo "[2/6] Creando API backend..."
cat > api.py << 'EOFAPI'
#!/usr/bin/env python3
import os, sys, json, threading, logging, time, requests, xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path

# Configuración de rutas
BASE_DIR = "/opt/vmix-schedule-44"
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_FILE = os.path.join(DATA_DIR, "vMix_Schedule_44_Contenidos_DB.json")
CONFIG_FILE = os.path.join(DATA_DIR, "vMix_Schedule_44_Contenidos_Config.json")
LOG_FILE = os.path.join(LOGS_DIR, "api.log")

# Crear directorios
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración vMix
VMIX_HOST = "192.168.192.140"
VMIX_PORT = 8098
VMIX_URL = f"http://{VMIX_HOST}:{VMIX_PORT}/api"

# Variables globales
_tanda_lock = threading.Lock()
_tanda_en_progreso = False
_auto_enabled = True
_monitor_running = True

# Configuración por defecto
DEFAULT_CONFIG = {
    "PUBLIS_POR_BLOQUE": 4,
    "INICIO_PUBLIS_INPUT": "14",
    "PUBLIS_LISTA_ID": "15",
    "CIERRE_PUBLIS_INPUT": "16",
    "FADE_DURATION_MS": 500,
    "PUBLIS_CLIP_TIMEOUT": 300,
    "INICIO_PUBLIS_TIMEOUT": 11,
    "CIERRE_PUBLIS_TIMEOUT": 5,
    "VMIX_HOST": VMIX_HOST,
    "VMIX_PORT": VMIX_PORT
}

app = Flask(__name__)
CORS(app)

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except:
        pass
    return DEFAULT_CONFIG

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE) as f:
                return json.load(f)
    except:
        pass
    return {"programas": {}, "tandas": {}}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

def call_vmix(func, **kwargs):
    try:
        params = {"Function": func, **kwargs}
        resp = requests.get(VMIX_URL, params=params, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Error calling vMix: {e}")
        return False

def get_vmix_status():
    try:
        resp = requests.get(f"http://{VMIX_HOST}:{VMIX_PORT}/api/", timeout=5)
        root = ET.fromstring(resp.content)
        return "Conectado"
    except:
        return "Desconectado"

def vmix_monitor():
    global _monitor_running
    while _monitor_running:
        try:
            time.sleep(1)
        except:
            pass

def system_tick():
    global _auto_enabled, _tanda_en_progreso, _tanda_lock
    while _monitor_running:
        try:
            if _auto_enabled:
                now = datetime.now()
                hms = now.strftime("%H:%M:%S")
                db = load_db()
                day = now.strftime("%A")
                
                # Ejecutar programas
                if day in db.get("programas", {}):
                    for evt in db["programas"][day]:
                        if evt.get("time") == hms:
                            input_id = evt.get("name")
                            call_vmix("SelectIndex", Input=input_id)
                            logger.info(f"Ejecutado evento: {input_id}")
                
                # Ejecutar tandas
                if day in db.get("tandas", {}):
                    for tanda in db["tandas"][day]:
                        if tanda.get("time") == hms and not _tanda_en_progreso:
                            with _tanda_lock:
                                _tanda_en_progreso = True
                                logger.info(f"Iniciando tanda: {tanda.get('list_id')}")
                            _tanda_en_progreso = False
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error en system_tick: {e}")

# RUTAS API
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "vmix": get_vmix_status(),
        "auto_enabled": _auto_enabled,
        "tanda_en_progreso": _tanda_en_progreso,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    save_config(request.json)
    return jsonify({"status": "ok"})

@app.route('/api/events', methods=['GET'])
def get_events():
    db = load_db()
    return jsonify(db)

@app.route('/api/events', methods=['POST'])
def add_event():
    db = load_db()
    data = request.json
    day = data.get("day")
    if day not in db["programas"]:
        db["programas"][day] = []
    db["programas"][day].append(data)
    save_db(db)
    return jsonify({"status": "ok"})

@app.route('/api/events/<day>/<int:idx>', methods=['DELETE'])
def delete_event(day, idx):
    db = load_db()
    if day in db["programas"] and 0 <= idx < len(db["programas"][day]):
        db["programas"][day].pop(idx)
        save_db(db)
    return jsonify({"status": "ok"})

@app.route('/api/vmix/fade', methods=['POST'])
def vmix_fade():
    call_vmix("Fade", Input="1", Duration="500")
    return jsonify({"status": "ok"})

@app.route('/api/auto/toggle', methods=['POST'])
def toggle_auto():
    global _auto_enabled
    _auto_enabled = request.json.get("enabled", True)
    logger.info(f"Automatización: {'ON' if _auto_enabled else 'OFF'}")
    return jsonify({"auto_enabled": _auto_enabled})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()[-50:]
        return jsonify({"logs": lines})
    except:
        return jsonify({"logs": []})

if __name__ == '__main__':
    # Iniciar threads
    threading.Thread(target=vmix_monitor, daemon=True).start()
    threading.Thread(target=system_tick, daemon=True).start()
    
    logger.info("🚀 vMix Schedule 44 API iniciada")
    app.run(host='127.0.0.1', port=5000, debug=False)
EOFAPI

# ============================================================================
# CREAR frontend/index.html
# ============================================================================
echo "[3/6] Creando interfaz web..."
cat > frontend/index.html << 'EOFHTML'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>vMix Schedule 44 - Control Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            color: #fff;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #00f2ff 0%, #0099cc 100%);
            color: #000;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 28px; }
        .status {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        .status-dot {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            background: #00f2ff;
        }
        .status-dot.offline { background: #ff0000; }
        main { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .card {
            background: #1a1a1a;
            border: 2px solid #00f2ff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 { color: #00f2ff; margin-bottom: 15px; }
        button {
            background: #00f2ff;
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        button:hover { background: #00ccff; transform: scale(1.05); }
        button.active { background: #00ff88; }
        input, select {
            background: #0a0a0a;
            border: 1px solid #00f2ff;
            color: #fff;
            padding: 8px;
            border-radius: 5px;
            margin-bottom: 10px;
            width: 100%;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #00f2ff;
        }
        th { background: #00f2ff; color: #000; }
        .logs { background: #000; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto; font-size: 12px; font-family: monospace; }
        .sidebar { display: flex; flex-direction: column; gap: 20px; }
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #1a1a1a; border: 1px solid #00f2ff; cursor: pointer; border-radius: 5px; color: #00f2ff; }
        .tab.active { background: #00f2ff; color: #000; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🎬 vMix Schedule 44</h1>
                <p>Control Panel - TrueNAS Server</p>
            </div>
            <div class="status">
                <div>
                    <div class="status-dot" id="statusDot"></div>
                    <span id="statusText">Conectando...</span>
                </div>
            </div>
        </header>

        <main>
            <div>
                <div class="card">
                    <h2>📺 Monitor</h2>
                    <p>Entrada: <strong id="currentInput">--</strong></p>
                    <p>Hora: <strong id="currentTime">--:--:--</strong></p>
                    <p>Estado: <span id="autoStatus">--</span></p>
                </div>

                <div class="tabs">
                    <div class="tab active" onclick="showTab('eventos')">Eventos</div>
                    <div class="tab" onclick="showTab('logs')">Logs</div>
                </div>

                <div id="eventos" class="tab-content active card">
                    <h2>📅 Eventos Programados</h2>
                    <input type="text" id="eventDay" placeholder="Día (ej: Monday)" />
                    <input type="time" id="eventTime" />
                    <input type="text" id="eventInput" placeholder="Input ID" />
                    <button onclick="addEvent()">Agregar Evento</button>
                    <table id="eventTable">
                        <thead><tr><th>Día</th><th>Hora</th><th>Input</th><th>Acción</th></tr></thead>
                        <tbody></tbody>
                    </table>
                </div>

                <div id="logs" class="tab-content card" style="display:none;">
                    <h2>📝 Logs del Sistema</h2>
                    <div class="logs" id="logsArea"></div>
                </div>
            </div>

            <div class="sidebar">
                <div class="card">
                    <h2>⚙️ Control</h2>
                    <button id="autoToggle" onclick="toggleAuto()">AUTO: OFF</button>
                    <p style="margin-top: 15px; font-size: 14px;">Estado: <span id="detailedStatus">Desconectado</span></p>
                </div>

                <div class="card">
                    <h2>🔧 Sistema</h2>
                    <p>Uptime: <span id="uptime">--</span></p>
                    <p>Versión: 1.0 TrueNAS</p>
                    <p>Backend: Flask 2.3.0</p>
                </div>
            </div>
        </main>
    </div>

    <script>
        const API_BASE = '/api';
        let autoEnabled = false;

        async function fetchStatus() {
            try {
                const res = await fetch(API_BASE + '/status');
                const data = await res.json();
                
                document.getElementById('statusDot').className = 
                    data.vmix === 'Conectado' ? 'status-dot' : 'status-dot offline';
                document.getElementById('statusText').textContent = data.vmix;
                document.getElementById('autoStatus').textContent = 
                    data.auto_enabled ? '✅ AUTO ON' : '❌ AUTO OFF';
                document.getElementById('detailedStatus').textContent = data.vmix;
                autoEnabled = data.auto_enabled;
                updateAutoButton();
            } catch (e) {
                console.error('Error fetching status:', e);
            }
        }

        function updateAutoButton() {
            const btn = document.getElementById('autoToggle');
            btn.textContent = autoEnabled ? 'AUTO: ON' : 'AUTO: OFF';
            btn.className = autoEnabled ? 'active' : '';
        }

        function toggleAuto() {
            fetch(API_BASE + '/auto/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: !autoEnabled })
            }).then(r => r.json()).then(d => {
                autoEnabled = d.auto_enabled;
                updateAutoButton();
                fetchStatus();
            });
        }

        async function addEvent() {
            const day = document.getElementById('eventDay').value;
            const time = document.getElementById('eventTime').value;
            const input = document.getElementById('eventInput').value;
            
            if (!day || !time || !input) {
                alert('Rellena todos los campos');
                return;
            }

            await fetch(API_BASE + '/events', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ day, time, name: input })
            });
            
            loadEvents();
        }

        async function loadEvents() {
            try {
                const res = await fetch(API_BASE + '/events');
                const data = await res.json();
                const tbody = document.querySelector('#eventTable tbody');
                tbody.innerHTML = '';
                
                for (const day in data.programas) {
                    data.programas[day].forEach((evt, idx) => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${day}</td>
                            <td>${evt.time}</td>
                            <td>${evt.name}</td>
                            <td><button onclick="deleteEvent('${day}', ${idx})">Eliminar</button></td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (e) {
                console.error('Error loading events:', e);
            }
        }

        async function deleteEvent(day, idx) {
            await fetch(API_BASE + `/events/${day}/${idx}`, { method: 'DELETE' });
            loadEvents();
        }

        async function fetchLogs() {
            try {
                const res = await fetch(API_BASE + '/logs');
                const data = await res.json();
                document.getElementById('logsArea').textContent = data.logs.join('');
            } catch (e) {
                console.error('Error fetching logs:', e);
            }
        }

        function updateTime() {
            const now = new Date();
            document.getElementById('currentTime').textContent = 
                now.toLocaleTimeString('es-ES');
        }

        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
            
            if (tab === 'logs') fetchLogs();
        }

        // Iniciar
        fetchStatus();
        loadEvents();
        setInterval(fetchStatus, 2000);
        setInterval(updateTime, 1000);
        updateTime();
    </script>
</body>
</html>
EOFHTML

# ============================================================================
# CREAR requirements.txt
# ============================================================================
echo "[4/6] Creando dependencias Python..."
cat > requirements.txt << 'EOFREQ'
flask>=2.3.0
requests>=2.31.0
flask-cors>=4.0.0
gunicorn>=20.1.0
EOFREQ

# ============================================================================
# CREAR nginx.conf
# ============================================================================
echo "[5/6] Configurando Nginx..."
cat > nginx.conf << 'EOFNGINX'
server {
    listen 80;
    server_name 192.168.192.44;

    location /ui/ {
        alias /opt/vmix-schedule-44/frontend/;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        return 301 /ui/;
    }

    access_log /var/log/nginx/vmix-schedule-44-access.log;
    error_log /var/log/nginx/vmix-schedule-44-error.log;
}
EOFNGINX

# Copiar a nginx
sudo cp nginx.conf /usr/local/etc/nginx/vmix-schedule-44.conf || echo "⚠️ Nginx config no copiada"

echo "[6/6] Instalando dependencias Python..."

# Instalar Python y dependencias
if command -v pkg &> /dev/null; then
    # FreeBSD (TrueNAS)
    sudo pkg install -y python39 py39-pip nginx
    python3.9 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
elif command -v apt &> /dev/null; then
    # Linux
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Crear archivos de datos iniciales
cat > data/vMix_Schedule_44_Contenidos_Config.json << 'EOFCONFIG'
{
  "PUBLIS_POR_BLOQUE": 4,
  "INICIO_PUBLIS_INPUT": "14",
  "PUBLIS_LISTA_ID": "15",
  "CIERRE_PUBLIS_INPUT": "16",
  "FADE_DURATION_MS": 500,
  "PUBLIS_CLIP_TIMEOUT": 300,
  "INICIO_PUBLIS_TIMEOUT": 11,
  "CIERRE_PUBLIS_TIMEOUT": 5,
  "VMIX_HOST": "192.168.192.140",
  "VMIX_PORT": 8098
}
EOFCONFIG

cat > data/vMix_Schedule_44_Contenidos_DB.json << 'EOFDB'
{
  "programas": {},
  "tandas": {}
}
EOFDB

chmod +x api.py

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ INSTALACIÓN COMPLETADA                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Ubicación: /opt/vmix-schedule-44"
echo "🌐 Acceso: http://192.168.192.44/ui/"
echo ""
echo "👉 Siguientes pasos:"
echo "   1. Instalar Nginx:"
echo "      sudo systemctl enable nginx"
echo "      sudo systemctl start nginx"
echo ""
echo "   2. Crear servicio systemd:"
echo "      sudo bash -c 'cat > /etc/systemd/system/vmix-schedule-44.service << EOFSVC"
echo "[Unit]"
echo "Description=vMix Schedule 44 API"
echo "After=network.target"
echo ""
echo "[Service]"
echo "Type=simple"
echo "User=root"
echo "WorkingDirectory=/opt/vmix-schedule-44"
echo "ExecStart=/opt/vmix-schedule-44/venv/bin/gunicorn -b 127.0.0.1:5000 api:app"
echo "Restart=always"
echo ""
echo "[Install]"
echo "WantedBy=multi-user.target"
echo "EOFSVC'"
echo ""
echo "   3. Iniciar servicio:"
echo "      sudo systemctl daemon-reload"
echo "      sudo systemctl enable vmix-schedule-44"
echo "      sudo systemctl start vmix-schedule-44"
echo ""
echo "   4. Verificar:"
echo "      sudo systemctl status vmix-schedule-44"
echo "      sudo systemctl status nginx"
echo ""
echo "   5. Abrir en navegador:"
echo "      http://192.168.192.44/ui/"
echo ""
