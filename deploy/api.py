#!/usr/bin/env python3
"""
vMix Schedule 44 - API REST Backend
Compatible con http://192.168.192.44/ui/
Ejecuta automatización vMix sin GUI
"""

import sys
import json
import os
import requests
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# --- CONFIGURACIÓN ---
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data", "vMix_Schedule_44_Contenidos_DB.json")
CONFIG_FILE = os.path.join(BASE_DIR, "data", "vMix_Schedule_44_Contenidos_Config.json")
LOG_FILE = os.path.join(BASE_DIR, "logs", "api.log")

# Crear directorios si no existen
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

VMIX_URL = 'http://192.168.192.140:8098/api/'

# Variables de estado
_tanda_en_progreso = False
_auto_enabled = True
_tanda_lock = threading.Lock()
_vmix_status = {
    'entrada_activa': None,
    'conectado': False,
    'ultima_actualizacion': None
}

# --- LOGGING ---
def log(msg):
    """Registra mensajes."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except:
        pass

# --- FUNCIONES vMIX ---
def call_vmix(func, retries=2, backoff=1.5, **kwargs):
    """Llama API vMix con reintentos."""
    query = {'Function': func}
    query.update(kwargs)
    attempt = 0
    delay = 1.0
    while attempt <= retries:
        try:
            r = requests.get(VMIX_URL, params=query, timeout=3)
            if 200 <= r.status_code < 500:
                return {'status': r.status_code, 'ok': True}
            log(f"[vMix] {func} -> {r.status_code}")
        except Exception as e:
            log(f"[vMix] Error en {func}: {e}")
        attempt += 1
        time.sleep(delay)
        delay *= backoff
    return {'status': 500, 'ok': False, 'error': 'timeout'}

def obtener_estado_vmix():
    """Obtiene estado actual de vMix."""
    try:
        r = requests.get(VMIX_URL, timeout=3)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            entrada = root.findtext('active')
            _vmix_status['entrada_activa'] = entrada
            _vmix_status['conectado'] = True
            _vmix_status['ultima_actualizacion'] = datetime.now().isoformat()
            return entrada
    except Exception as e:
        log(f"[vMix] Error obteniendo estado: {e}")
        _vmix_status['conectado'] = False
    return None

# --- GESTIÓN DE DATOS ---
def load_config():
    """Carga configuración."""
    default = {
        "VMIX_IP": "192.168.192.140:8098",
        "INICIO_PUBLIS_INPUT": "14",
        "PUBLIS_LISTA_ID": "15",
        "CIERRE_PUBLIS_INPUT": "16",
        "PUBLIS_POR_BLOQUE": 4,
        "FADE_DURATION_MS": 500
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return {**default, **json.load(f)}
        except:
            return default
    return default

def save_config(config):
    """Guarda configuración."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_db():
    """Carga base de datos de eventos."""
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    empty = {"programas": {d: [] for d in dias}, "tandas": {d: [] for d in dias}}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return empty
    return empty

def save_db(db):
    """Guarda base de datos de eventos."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

# --- THREAD DE MONITOREO ---
def vmix_monitor():
    """Monitor de vMix en background."""
    while True:
        try:
            obtener_estado_vmix()
        except:
            pass
        time.sleep(1)

# --- API ENDPOINTS ---
@app.route('/', methods=['GET'])
def index():
    """Sirve el frontend."""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend'), 'index.html')

@app.route('/api/status', methods=['GET'])
def api_status():
    """Estado actual del sistema."""
    obtener_estado_vmix()
    config = load_config()
    db = load_db()
    
    # Contar próximos eventos
    ahora = datetime.now()
    dia_hoy = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][ahora.weekday()]
    
    total_progs = sum(len(db['programas'].get(d, [])) for d in db['programas'])
    total_tandas = sum(len(db['tandas'].get(d, [])) for d in db['tandas'])
    
    return jsonify({
        'vmix': _vmix_status,
        'auto_enabled': _auto_enabled,
        'tanda_en_progreso': _tanda_en_progreso,
        'total_programas': total_progs,
        'total_tandas': total_tandas,
        'dia_hoy': dia_hoy,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Obtiene configuración."""
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def api_set_config():
    """Guarda configuración."""
    try:
        config = request.json
        save_config(config)
        log(f"[API] Configuración guardada")
        return jsonify({'ok': True, 'message': 'Configuración guardada'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/events', methods=['GET'])
def api_get_events():
    """Obtiene todos los eventos."""
    db = load_db()
    return jsonify(db)

@app.route('/api/events', methods=['POST'])
def api_add_event():
    """Agrega un evento."""
    try:
        data = request.json
        dia = data.get('dia')
        tipo = data.get('tipo')  # 'programa' o 'tanda'
        evento = data.get('evento')
        
        db = load_db()
        if tipo == 'programa':
            db['programas'][dia].append(evento)
            db['programas'][dia].sort(key=lambda x: x['time'])
        elif tipo == 'tanda':
            db['tandas'][dia].append(evento)
            db['tandas'][dia].sort(key=lambda x: x['time'])
        
        save_db(db)
        log(f"[API] Evento agregado en {dia}")
        return jsonify({'ok': True, 'message': 'Evento agregado'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/events/<dia>/<int:idx>', methods=['DELETE'])
def api_delete_event(dia, idx):
    """Elimina un evento."""
    try:
        data = request.json
        tipo = data.get('tipo')
        
        db = load_db()
        if tipo == 'programa':
            db['programas'][dia].pop(idx)
        elif tipo == 'tanda':
            db['tandas'][dia].pop(idx)
        
        save_db(db)
        log(f"[API] Evento eliminado de {dia}")
        return jsonify({'ok': True, 'message': 'Evento eliminado'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/vmix/fade', methods=['POST'])
def api_vmix_fade():
    """Ejecuta Fade en vMix."""
    try:
        data = request.json
        input_id = data.get('input')
        duration = data.get('duration', 500)
        result = call_vmix('Fade', Input=input_id, Duration=str(duration))
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/vmix/cut', methods=['POST'])
def api_vmix_cut():
    """Ejecuta Cut en vMix."""
    try:
        data = request.json
        input_id = data.get('input')
        result = call_vmix('Cut', Input=input_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@app.route('/api/auto/toggle', methods=['POST'])
def api_toggle_auto():
    """Activa/desactiva automatización."""
    global _auto_enabled
    _auto_enabled = not _auto_enabled
    log(f"[API] AUTO: {'ON' if _auto_enabled else 'OFF'}")
    return jsonify({'ok': True, 'auto_enabled': _auto_enabled})

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    """Obtiene últimos logs."""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()[-50:]  # Últimas 50 líneas
                return jsonify({'logs': lines})
    except:
        pass
    return jsonify({'logs': []})

# --- SCHEDULER EN BACKGROUND ---
def system_tick():
    """Ejecuta eventos programados cada segundo."""
    last_fired = ""
    while True:
        if _auto_enabled:
            ahora = datetime.now()
            t_str = ahora.strftime("%H:%M:%S")
            dia_hoy = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][ahora.weekday()]
            
            if last_fired != t_str:
                db = load_db()
                config = load_config()
                
                # Ejecutar programas
                for ev in db['programas'].get(dia_hoy, []):
                    if ev['time'] == t_str:
                        log(f"[SCHEDULER] Ejecutando programa a {t_str}: {ev['name']}")
                        call_vmix('Fade', Input=ev['name'], Duration='500')
                
                # Ejecutar tandas
                for ev in db['tandas'].get(dia_hoy, []):
                    if ev['time'] == t_str:
                        log(f"[SCHEDULER] Ejecutando tanda a {t_str}")
                
                last_fired = t_str
        
        time.sleep(1)

if __name__ == '__main__':
    # Iniciar monitors en background
    threading.Thread(target=vmix_monitor, daemon=True).start()
    threading.Thread(target=system_tick, daemon=True).start()
    
    log("[API] vMix Schedule 44 Backend iniciado")
    log("[API] Escuchando en puerto 5000")
    
    # Ejecutar servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=False)
