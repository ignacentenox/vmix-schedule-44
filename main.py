import sys
import json
import os
import requests
import threading
import time
import xml.etree.ElementTree as ET

import traceback
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                               QListWidget, QFrame, QDialog, QTimeEdit, QLineEdit,
                               QSpinBox, QMenu, QTextEdit, QScrollArea, QMessageBox)
from PySide6.QtCore import QTimer, Qt, QTime
from PySide6.QtGui import QColor, QPainter, QFont

# --- RUTAS ---
BASE_DIR = "/Users/ignaciomanuelcenteno/Documents/PROG/2025/CANAL44_RCUPLAY/scheduletv"
DB_FILE = os.path.join(BASE_DIR, "vMix_Schedule_44_Contenidos_DB.json")
CONFIG_FILE = os.path.join(BASE_DIR, "vMix_Schedule_44_Contenidos_Config.json")
LOG_FILE = os.path.join(BASE_DIR, "schedule_log.txt")
VMIX_URL = 'http://192.168.192.140:8098/api/'

# Lock para evitar tandas superpuestas
_tanda_lock = threading.Lock()

# Variables para monitoreo de tanda en vivo
_tanda_en_progreso = False
_tanda_entrada_anterior = None
_tanda_entrada_actual = None  # Entrada donde está jugando la tanda (jingle/publis)
_tanda_tiempo_inicio = None
_tanda_lista_id = None  # ID de la lista de publis
_tanda_total_spots = None  # Total de spots a reproducir
_tanda_proximo_programa = None  # Próximo programa después de la tanda
_tanda_proxima_tanda = None  # Próxima tanda después de la actual
_mostrar_estado_vivo = True  # Flag para permitir que vmix_monitor actualice el label

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
                log(f"[vMix] {func} Input={kwargs.get('Input', '?')} -> {r.status_code}")
                return r
            if 'No suitable Function' in r.text:
                log(f"[vMix] Función no encontrada: {func}")
                return None
            log(f"[vMix] {func} -> {r.status_code} (intento {attempt+1}/{retries+1})")
        except Exception as e:
            log(f"[vMix] Excepción en {func}: {e}")
        attempt += 1
        time.sleep(delay)
        delay *= backoff
    return None

def esperar_fin_reproduccion(input_num, timeout=600):
    """Espera que una entrada termine de reproducirse completamente (detecta duración real)."""
    start = time.time()
    duracion_video = None
    timeout_dinamico = timeout
    ultimo_estado = {'pos': -1, 'dur': -1, 'state': 'desconocido'}
    checks = 0
    errores = {'status': 0, 'exceptions': 0}
    
    while time.time() - start < timeout_dinamico:
        try:
            r = requests.get(VMIX_URL, timeout=3)
            
            if r.status_code == 200:
                checks += 1
                root = ET.fromstring(r.text)
                for inp in root.findall('.//input'):
                    if inp.get('number') == str(input_num):
                        state = inp.get('state', '')
                        
                        try:
                            pos = float(inp.findtext('position') or -1)
                            dur = float(inp.findtext('duration') or 0)
                            
                            ultimo_estado = {'pos': pos, 'dur': dur, 'state': state}
                            
                            # Detectar duración y ajustar timeout dinámico
                            if duracion_video is None and dur > 0:
                                duracion_video = dur
                                timeout_dinamico = dur + 2.0  # Añade margen de 2 segundos
                                log(f"[REPRODUCCIÓN] Duración detectada: {dur:.1f}s (timeout dinámico: {timeout_dinamico:.1f}s)")
                            
                            # Video completado
                            if state == 'Completed':
                                elapsed = time.time() - start
                                log(f"[REPRODUCCIÓN] ✅ Completado en {elapsed:.1f}s (duración real respetada)")
                                return True
                            
                            # Posición muy cerca del final (dentro del último 5%)
                            if dur > 0 and pos >= (dur * 0.95):
                                elapsed = time.time() - start
                                log(f"[REPRODUCCIÓN] ✅ Fin detectado (pos: {pos:.1f}s, duración: {dur:.1f}s, tiempo: {elapsed:.1f}s)")
                                return True
                        except (ValueError, TypeError) as e:
                            log(f"[DEBUG] Error parsing pos/dur: {e}")
                        break
            else:
                errores['status'] += 1
                if errores['status'] == 1:  # Log solo la primera vez
                    log(f"[ERROR] esperar_fin_reproduccion: vMix retorna status {r.status_code} (input {input_num})")
            
            time.sleep(0.5)
        except Exception as e:
            errores['exceptions'] += 1
            if errores['exceptions'] == 1:  # Log solo la primera vez
                log(f"[ERROR] esperar_fin_reproduccion exception: {e}")
            time.sleep(1)
    
    # Timeout
    elapsed = time.time() - start
    log(f"⚠️ [REPRODUCCIÓN] TIMEOUT tras {elapsed:.1f}s (checks: {checks}, errores_status: {errores['status']}, errores_conn: {errores['exceptions']}, último estado: pos={ultimo_estado['pos']:.1f}s, dur={ultimo_estado['dur']:.1f}s, state={ultimo_estado['state']})")
    return False

def obtener_estado_completo():
    """Captura estado completo de vMix con reintentos."""
    estado = {'entrada': None, 'indices_lista': None, 'posicion': None, 'duracion': None}
    
    for intento in range(3):
        try:
            r = requests.get(VMIX_URL, timeout=3)
            if r.status_code == 200:
                root = ET.fromstring(r.text)
                entrada_activa = root.findtext('active')
                
                if entrada_activa and entrada_activa != 'None':
                    estado['entrada'] = entrada_activa
                    log(f"[DEBUG] Entrada activa capturada: {entrada_activa}")
                    
                    for inp in root.findall('.//input'):
                        if inp.get('number') == str(entrada_activa):
                            estado['posicion'] = inp.findtext('position')
                            estado['duracion'] = inp.findtext('duration')
                            break
                    return estado
                else:
                    log(f"[DEBUG] Entrada nula/None en intento {intento+1}")
            else:
                log(f"[ERROR] obtener_estado_completo: status {r.status_code} (intento {intento+1})")
        except Exception as e:
            log(f"[ERROR] obtener_estado_completo: {e} (intento {intento+1})")
        
        if intento < 2:
            time.sleep(0.5)
    
    log("[WARNING] No se pudo obtener estado de vMix tras 3 intentos")
    return estado

def restaurar_estado(estado_previo):
    """Restaura entrada anterior después de tanda."""
    if not estado_previo or not estado_previo.get('entrada'):
        log("[TANDA] ⚠️ No hay estado previo para restaurar (entrada desconocida)")
        return
    
    entrada = estado_previo['entrada']
    if not entrada or entrada == 'None':
        log("[TANDA] ⚠️ Entrada anterior es None/inválida")
        return
    
    log(f"[TANDA] 🔄 Fade 500ms → Entrada {entrada}")
    call_vmix('Fade', Input=entrada, Duration='500')
    time.sleep(1)  # Espera a que se complete el fade
    log(f"[TANDA] ✅ Fade completado hacia entrada {entrada}")

def get_lista_item_count(list_input):
    """Obtiene número real de items en una lista de vMix."""
    try:
        r = requests.get(VMIX_URL + 'state', timeout=3)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for inp in root.findall('.//input'):
                if inp.get('number') == str(list_input):
                    # Contar elementos en la lista
                    items = inp.findall('list/item')
                    count = len(items)
                    log(f"[LISTA] ID {list_input} tiene {count} elementos")
                    return max(1, count)  # Mínimo 1
    except Exception as e:
        log(f"[ERROR] get_lista_item_count: {e}")
    return 1


class HorizontalVU(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(12); self.setFixedWidth(150)
        self.l, self.r = 0.0, 0.0
    def update_levels(self, l, r): self.l, self.r = l, r; self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(0, 0, self.width(), 4, QColor(40, 40, 40))
        p.fillRect(0, 8, self.width(), 4, QColor(40, 40, 40))
        p.fillRect(0, 0, int(self.l * self.width()), 4, QColor("#00f2ff"))
        p.fillRect(0, 8, int(self.r * self.width()), 4, QColor("#00f2ff"))

class TandaConfigDialog(QDialog):
    """Diálogo para configurar parámetros de tanda."""
    def __init__(self, parent=None, tanda_data=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Tanda de Publicidades")
        self.setFixedSize(400, 350)
        self.setStyleSheet("background-color: #121212; color: white; border: 1px solid #333;")
        layout = QVBoxLayout(self)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setStyleSheet("font-size: 14px; padding: 5px;")
        
        self.list_id_edit = QLineEdit()
        self.list_id_edit.setStyleSheet("font-size: 14px; padding: 5px;")
        self.list_id_edit.setPlaceholderText("ID de lista vMix (ej: 18)")
        
        self.spot_count = QSpinBox()
        self.spot_count.setMinimum(1)
        self.spot_count.setMaximum(20)
        self.spot_count.setValue(4)
        self.spot_count.setStyleSheet("font-size: 14px; padding: 5px;")
        
        if tanda_data:
            self.time_edit.setTime(QTime.fromString(tanda_data.get('time', '00:00:00'), "HH:mm:ss"))
            self.list_id_edit.setText(str(tanda_data.get('list_id', '')))
            self.spot_count.setValue(tanda_data.get('spots', 4))
        
        layout.addWidget(QLabel("⏰ HORA DE INICIO:"))
        layout.addWidget(self.time_edit)
        layout.addWidget(QLabel("📺 ID LISTA vMix:"))
        layout.addWidget(self.list_id_edit)
        layout.addWidget(QLabel("🎬 CANTIDAD DE SPOTS:"))
        layout.addWidget(self.spot_count)
        layout.addStretch()
        
        btn = QPushButton("GUARDAR TANDA")
        btn.setStyleSheet("background: #00f2ff; color: black; font-weight: bold; padding: 12px; margin-top: 10px; border-radius: 4px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
    
    def get_data(self):
        return {
            "time": self.time_edit.time().toString("HH:mm:ss"),
            "list_id": self.list_id_edit.text(),
            "spots": self.spot_count.value()
        }

class EventDialog(QDialog):
    def __init__(self, parent=None, hora="00:00:00", nombre=""):
        super().__init__(parent)
        self.setWindowTitle("Configurar Evento")
        self.setFixedSize(320, 240)
        self.setStyleSheet("background-color: #121212; color: white; border: 1px solid #333;")
        layout = QVBoxLayout(self)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setTime(QTime.fromString(hora, "HH:mm:ss"))
        self.time_edit.setStyleSheet("font-size: 16px; padding: 5px;")
        self.name_edit = QLineEdit(nombre)
        self.name_edit.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(QLabel("HORA DE INICIO:"))
        layout.addWidget(self.time_edit)
        layout.addWidget(QLabel("ID INPUT vMix:"))
        layout.addWidget(self.name_edit)
        btn = QPushButton("GUARDAR EVENTO")
        btn.setStyleSheet("background: #00f2ff; color: black; font-weight: bold; padding: 12px; margin-top: 10px; border-radius: 4px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
    def get_data(self):
        return {"time": self.time_edit.time().toString("HH:mm:ss"), "name": self.name_edit.text()}


class AMixTVPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("vMix Schedule 44 - Powered by IGNACE")
        self.resize(1200, 850)
        self.config = self.load_config()
        self.db = self.load_db()
        self.auto_enabled = True
        self.last_fired = ""
        self.setup_ui()
        self.refresh_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.system_tick)
        self.timer.start(1000)
        threading.Thread(target=self.vmix_monitor, daemon=True).start()

    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #080808; }
            QLabel { font-family: 'Segoe UI', Arial; }
            QTabWidget::pane { border: 1px solid #222; background: #0a0a0a; }
            QTabBar::tab { background: #111; color: #777; padding: 12px 25px; border: 1px solid #222; font-weight: bold; }
            QTabBar::tab:selected { color: #00f2ff; border-bottom: 2px solid #00f2ff; background: #181818; }
            QListWidget { background: transparent; color: #ddd; border: none; font-family: 'Consolas', monospace; font-size: 14px; outline: none; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #151515; }
            QListWidget::item:selected { background: #1a1a1a; color: #00f2ff; }
            QLineEdit, QSpinBox { background: #1a1a1a; color: white; border: 1px solid #333; padding: 4px; border-radius: 3px; }
            #btn_vivo { background: transparent; color: #00f2ff; border: 2px solid #00f2ff; font-weight: bold; font-size: 14px; border-radius: 6px; }
            #btn_auto { font-weight: bold; border-radius: 4px; padding: 5px; font-size: 11px; }
        """)

        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- BARRA SUPERIOR DE CONFIG ---
        config_panel = QFrame(); config_panel.setFixedHeight(50); config_panel.setStyleSheet("background: #0f0f0f; border-bottom: 1px solid #222;")
        config_layout = QHBoxLayout(config_panel)
        
        self.spin_spots = QSpinBox(); self.spin_spots.setValue(self.config.get("PUBLIS_POR_BLOQUE", 4))
        self.in_inicio = QLineEdit(self.config.get("INICIO_PUBLIS_INPUT", "14")); self.in_inicio.setFixedWidth(45)
        self.in_cierre = QLineEdit(self.config.get("CIERRE_PUBLIS_INPUT", "16")); self.in_cierre.setFixedWidth(45)
        
        btn_save_cfg = QPushButton("APLICAR CAMBIOS")
        btn_save_cfg.setStyleSheet("background: #222; color: #aaa; border: 1px solid #444; padding: 4px 15px;")
        btn_save_cfg.clicked.connect(self.save_config)

        config_layout.addWidget(QLabel("SPOTS:"), 0, Qt.AlignRight)
        config_layout.addWidget(self.spin_spots)
        config_layout.addSpacing(20)
        config_layout.addWidget(QLabel("JINGLE IN (ID):"))
        config_layout.addWidget(self.in_inicio)
        config_layout.addWidget(QLabel("JINGLE OUT (ID):"))
        config_layout.addWidget(self.in_cierre)
        config_layout.addStretch()
        config_layout.addWidget(btn_save_cfg)
        main_layout.addWidget(config_panel)

        # --- MONITOR CENTRAL (STATUS) ---
        monitor_box = QFrame(); monitor_box.setFixedHeight(120)
        monitor_layout = QHBoxLayout(monitor_box)

        # Izquierda: Vivo + Botón Auto
        v_vivo = QVBoxLayout()
        self.btn_vivo = QPushButton("EN VIVO"); self.btn_vivo.setFixedSize(130, 45); self.btn_vivo.setObjectName("btn_vivo")
        self.btn_auto = QPushButton("AUTO: ON"); self.btn_auto.setFixedSize(130, 25); self.btn_auto.setObjectName("btn_auto")
        self.btn_auto.setStyleSheet("background: #004422; color: #00ff88; border: 1px solid #00ff88;")
        self.btn_auto.clicked.connect(self.toggle_auto)
        v_vivo.addWidget(self.btn_vivo); v_vivo.addWidget(self.btn_auto)
        monitor_layout.addLayout(v_vivo)

        # Centro: Tiempos y Próximos Eventos
        v_center = QVBoxLayout(); v_center.setAlignment(Qt.AlignCenter)
        self.lbl_main = QLabel("CONECTANDO A VMIX..."); self.lbl_main.setStyleSheet("font-size: 24px; color: white; font-weight: 800; letter-spacing: 1px;")
        
        self.lbl_next_prog = QLabel("PRÓX. PROGRAMA: --:--:-- (-00:00:00)")
        self.lbl_next_prog.setStyleSheet("color: #aaa; font-size: 13px;")
        
        self.lbl_next_tanda = QLabel("PRÓX. TANDA: --:--:-- (-00:00:00)")
        self.lbl_next_tanda.setStyleSheet("color: #00f2ff; font-size: 13px; font-weight: bold;")
        
        v_center.addWidget(self.lbl_main, 0, Qt.AlignCenter)
        v_center.addWidget(self.lbl_next_prog, 0, Qt.AlignCenter)
        v_center.addWidget(self.lbl_next_tanda, 0, Qt.AlignCenter)
        monitor_layout.addLayout(v_center, 1)

        # Derecha: Reloj Gigante
        self.lbl_clock = QLabel("00:00:00"); self.lbl_clock.setStyleSheet("font-size: 55px; color: #00f2ff; font-family: 'Consolas'; font-weight: bold;")
        monitor_layout.addWidget(self.lbl_clock)

        main_layout.addWidget(monitor_box)

        # --- SECCIÓN DE TABLAS ---
        self.main_tabs = QTabWidget()
        self.prog_tabs = QTabWidget(); self.prog_lists = {}
        self.tanda_tabs = QTabWidget(); self.tanda_lists = {}
        for d in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]:
            lp = QListWidget(); lp.setContextMenuPolicy(Qt.CustomContextMenu); lp.customContextMenuRequested.connect(self.show_context_menu)
            self.prog_lists[d] = lp; self.prog_tabs.addTab(lp, d)
            lt = QListWidget(); lt.setContextMenuPolicy(Qt.CustomContextMenu); lt.customContextMenuRequested.connect(self.show_context_menu)
            self.tanda_lists[d] = lt; self.tanda_tabs.addTab(lt, d)
        
        self.main_tabs.addTab(self.prog_tabs, "PROGRAMACIÓN / CONTENIDOS")
        self.main_tabs.addTab(self.tanda_tabs, "TANDAS / PUBLICIDAD")
        main_layout.addWidget(self.main_tabs)

        # --- FOOTER ---
        footer = QHBoxLayout(); footer.setContentsMargins(10, 10, 10, 10)
        btn_add = QPushButton("+ AGREGAR EVENTO"); btn_add.setFixedSize(160, 35)
        btn_add.setStyleSheet("background: #00f2ff; color: black; font-weight: bold; border-radius: 4px;")
        btn_add.clicked.connect(self.add_event)
        
        btn_del = QPushButton("ELIMINAR"); btn_del.setFixedSize(100, 35)
        btn_del.setStyleSheet("background: #331111; color: #ff6666; border: 1px solid #ff6666; border-radius: 4px;")
        btn_del.clicked.connect(self.delete_event)
        
        footer.addWidget(btn_add); footer.addWidget(btn_del); footer.addStretch()
        self.vu = HorizontalVU(); footer.addWidget(self.vu)
        main_layout.addLayout(footer)

    def toggle_auto(self):
        self.auto_enabled = not self.auto_enabled
        if self.auto_enabled:
            self.btn_auto.setText("AUTO: ON")
            self.btn_auto.setStyleSheet("background: #004422; color: #00ff88; border: 1px solid #00ff88;")
        else:
            self.btn_auto.setText("AUTO: OFF")
            self.btn_auto.setStyleSheet("background: #441111; color: #ff6666; border: 1px solid #ff6666;")

    def load_config(self):
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

    def save_config(self):
        """Guarda configuración"""
        self.config = {
            "PUBLIS_POR_BLOQUE": self.spin_spots.value(),
            "INICIO_PUBLIS_INPUT": self.in_inicio.text().strip(),
            "PUBLIS_LISTA_ID": "15",
            "CIERRE_PUBLIS_INPUT": self.in_cierre.text().strip(),
            "FADE_DURATION_MS": 500,
            "PUBLIS_CLIP_TIMEOUT": 300,
            "INICIO_PUBLIS_TIMEOUT": 11,
            "CIERRE_PUBLIS_TIMEOUT": 5
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        log(f"[CONFIG] Guardada - JINGLES: 14 (entrada) → 15 (publis) → 16 (cierre) | SPOTS: {self.config['PUBLIS_POR_BLOQUE']}")
        
        # Mostrar diálogo profesional de confirmación
        msg = QMessageBox(self)
        msg.setWindowTitle("✅ Cambios Aplicados")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0a0a0a;
            }
            QMessageBox QLabel {
                color: #ddd;
                font-size: 13px;
            }
            QPushButton {
                background-color: #1a1a1a;
                color: #00f2ff;
                border: 1px solid #333;
                padding: 5px 20px;
                border-radius: 3px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #222;
                border: 1px solid #444;
            }
        """)
        msg.setIcon(QMessageBox.Information)
        
        config_info = f"""
CONFIGURACIÓN GUARDADA Y APLICADA

▶ Entrada Publis (Jingle): ID 14
▶ Lista Publis (Spots): ID 15
▶ Cierre Publis (Jingle): ID 16
▶ Spots por bloque: {self.config['PUBLIS_POR_BLOQUE']}
▶ Duración Fade: {self.config['FADE_DURATION_MS']}ms
        """.strip()
        
        msg.setText(config_info)
        msg.exec()
        
        # Actualizar UI
        self.refresh_ui()

    def load_db(self):
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        empty = {"programas": {d: [] for d in dias}, "tandas": {d: [] for d in dias}}
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f: return json.load(f)
            except: return empty
        return empty

    def save_db(self):
        with open(DB_FILE, 'w') as f: json.dump(self.db, f, indent=4)

    def refresh_ui(self):
        for d in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]:
            self.prog_lists[d].clear()
            self.tanda_lists[d].clear()
            
            for ev in self.db["programas"].get(d, []):
                self.prog_lists[d].addItem(f"🕒 {ev['time']}   |   INPUT: {ev['name']}")
            
            for ev in self.db["tandas"].get(d, []):
                list_id = ev.get('list_id', '?')
                spots = ev.get('spots', 4)
                self.tanda_lists[d].addItem(f"📺 {ev['time']}   |   LISTA: {list_id}   |   SPOTS: {spots}")

    def show_context_menu(self, pos):
        list_widget = self.sender()
        if item := list_widget.itemAt(pos):
            menu = QMenu(self); menu.setStyleSheet("background: #1a1a1a; color: white;")
            act_edit = menu.addAction("✏️ MODIFICAR"); act_del = menu.addAction("🗑️ ELIMINAR")
            action = menu.exec(list_widget.mapToGlobal(pos))
            if action == act_edit: self.edit_event(list_widget)
            elif action == act_del: self.delete_event()

    def add_event(self):
        is_prog = self.main_tabs.currentIndex() == 0
        tab = self.prog_tabs if is_prog else self.tanda_tabs
        dia = tab.tabText(tab.currentIndex())
        
        if is_prog:
            d = EventDialog(self)
        else:
            d = TandaConfigDialog(self)
        
        if d.exec():
            key = "programas" if is_prog else "tandas"
            self.db[key][dia].append(d.get_data())
            self.db[key][dia].sort(key=lambda x: x['time'])
            self.save_db()
            self.refresh_ui()
            log(f"[DB] Evento agregado en {dia}")

    def edit_event(self, list_widget):
        is_prog = self.main_tabs.currentIndex() == 0
        tab = self.prog_tabs if is_prog else self.tanda_tabs
        dia = tab.tabText(tab.currentIndex())
        idx = list_widget.currentRow()
        if idx >= 0:
            key = "programas" if is_prog else "tandas"
            old = self.db[key][dia][idx]
            
            if is_prog:
                d = EventDialog(self, hora=old['time'], nombre=old['name'])
            else:
                d = TandaConfigDialog(self, tanda_data=old)
            
            if d.exec():
                self.db[key][dia][idx] = d.get_data()
                self.db[key][dia].sort(key=lambda x: x['time'])
                self.save_db()
                self.refresh_ui()
                log(f"[DB] Evento modificado en {dia}")

    def delete_event(self):
        is_prog = self.main_tabs.currentIndex() == 0
        tab = self.prog_tabs if is_prog else self.tanda_tabs
        dia = tab.tabText(tab.currentIndex())
        list_w = self.prog_lists[dia] if is_prog else self.tanda_lists[dia]
        if (idx := list_w.currentRow()) >= 0:
            self.db["programas" if is_prog else "tandas"][dia].pop(idx)
            self.save_db(); self.refresh_ui()

    def _format_timedelta(self, td):
        """Formatea timedelta a HH:MM:SS"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def system_tick(self):
        ahora = datetime.now()
        t_str = ahora.strftime("%H:%M:%S")
        self.lbl_clock.setText(t_str)
        dia_hoy = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][ahora.weekday()]
        
        if self.auto_enabled and self.last_fired != t_str:
            for ev in self.db["programas"].get(dia_hoy, []):
                if ev['time'] == t_str:
                    self.fire_vmix(ev['name'])
            
            for ev in self.db["tandas"].get(dia_hoy, []):
                if ev['time'] == t_str:
                    log(f"[SCHEDULER] Ejecutando TANDA a las {t_str}")
                    self.execute_tanda_block(ev)
            
            self.last_fired = t_str

        # Actualizar Próximos Eventos
        self.update_next_labels(ahora, dia_hoy)

    def update_next_labels(self, ahora, dia):
        def find_next(category):
            for ev in self.db[category].get(dia, []):
                ev_time = datetime.strptime(ev['time'], "%H:%M:%S").replace(year=ahora.year, month=ahora.month, day=ahora.day)
                if ev_time > ahora: return ev, ev_time
            return None, None

        # Siguiente Programa
        prog, p_time = find_next("programas")
        if prog:
            diff = p_time - ahora
            tiempo_restante = self._format_timedelta(diff)
            self.lbl_next_prog.setText(f"PRÓX. PROG: {prog['name']} @ {prog['time']} (-{tiempo_restante})")
        else: self.lbl_next_prog.setText("NO HAY MÁS PROGRAMAS")

        # Siguiente Tanda
        tanda, t_time = find_next("tandas")
        if tanda:
            diff = t_time - ahora
            tiempo_restante = self._format_timedelta(diff)
            list_id = tanda.get('list_id', tanda.get('name', '?'))
            self.lbl_next_tanda.setText(f"PRÓX. TANDA: LISTA {list_id} @ {tanda['time']} (-{tiempo_restante})")
        else: self.lbl_next_tanda.setText("NO HAY MÁS TANDAS")

    def fire_vmix(self, name):
        try:
            requests.get(f"{VMIX_URL}?Function=Fade&Input={name}&Duration=500")
        except Exception as e:
            log(f"[VMIX] Error al ejecutar Fade para '{name}': {e}")

    def execute_tanda_block(self, tanda_data):
        """Ejecuta secuencia completa de tanda con jingle entrada + spots + jingle cierre."""
        def tanda_sequence():
            global _tanda_en_progreso, _tanda_entrada_anterior, _tanda_entrada_actual, _tanda_tiempo_inicio
            global _tanda_lista_id, _tanda_total_spots, _tanda_proximo_programa, _tanda_proxima_tanda
            global _mostrar_estado_vivo

            if not _tanda_lock.acquire(blocking=False):
                log("⚠️ [TANDA] Ya hay una tanda en curso, ignorando")
                self.show_status_message("⚠️ Tanda ya en curso")
                return

            # Desactivar monitor normal de vMix mientras se ejecuta tanda
            _mostrar_estado_vivo = False
            
            try:
                self.lbl_main.setText("")
            except Exception:
                pass

            actual_spots = 0
            mensaje_final = ""
            try:
                # ========== PREPARACIÓN ==========
                list_input = str(tanda_data.get('list_id', self.config.get('PUBLIS_LISTA_ID', '15')))
                spots_count = int(tanda_data.get('spots', self.config.get('PUBLIS_POR_BLOQUE', 4)))
                if not list_input or list_input == '0':
                    raise Exception("ID de lista no definido en tanda")

                # Estado previo para restaurar al final
                estado_previo = obtener_estado_completo()
                _tanda_entrada_anterior = estado_previo.get('entrada')
                _tanda_lista_id = list_input
                _tanda_total_spots = spots_count
                _tanda_en_progreso = True
                _tanda_tiempo_inicio = datetime.now()
                _tanda_entrada_actual = f"Lista {list_input}"

                # Iniciar monitor de tanda
                threading.Thread(target=self._monitor_tanda_countdown, daemon=True).start()

                # Calcular spots reales disponibles
                real_item_count = get_lista_item_count(list_input)
                if real_item_count <= 0:
                    raise Exception(f"Lista {list_input} vacía o no existe")
                
                actual_spots = min(spots_count, real_item_count)
                indices_spots = list(range(real_item_count))[:actual_spots]

                log("=" * 70)
                log(f"🎬 INICIANDO TANDA PUBLICITARIA")
                log(f"   Lista: {list_input} | Spots: {actual_spots} de {real_item_count} disponibles")
                log(f"   Entrada anterior: {_tanda_entrada_anterior}")
                log("=" * 70)

                # ========== PASO 1: JINGLE DE ENTRADA ==========
                inicio_input = self.config.get("INICIO_PUBLIS_INPUT", "14")
                log(f"\n[PASO 1/4] JINGLE DE ENTRADA")
                log(f"   ▶️ Fade {self.config.get('FADE_DURATION_MS',500)}ms → JINGLE ENTRADA (ID: {inicio_input})")
                call_vmix('Fade', Input=inicio_input, Duration=str(self.config.get('FADE_DURATION_MS',500)))
                timeout_entrada = self.config.get('INICIO_PUBLIS_TIMEOUT', 11)
                log(f"   ⏳ Esperando fin de jingle (máx {timeout_entrada}s)...")
                if not esperar_fin_reproduccion(inicio_input, timeout=timeout_entrada):
                    log(f"   ⚠️ Timeout en jingle entrada (continuando igual)")
                log(f"   ✅ Jingle entrada completado")

                # ========== PASO 2: REPRODUCIR SPOTS PUBLICITARIOS ==========
                log(f"\n[PASO 2/4] REPRODUCIENDO {actual_spots} SPOTS DE PUBLICIDAD")
                
                for i, spot_idx in enumerate(indices_spots, 1):
                    log(f"\n   [SPOT {i}/{actual_spots}] ▶️ Seleccionando...")
                    
                    # Seleccionar índice
                    call_vmix('SelectIndex', Input=list_input, Value=str(spot_idx))
                    time.sleep(0.1)  # Pequeña pausa para que vMix registre el cambio
                    
                    # Resetear a inicio
                    call_vmix('SetPosition', Input=list_input, Value='0')
                    time.sleep(0.05)
                    
                    # Primera vez = Fade, resto = Cut
                    if i == 1:
                        log(f"   [SPOT {i}/{actual_spots}] ▶️ Iniciando con Fade {self.config.get('FADE_DURATION_MS',500)}ms")
                        call_vmix('Fade', Input=list_input, Duration=str(self.config.get('FADE_DURATION_MS',500)))
                    else:
                        log(f"   [SPOT {i}/{actual_spots}] ▶️ Cortando a siguiente spot")
                        call_vmix('Cut', Input=list_input)
                    
                    time.sleep(0.3)  # Dar tiempo para que el cut/fade se procese
                    
                    # Esperar a que se reproduzca completamente
                    timeout_spot = self.config.get('PUBLIS_CLIP_TIMEOUT', 300)
                    log(f"   [SPOT {i}/{actual_spots}] 📽️ Reproduciendo (máx {timeout_spot}s)...")
                    if esperar_fin_reproduccion(list_input, timeout=timeout_spot):
                        log(f"   [SPOT {i}/{actual_spots}] ✅ Completado")
                    else:
                        log(f"   [SPOT {i}/{actual_spots}] ⚠️ Timeout (video > {timeout_spot}s, continuando)")

                log(f"\n   ✅ Todos los {actual_spots} spots completados")

                # ========== PASO 3: JINGLE DE CIERRE ==========
                cierre_input = self.config.get("CIERRE_PUBLIS_INPUT", "16")
                log(f"\n[PASO 3/4] JINGLE DE CIERRE")
                log(f"   ▶️ Fade {self.config.get('FADE_DURATION_MS',500)}ms → JINGLE CIERRE (ID: {cierre_input})")
                call_vmix('Fade', Input=cierre_input, Duration=str(self.config.get('FADE_DURATION_MS',500)))
                timeout_cierre = self.config.get('CIERRE_PUBLIS_TIMEOUT', 15)
                log(f"   ⏳ Esperando fin de jingle (máx {timeout_cierre}s)...")
                if not esperar_fin_reproduccion(cierre_input, timeout=timeout_cierre):
                    log(f"   ⚠️ Timeout en jingle cierre (continuando igual)")
                log(f"   ✅ Jingle cierre completado")

                # ========== PASO 4: RESTAURAR ENTRADA ANTERIOR ==========
                log(f"\n[PASO 4/4] RESTAURANDO ENTRADA ANTERIOR")
                log(f"   ▶️ Fade 500ms → Entrada {_tanda_entrada_anterior}")
                time.sleep(0.5)
                restaurar_estado(estado_previo)
                log(f"   ✅ Entrada anterior restaurada")

                log("\n" + "=" * 70)
                log(f"✅ TANDA FINALIZADA - {actual_spots} spots reproducidos sin cortes")
                log("=" * 70)
                mensaje_final = "✅ TANDA COMPLETADA"
            except Exception as e:
                log(f"\n❌ [ERROR] TANDA: {e}\n{traceback.format_exc()}")
                mensaje_final = f"❌ Error en tanda: {e}"
                self.show_status_message(mensaje_final)
            finally:
                # Restaurar estado global y liberar lock
                _tanda_en_progreso = False
                _tanda_entrada_actual = None
                _tanda_entrada_anterior = None
                _tanda_lista_id = None
                _tanda_total_spots = None
                _tanda_proximo_programa = None
                _tanda_proxima_tanda = None
                _tanda_tiempo_inicio = None
                _mostrar_estado_vivo = True  # RE-ACTIVAR monitor normal de vMix
                time.sleep(0.2)
                try:
                    _tanda_lock.release()
                except RuntimeError:
                    pass

                # Mostrar mensaje final en UI y limpiar
                try:
                    self.lbl_main.setText(mensaje_final)
                    if mensaje_final.startswith("✅"):
                        time.sleep(2)
                    else:
                        time.sleep(3)
                    self.lbl_main.setText("")
                    log("[MONITOR] Label limpiado, tanda finalizada")
                except Exception as e:
                    log(f"[ERROR] Limpieza monitor: {e}")

        threading.Thread(target=tanda_sequence, daemon=True).start()

    def _monitor_tanda_countdown(self):
        """Monitorea la tanda en progreso y actualiza contador en UI."""
        global _tanda_en_progreso, _tanda_entrada_anterior, _tanda_entrada_actual, _tanda_tiempo_inicio
        global _tanda_lista_id, _tanda_total_spots, _tanda_proximo_programa, _tanda_proxima_tanda
        
        contador = 0
        try:
            while _tanda_en_progreso:
                # Actualizar cada 1 segundo (divisor 10 = 100ms checks)
                if contador % 10 == 0:
                    if _tanda_tiempo_inicio is None:
                        break
                    
                    if isinstance(_tanda_tiempo_inicio, datetime):
                        tiempo_transcurrido = (datetime.now() - _tanda_tiempo_inicio).total_seconds()
                    else:
                        tiempo_transcurrido = time.time() - _tanda_tiempo_inicio
                    
                    minutos = int(tiempo_transcurrido // 60)
                    segundos = int(tiempo_transcurrido % 60)
                    
                    entrada_actual_str = _tanda_entrada_actual if _tanda_entrada_actual else "?"
                    entrada_anterior_str = _tanda_entrada_anterior if _tanda_entrada_anterior else "?"
                    lista_str = _tanda_lista_id if _tanda_lista_id else "?"
                    spots_str = _tanda_total_spots if _tanda_total_spots else "?"
                    
                    # Formato multi-línea
                    msg = (
                        f"┌─ ENTRADA ACTUAL: {entrada_actual_str}\n"
                        f"├─ PROCESO DE TANDA: {minutos:02d}:{segundos:02d} (Lista {lista_str}, {spots_str} spots)\n"
                        f"├─ VOLVIENDO A: Entrada {entrada_anterior_str}\n"
                        f"└─ Estado: En progreso..."
                    )
                    self.lbl_main.setText(msg)
                
                contador += 1
                time.sleep(0.1)  # Check frecuente (100ms)
        except Exception as e:
            log(f"[ERROR] Monitor tanda: {e}")
        finally:
            # Garantizar que se limpie el label cuando termina
            try:
                time.sleep(0.2)
                self.lbl_main.setText("")
                log("[MONITOR] Label limpiado, tanda finalizada")
            except Exception as e:
                log(f"[ERROR] Limpieza monitor: {e}")

    def show_status_message(self, msg):
        """Muestra mensaje de estado en la UI (desde thread daemon)."""
        try:
            self.lbl_main.setText(msg)
            log(f"[UI] {msg}")
        except Exception as e:
            log(f"[ERROR] show_status_message: {e}")

    def vmix_monitor(self):
        """Monitor de estado vivo de vMix - actualiza UI y niveles de audio."""
        global _mostrar_estado_vivo
        
        while True:
            try:
                # NO actualizar label si hay tanda en progreso (el monitor de tanda lo maneja)
                if not _mostrar_estado_vivo:
                    time.sleep(0.1)
                    continue
                
                r = requests.get(VMIX_URL, timeout=0.3)
                if r.status_code == 200:
                    root = ET.fromstring(r.text)
                    active_elem = root.find('active')
                    if active_elem is not None and active_elem.text:
                        active_id = active_elem.text
                        # Obtener nombre de la entrada activa
                        for inp in root.findall('.//input'):
                            if inp.get('number') == str(active_id):
                                name = inp.get('title', f"Input {active_id}")
                                break
                        else:
                            name = f"Input {active_id}"
                        
                        self.lbl_main.setText(f"{name.upper()} (#{active_id})")
                    
                    # Actualizar niveles de audio
                    master = root.find(".//master")
                    if master is not None:
                        try:
                            l_level = float(master.get('num1', 0))
                            r_level = float(master.get('num2', 0))
                            self.vu.update_levels(l_level, r_level)
                        except (ValueError, TypeError):
                            pass
            except Exception as e:
                # Silenciar errores de conexión frecuentes (timeout normal)
                pass
            time.sleep(0.1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AMixTVPro(); win.show()
    sys.exit(app.exec())