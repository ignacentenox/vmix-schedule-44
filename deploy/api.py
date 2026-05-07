#!/usr/bin/env python3
"""
vMix Schedule 44 - API REST Backend (migración de main.py)
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
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

DB_FILE = os.path.join(DATA_DIR, "vMix_Schedule_44_Contenidos_DB.json")
CONFIG_FILE = os.path.join(DATA_DIR, "vMix_Schedule_44_Contenidos_Config.json")
LOG_FILE = os.path.join(LOGS_DIR, "api.log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Archivo para guardar URL de vMix
VMIX_CONFIG_FILE = os.path.join(DATA_DIR, "vmix_url.txt")

# Cargar URL de vMix desde archivo o usar default
def get_vmix_url():
    if os.path.exists(VMIX_CONFIG_FILE):
        try:
            with open(VMIX_CONFIG_FILE, 'r') as f:
                url = f.read().strip()
                if url:
                    return url
        except:
            pass
    return 'http://192.168.192.140:8098/api/'

VMIX_URL = get_vmix_url()

# Variables globales
_tanda_lock = threading.Lock()
_tanda_en_progreso = False
_tanda_entrada_anterior = None
_tanda_entrada_actual = None
_tanda_tiempo_inicio = None
_tanda_lista_id = None
_tanda_total_spots = None
_mostrar_estado_vivo = True
auto_enabled = True
last_fired = ""
vmix_status = {'entrada_activa': None, 'conectado': False, 'ultima_actualizacion': None}
next_programa = None
next_tanda = None

# --- LOGGING ---
def log(msg):
    """Registra mensajes en archivo y consola."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except Exception:
        pass

# --- VMIX API HELPERS ---
def call_vmix(func, retries=2, backoff=1.5, **kwargs):
    """Llama API vMix con reintentos exponenciales."""
    query = {'Function': func}
    query.update(kwargs)
    attempt = 0
    delay = 1.0
    while attempt <= retries:
        try:
            r = requests.get(VMIX_URL, params=query, timeout=3)
            if 200 <= r.status_code < 500:
                return r
            if 'No suitable Function' in r.text:
                return None
        except Exception as e:
            pass
        attempt += 1
        time.sleep(delay)
        delay *= backoff
    return None

def esperar_fin_reproduccion(input_num, timeout=600):
    """Espera que una entrada termine de reproducirse."""
    start = time.time()
    duracion_video = None
    timeout_dinamico = timeout
    
    while time.time() - start < timeout_dinamico:
        try:
            r = requests.get(VMIX_URL, timeout=3)
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                for inp in root.findall('.//input'):
                    if inp.get('number') == str(input_num):
                        state = inp.get('state', '')
                        try:
                            pos = float(inp.findtext('position') or -1)
                            dur = float(inp.findtext('duration') or 0)
                            
                            if duracion_video is None and dur > 0:
                                duracion_video = dur
                                timeout_dinamico = dur + 2.0
                            
                            if state == 'Completed':
                                return True
                            
                            if dur > 0 and pos >= (dur * 0.95):
                                return True
                        except (ValueError, TypeError):
                            pass
                        break
            time.sleep(0.5)
        except Exception:
            time.sleep(1)
    
    return False

def obtener_estado_completo():
    """Captura estado completo de vMix."""
    estado = {'entrada': None, 'posicion': None, 'duracion': None}
    
    for intento in range(3):
        try:
            r = requests.get(VMIX_URL, timeout=3)
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                entrada_activa = root.findtext('active')
                
                if entrada_activa and entrada_activa != 'None':
                    estado['entrada'] = entrada_activa
                    
                    for inp in root.findall('.//input'):
                        if inp.get('number') == str(entrada_activa):
                            estado['posicion'] = inp.findtext('position')
                            estado['duracion'] = inp.findtext('duration')
                            break
                    return estado
        except Exception:
            pass
        
        if intento < 2:
            time.sleep(0.5)
    
    return estado

def restaurar_estado(estado_previo):
    """Restaura entrada anterior después de tanda."""
    if not estado_previo or not estado_previo.get('entrada'):
        return
    
    entrada = estado_previo['entrada']
    if not entrada or entrada == 'None':
        return
    
    log(f"[TANDA] Fade 500ms → Entrada {entrada}")
    call_vmix('Fade', Input=entrada, Duration='500')
    time.sleep(1)

def get_lista_item_count(list_input):
    """Obtiene número de items en una lista de vMix."""
    try:
        r = requests.get(VMIX_URL + 'state', timeout=3)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for inp in root.findall('.//input'):
                if inp.get('number') == str(list_input):
                    items = inp.findall('list/item')
                    return max(1, len(items))
    except Exception:
        pass
    return 1

# --- CONFIG HELPERS ---
def load_config():
    """Carga configuración."""
    default = {
        "PUBLIS_POR_BLOQUE": 4,
        "INICIO_PUBLIS_INPUT": "14",
        "PUBLIS_LISTA_ID": "15",
        "CIERRE_PUBLIS_INPUT": "16",
        "FADE_DURATION_MS": 500,
        "PUBLIS_CLIP_TIMEOUT": 300,
        "INICIO_PUBLIS_TIMEOUT": 11,
        "CIERRE_PUBLIS_TIMEOUT": 5
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = json.load(f)
                return {**default, **loaded}
        except:
            return default
    return default

def save_config(config):
    """Guarda configuración."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_db():
    """Carga base de datos."""
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
    """Guarda base de datos."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

# Variables globales para API
config = load_config()
db = load_db()

# --- REST ENDPOINTS ---

@app.route('/', methods=['GET'])
@app.route('/ui/', methods=['GET'])
@app.route('/ui', methods=['GET'])
def index():
    """Sirve el frontend."""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend'), 'index.html')

@app.route('/api/status', methods=['GET'])
def api_status():
    """Estado general del sistema."""
    global auto_enabled, vmix_status, next_programa, next_tanda
    
    return jsonify({
        "auto_enabled": auto_enabled,
        "dia_hoy": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][datetime.now().weekday()],
        "tanda_en_progreso": _tanda_en_progreso,
        "timestamp": datetime.now().isoformat(),
        "total_programas": sum(len(db["programas"].get(d, [])) for d in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]),
        "total_tandas": sum(len(db["tandas"].get(d, [])) for d in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]),
        "vmix": vmix_status,
        "next_programa": next_programa,
        "next_tanda": next_tanda
    })

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Obtiene/guarda configuración."""
    global config, VMIX_URL
    if request.method == 'GET':
        cfg = config.copy()
        cfg['VMIX_URL'] = VMIX_URL
        return jsonify(cfg)
    else:
        data = request.get_json()
        
        # Cambiar URL de vMix si viene en la request
        if 'VMIX_URL' in data:
            new_url = data['VMIX_URL'].strip()
            if new_url:
                VMIX_URL = new_url
                with open(VMIX_CONFIG_FILE, 'w') as f:
                    f.write(new_url)
                log(f"[CONFIG] URL de vMix cambiada a: {new_url}")
        
        # Guardar resto de config
        for key in data:
            if key != 'VMIX_URL' and key in config:
                config[key] = data[key]
        
        save_config(config)
        log("[CONFIG] Configuración guardada")
        return jsonify({"status": "ok"})

@app.route('/api/vmix/test', methods=['GET'])
def api_vmix_test():
    """Verifica conectividad a vMix."""
    try:
        r = requests.get(VMIX_URL, params={'Function': 'GetStatus'}, timeout=2)
        if r.status_code == 200:
            return jsonify({"status": "conectado", "url": VMIX_URL, "response_code": r.status_code})
        else:
            return jsonify({"status": "error", "url": VMIX_URL, "response_code": r.status_code, "error": r.text[:100]})
    except requests.ConnectionError:
        return jsonify({"status": "no_conecta", "url": VMIX_URL, "error": "Connection refused"})
    except requests.Timeout:
        return jsonify({"status": "timeout", "url": VMIX_URL, "error": "Request timeout"})
    except Exception as e:
        return jsonify({"status": "error", "url": VMIX_URL, "error": str(e)})

@app.route('/api/db', methods=['GET'])
def api_db():
    """Obtiene base de datos completa."""
    return jsonify(db)

@app.route('/api/events', methods=['GET'])
def api_events():
    """Obtiene eventos de un día (GET /api/events?dia=Lunes)."""
    dia = request.args.get('dia', "Lunes")
    return jsonify({
        "programas": db["programas"].get(dia, []),
        "tandas": db["tandas"].get(dia, [])
    })

@app.route('/api/events/<type>/<dia>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_events_crud(type, dia):
    """CRUD para eventos de un día."""
    global db
    
    if type not in ["programas", "tandas"]:
        return jsonify({"error": "Tipo inválido"}), 400
    
    if dia not in db.get(type, {}):
        db.setdefault(type, {})[dia] = []
    
    if request.method == 'GET':
        return jsonify(db[type][dia])
    
    elif request.method == 'POST':
        new_event = request.get_json()
        db[type][dia].append(new_event)
        db[type][dia].sort(key=lambda x: x['time'])
        save_db(db)
        log(f"[DB] Evento agregado en {dia}")
        return jsonify(new_event), 201
    
    elif request.method == 'PUT':
        idx = request.args.get('idx', type=int)
        updated = request.get_json()
        if 0 <= idx < len(db[type][dia]):
            db[type][dia][idx] = updated
            db[type][dia].sort(key=lambda x: x['time'])
            save_db(db)
            log(f"[DB] Evento modificado en {dia}")
            return jsonify(updated)
        return jsonify({"error": "Índice no válido"}), 404
    
    elif request.method == 'DELETE':
        idx = request.args.get('idx', type=int)
        if 0 <= idx < len(db[type][dia]):
            db[type][dia].pop(idx)
            save_db(db)
            log(f"[DB] Evento eliminado en {dia}")
            return jsonify({"status": "ok"})
        return jsonify({"error": "Índice no válido"}), 404

@app.route('/api/auto/toggle', methods=['POST'])
def api_auto_toggle():
    """Activa/desactiva automático."""
    global auto_enabled
    auto_enabled = not auto_enabled
    log(f"[AUTO] Cambió a: {'ON' if auto_enabled else 'OFF'}")
    return jsonify({"auto_enabled": auto_enabled})

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """Obtiene últimas líneas del log."""
    lines = request.args.get('lines', 50, type=int)
    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
            return jsonify({"logs": recent_lines})
    except:
        return jsonify({"logs": []})

@app.route('/api/vmix/fade', methods=['POST'])
def api_vmix_fade():
    """Ejecuta un Fade en vMix."""
    data = request.get_json()
    input_id = data.get('input')
    duration = data.get('duration', 500)
    
    result = call_vmix('Fade', Input=str(input_id), Duration=str(duration))
    return jsonify({"status": "ok" if result else "error"})

@app.route('/api/vmix/cut', methods=['POST'])
def api_vmix_cut():
    """Ejecuta un Cut en vMix."""
    data = request.get_json()
    input_id = data.get('input')
    
    result = call_vmix('Cut', Input=str(input_id))
    return jsonify({"status": "ok" if result else "error"})

@app.route('/api/tanda/execute', methods=['POST'])
def api_tanda_execute():
    """Ejecuta una tanda publicitaria."""
    global _tanda_en_progreso, auto_enabled, config
    
    if _tanda_en_progreso:
        return jsonify({"error": "Tanda ya en curso"}), 400
    
    tanda_data = request.get_json()
    
    def tanda_sequence():
        global _tanda_en_progreso, _tanda_entrada_anterior, _tanda_entrada_actual, _tanda_tiempo_inicio
        global _tanda_lista_id, _tanda_total_spots, _mostrar_estado_vivo, auto_enabled
        
        if not _tanda_lock.acquire(blocking=False):
            log("⚠️ [TANDA] Ya hay una tanda en curso")
            return
        
        _mostrar_estado_vivo = False
        
        try:
            list_input = str(tanda_data.get('list_id', config.get('PUBLIS_LISTA_ID', '15')))
            spots_count = int(tanda_data.get('spots', config.get('PUBLIS_POR_BLOQUE', 4)))
            
            if not list_input or list_input == '0':
                raise Exception("ID de lista no definido")
            
            estado_previo = obtener_estado_completo()
            _tanda_entrada_anterior = estado_previo.get('entrada')
            _tanda_lista_id = list_input
            _tanda_total_spots = spots_count
            _tanda_en_progreso = True
            _tanda_tiempo_inicio = datetime.now()
            _tanda_entrada_actual = f"Lista {list_input}"
            
            real_item_count = get_lista_item_count(list_input)
            if real_item_count <= 0:
                raise Exception(f"Lista {list_input} vacía")
            
            actual_spots = min(spots_count, real_item_count)
            indices_spots = list(range(real_item_count))[:actual_spots]
            
            log(f"🎬 INICIANDO TANDA - Lista: {list_input} | Spots: {actual_spots}")
            
            # JINGLE ENTRADA
            inicio_input = config.get("INICIO_PUBLIS_INPUT", "14")
            log(f"[1/4] JINGLE ENTRADA: {inicio_input}")
            call_vmix('Fade', Input=inicio_input, Duration=str(config.get('FADE_DURATION_MS', 500)))
            esperar_fin_reproduccion(inicio_input, timeout=config.get('INICIO_PUBLIS_TIMEOUT', 11))
            
            # SPOTS
            log(f"[2/4] REPRODUCIENDO {actual_spots} SPOTS")
            for i, spot_idx in enumerate(indices_spots, 1):
                call_vmix('SelectIndex', Input=list_input, Value=str(spot_idx))
                time.sleep(0.1)
                call_vmix('SetPosition', Input=list_input, Value='0')
                time.sleep(0.05)
                
                if i == 1:
                    call_vmix('Fade', Input=list_input, Duration=str(config.get('FADE_DURATION_MS', 500)))
                else:
                    call_vmix('Cut', Input=list_input)
                
                time.sleep(0.3)
                esperar_fin_reproduccion(list_input, timeout=config.get('PUBLIS_CLIP_TIMEOUT', 300))
            
            # JINGLE CIERRE
            cierre_input = config.get("CIERRE_PUBLIS_INPUT", "16")
            log(f"[3/4] JINGLE CIERRE: {cierre_input}")
            call_vmix('Fade', Input=cierre_input, Duration=str(config.get('FADE_DURATION_MS', 500)))
            esperar_fin_reproduccion(cierre_input, timeout=config.get('CIERRE_PUBLIS_TIMEOUT', 15))
            
            # RESTAURAR
            log(f"[4/4] RESTAURANDO ENTRADA {_tanda_entrada_anterior}")
            time.sleep(0.5)
            restaurar_estado(estado_previo)
            
            log("✅ TANDA COMPLETADA")
        except Exception as e:
            log(f"❌ ERROR EN TANDA: {e}")
        finally:
            _tanda_en_progreso = False
            _tanda_entrada_actual = None
            _tanda_entrada_anterior = None
            _tanda_lista_id = None
            _tanda_total_spots = None
            _tanda_tiempo_inicio = None
            _mostrar_estado_vivo = True
            time.sleep(0.2)
            try:
                _tanda_lock.release()
            except RuntimeError:
                pass
    
    threading.Thread(target=tanda_sequence, daemon=True).start()
    return jsonify({"status": "tanda_iniciada"})

# --- BACKGROUND THREADS ---

def vmix_monitor():
    """Monitor de estado vivo de vMix."""
    global vmix_status, _mostrar_estado_vivo
    
    while True:
        try:
            if not _mostrar_estado_vivo:
                time.sleep(0.1)
                continue
            
            r = requests.get(VMIX_URL, timeout=0.3)
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                active_elem = root.find('active')
                if active_elem is not None and active_elem.text:
                    vmix_status['entrada_activa'] = active_elem.text
                    vmix_status['conectado'] = True
                    vmix_status['ultima_actualizacion'] = datetime.now().isoformat()
                else:
                    vmix_status['conectado'] = False
            else:
                vmix_status['conectado'] = False
        except Exception:
            vmix_status['conectado'] = False
        
        time.sleep(0.5)

def system_ticker():
    """Ejecuta eventos programados."""
    global auto_enabled, last_fired, db, next_programa, next_tanda
    
    while True:
        try:
            if not auto_enabled:
                time.sleep(1)
                continue
            
            ahora = datetime.now()
            t_str = ahora.strftime("%H:%M:%S")
            dia_hoy = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][ahora.weekday()]
            
            if last_fired != t_str:
                # Ejecutar programas
                for ev in db.get("programas", {}).get(dia_hoy, []):
                    if ev['time'] == t_str:
                        log(f"[SCHEDULER] Ejecutando PROGRAMA: {ev['name']}")
                        call_vmix('Fade', Input=ev['name'], Duration='500')
                
                # Ejecutar tandas
                for ev in db.get("tandas", {}).get(dia_hoy, []):
                    if ev['time'] == t_str:
                        log(f"[SCHEDULER] Ejecutando TANDA")
                        try:
                            requests.post('http://127.0.0.1:8080/api/tanda/execute', json=ev)
                        except Exception:
                            pass
                
                last_fired = t_str
            
            # Calcular próximos eventos
            for ev in db.get("programas", {}).get(dia_hoy, []):
                ev_time = datetime.strptime(ev['time'], "%H:%M:%S").replace(year=ahora.year, month=ahora.month, day=ahora.day)
                if ev_time > ahora:
                    next_programa = {"time": ev['time'], "name": ev.get('name', '?')}
                    break
            
            for ev in db.get("tandas", {}).get(dia_hoy, []):
                ev_time = datetime.strptime(ev['time'], "%H:%M:%S").replace(year=ahora.year, month=ahora.month, day=ahora.day)
                if ev_time > ahora:
                    next_tanda = {"time": ev['time'], "list_id": ev.get('list_id', '?')}
                    break
            
            time.sleep(1)
        except Exception as e:
            log(f"[ERROR] system_ticker: {e}")
            time.sleep(1)

if __name__ == '__main__':
    # Iniciar threads
    threading.Thread(target=vmix_monitor, daemon=True).start()
    threading.Thread(target=system_ticker, daemon=True).start()
    
    # Iniciar Flask
    log("[STARTUP] Iniciando vMix Schedule 44 API")
    app.run(host='0.0.0.0', port=8080, debug=False)
