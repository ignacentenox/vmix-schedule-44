#!/usr/bin/env python3
"""
vMix Schedule 44 - Versión Windows Portable
Compatible con Windows 10 / Windows 11
Rutas dinámicas (relativas) para portabilidad
"""

import sys
import json
import os
import requests
import threading
import time
import xml.etree.ElementTree as ET
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                               QListWidget, QFrame, QDialog, QTimeEdit, QLineEdit,
                               QSpinBox, QMenu, QTextEdit, QScrollArea, QMessageBox)
from PySide6.QtCore import QTimer, Qt, QTime
from PySide6.QtGui import QColor, QPainter, QFont

# --- RUTAS DINÁMICAS (PORTABLES) ---
# Si se ejecuta desde el .exe (PyInstaller), usar directorio del exe
# Si se ejecuta desde Python directo, usar directorio del script
if getattr(sys, 'frozen', False):
    # Ejecutado como .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Ejecutado como script Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "vMix_Schedule_44_Contenidos_DB.json")
CONFIG_FILE = os.path.join(BASE_DIR, "vMix_Schedule_44_Contenidos_Config.json")
LOG_FILE = os.path.join(BASE_DIR, "schedule_log.txt")
VMIX_URL = 'http://192.168.192.140:8098/api/'

# Crear carpeta de datos si no existe
os.makedirs(BASE_DIR, exist_ok=True)

print(f"[INIT] Ejecutando desde: {BASE_DIR}")
print(f"[INIT] DB: {DB_FILE}")
print(f"[INIT] Config: {CONFIG_FILE}")

# Lock para evitar tandas superpuestas
_tanda_lock = threading.Lock()

# Variables para monitoreo de tanda en vivo
_tanda_en_progreso = False
_tanda_entrada_anterior = None
_tanda_entrada_actual = None
_tanda_tiempo_inicio = None
_tanda_lista_id = None
_tanda_total_spots = None
_tanda_proximo_programa = None
_tanda_proxima_tanda = None
_mostrar_estado_vivo = True

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
                            
                            # Si obtenemos duración real del video, usarla como timeout
                            if dur > 0 and duracion_video is None:
                                duracion_video = dur
                                timeout_dinamico = start + dur + 2.0
                                log(f"[Video {input_num}] Duración: {dur:.1f}s, timeout dinámico activado")
                            
                            # Condición de finalización
                            if state == 'Paused' and pos >= dur:
                                log(f"[Video {input_num}] Reproducción completada (pos={pos:.1f}s, dur={dur:.1f}s)")
                                return True
                        except (ValueError, TypeError):
                            pass
        except requests.exceptions.Timeout:
            errores['timeout'] += 1
        except Exception as e:
            errores['exceptions'] += 1
            pass
        
        time.sleep(0.1)
    
    log(f"[Video {input_num}] TIMEOUT - Último estado: {ultimo_estado} | Checks: {checks} | Errores: {errores}")
    return False

def obtener_estado_completo():
    """Obtiene el estado completo de vMix."""
    try:
        r = requests.get(VMIX_URL, timeout=0.3)
        if r.status_code == 200:
            return ET.fromstring(r.text)
    except:
        pass
    return None

def execute_tanda_block(evento_id, entrada_jingle, entrada_publis, entrada_cierre, lista_id, spots):
    """Ejecuta bloque de publicidades (4 pasos atómicos con sincronización precisa)."""
    global _tanda_en_progreso, _tanda_entrada_anterior, _tanda_entrada_actual, _mostrar_estado_vivo
    
    with _tanda_lock:
        if _tanda_en_progreso:
            log("[TANDA] Ya hay una tanda en ejecución, rechazando nueva")
            return False
        _tanda_en_progreso = True
    
    try:
        # Paso 1: Reproducir jingle entrada (3s esperado)
        log(f"[TANDA] PASO 1: Jingle Entrada (Input {entrada_jingle})")
        _mostrar_estado_vivo = False
        _tanda_entrada_anterior = obtener_entrada_activa()
        call_vmix('ActivateInput', Input=entrada_jingle)
        time.sleep(0.5)
        esperar_fin_reproduccion(entrada_jingle, timeout=15)
        
        # Paso 2: Reproducir spots (loops en lista)
        log(f"[TANDA] PASO 2: Reproduciéndose {spots} spots de lista {lista_id}")
        call_vmix('ActivateInput', Input=entrada_publis)
        time.sleep(0.3)
        
        # Calcular tiempo total para los spots
        tiempo_spots_inicio = time.time()
        for i in range(spots):
            call_vmix('ListGoToIndex', ListID=lista_id, Value=i)
            time.sleep(0.15)
            esperar_fin_reproduccion(entrada_publis, timeout=30)
            tiempo_transcurrido = time.time() - tiempo_spots_inicio
            log(f"[TANDA] Spot {i+1}/{spots} completado (tiempo total: {tiempo_transcurrido:.1f}s)")
        
        # Paso 3: Reproducir jingle cierre (5s esperado)
        log(f"[TANDA] PASO 3: Jingle Cierre (Input {entrada_cierre})")
        call_vmix('ActivateInput', Input=entrada_cierre)
        time.sleep(0.5)
        esperar_fin_reproduccion(entrada_cierre, timeout=15)
        
        # Paso 4: Restaurar entrada anterior
        log(f"[TANDA] PASO 4: Restaurando entrada {_tanda_entrada_anterior}")
        if _tanda_entrada_anterior:
            call_vmix('ActivateInput', Input=_tanda_entrada_anterior)
        
        log(f"[TANDA] ✅ COMPLETADA en {time.time() - tiempo_spots_inicio:.1f}s")
        return True
    
    except Exception as e:
        log(f"[TANDA] ❌ ERROR: {e}\n{traceback.format_exc()}")
        return False
    
    finally:
        _mostrar_estado_vivo = True
        with _tanda_lock:
            _tanda_en_progreso = False

def obtener_entrada_activa():
    """Obtiene el número de la entrada activa."""
    try:
        root = obtener_estado_completo()
        if root:
            active = root.find('active')
            if active is not None and active.text:
                return active.text
    except:
        pass
    return "1"

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
            'time': self.time_edit.time().toString("HH:mm:ss"),
            'list_id': self.list_id_edit.text().strip(),
            'spots': self.spot_count.value()
        }

class EventDialog(QDialog):
    """Diálogo para agregar/editar eventos de programa."""
    def __init__(self, parent=None, event_data=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Evento")
        self.setFixedSize(450, 300)
        self.setStyleSheet("background-color: #121212; color: white; border: 1px solid #333;")
        layout = QVBoxLayout(self)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setStyleSheet("font-size: 14px; padding: 5px;")
        
        self.title_edit = QLineEdit()
        self.title_edit.setStyleSheet("font-size: 14px; padding: 5px;")
        self.title_edit.setPlaceholderText("Nombre del programa")
        
        if event_data:
            self.time_edit.setTime(QTime.fromString(event_data.get('time', '00:00:00'), "HH:mm:ss"))
            self.title_edit.setText(event_data.get('title', ''))
        
        layout.addWidget(QLabel("⏰ HORA:"))
        layout.addWidget(self.time_edit)
        layout.addWidget(QLabel("📺 PROGRAMA:"))
        layout.addWidget(self.title_edit)
        layout.addStretch()
        
        btn = QPushButton("GUARDAR")
        btn.setStyleSheet("background: #00f2ff; color: black; font-weight: bold; padding: 12px; margin-top: 10px; border-radius: 4px;")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
    
    def get_data(self):
        return {
            'time': self.time_edit.time().toString("HH:mm:ss"),
            'title': self.title_edit.text().strip()
        }

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
            QTabBar::tab { background: #111; color: #777; padding: 8px 20px; border: none; font-weight: bold; font-size: 12px; }
            QTabBar::tab:selected { color: #00f2ff; border-bottom: 2px solid #00f2ff; background: #181818; }
            QListWidget { background: transparent; color: #ddd; border: none; font-family: 'Consolas', monospace; font-size: 12px; outline: none; }
            QListWidget::item { padding: 6px; border-bottom: 1px solid #151515; }
            QListWidget::item:selected { background: #1a1a1a; color: #00f2ff; }
            QLineEdit, QSpinBox { background: transparent; color: white; border: none; padding: 3px; border-radius: 0px; font-size: 11px; }
            QPushButton { background: #222; color: #aaa; border: 1px solid #444; padding: 4px 12px; border-radius: 2px; font-size: 11px; }
            QPushButton:hover { background: #333; }
            #btn_vivo { background: transparent; color: #00f2ff; border: 2px solid #00f2ff; font-weight: bold; font-size: 13px; border-radius: 4px; padding: 8px; }
            #btn_auto { font-weight: bold; border-radius: 3px; padding: 4px 8px; font-size: 10px; }
        """)

        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- BARRA SUPERIOR ---
        config_panel = QFrame(); config_panel.setFixedHeight(50); config_panel.setStyleSheet("background: #0f0f0f; border-bottom: 1px solid #222;")
        config_layout = QHBoxLayout(config_panel)
        config_layout.setContentsMargins(10, 5, 10, 5)
        config_layout.setSpacing(10)
        
        btn_save_cfg = QPushButton("✓ APLICAR")
        btn_save_cfg.setFixedWidth(100)
        btn_save_cfg.clicked.connect(self.save_config)

        config_layout.addStretch()
        config_layout.addWidget(btn_save_cfg)
        main_layout.addWidget(config_panel)

        # --- MONITOR BOX ---
        monitor_box = QFrame(); monitor_box.setFixedHeight(120); monitor_box.setStyleSheet("background: #0a0a0a; border: 1px solid #222;")
        monitor_layout = QHBoxLayout(monitor_box)
        monitor_layout.setContentsMargins(15, 10, 15, 10)
        monitor_layout.setSpacing(20)

        # Izquierda: Botón EN VIVO + AUTO
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
        main_layout.addLayout(footer)

    def toggle_auto(self):
        self.auto_enabled = not self.auto_enabled
        if self.auto_enabled:
            self.btn_vivo.setText("EN VIVO")
            self.btn_vivo.setStyleSheet("#btn_vivo { background: transparent; color: #00f2ff; border: 2px solid #00f2ff; font-weight: bold; font-size: 14px; border-radius: 6px; }")
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
            "PUBLIS_POR_BLOQUE": self.config.get("PUBLIS_POR_BLOQUE", 4),
            "INICIO_PUBLIS_INPUT": "14",
            "PUBLIS_LISTA_ID": "15",
            "CIERRE_PUBLIS_INPUT": "16",
            "FADE_DURATION_MS": 500,
            "PUBLIS_CLIP_TIMEOUT": 300,
            "INICIO_PUBLIS_TIMEOUT": 11,
            "CIERRE_PUBLIS_TIMEOUT": 5
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        log(f"[CONFIG] Guardada - JINGLES: 14 (entrada) → 15 (publis) → 16 (cierre) | SPOTS: {self.config['PUBLIS_POR_BLOQUE']}")
        
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
            }
        """)
        msg.setText("Configuración guardada correctamente.")
        msg.exec()

    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"events": {}}
        return {"events": {}}

    def save_db(self):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=4, ensure_ascii=False)
        log("[DB] Base de datos guardada")

    def refresh_ui(self):
        """Actualiza la UI con datos de la base de datos."""
        for day_key in self.prog_lists.keys():
            self.prog_lists[day_key].clear()
            self.tanda_lists[day_key].clear()
            
            if day_key in self.db.get("events", {}):
                eventos = self.db["events"][day_key]
                for evt_id, evt in eventos.items():
                    tipo = evt.get("type", "prog")
                    titulo = evt.get("title", "Sin título")
                    hora = evt.get("time", "--:--:--")
                    
                    if tipo == "tanda":
                        spots = evt.get("spots", 4)
                        lista = evt.get("list_id", "?")
                        texto = f"[{hora}] TANDA - {spots} spots (Lista: {lista})"
                        self.tanda_lists[day_key].addItem(texto)
                    else:
                        texto = f"[{hora}] {titulo}"
                        self.prog_lists[day_key].addItem(texto)

    def show_context_menu(self, pos):
        sender = self.sender()
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: #1a1a1a; color: white; } QMenu::item:selected { background: #00f2ff; color: black; }")
        
        edit_action = menu.addAction("✏️ Editar")
        del_action = menu.addAction("🗑️ Eliminar")
        
        action = menu.exec(sender.mapToGlobal(pos))
        
        if action == edit_action:
            item = sender.itemAt(pos)
            if item:
                self.edit_event(sender, item)
        elif action == del_action:
            item = sender.itemAt(pos)
            if item:
                self.delete_event_from_list(sender, item)

    def add_event(self):
        """Abre diálogo para agregar evento."""
        tab_index = self.main_tabs.currentIndex()
        if tab_index == 0:
            dialog = EventDialog(self)
        else:
            dialog = TandaConfigDialog(self)
        
        if dialog.exec():
            data = dialog.get_data()
            current_tab = self.prog_tabs.currentWidget() if tab_index == 0 else self.tanda_tabs.currentWidget()
            day_key = None
            for d, w in (self.prog_lists.items() if tab_index == 0 else self.tanda_lists.items()):
                if w == current_tab:
                    day_key = d
                    break
            
            if day_key:
                if "events" not in self.db:
                    self.db["events"] = {}
                if day_key not in self.db["events"]:
                    self.db["events"][day_key] = {}
                
                evt_id = f"{data['time']}"
                if tab_index == 0:
                    self.db["events"][day_key][evt_id] = {
                        "type": "prog",
                        "time": data['time'],
                        "title": data['title']
                    }
                else:
                    self.db["events"][day_key][evt_id] = {
                        "type": "tanda",
                        "time": data['time'],
                        "list_id": data['list_id'],
                        "spots": data['spots']
                    }
                
                self.save_db()
                self.refresh_ui()

    def delete_event(self):
        """Elimina evento seleccionado."""
        tab_index = self.main_tabs.currentIndex()
        current_tab = self.prog_tabs.currentWidget() if tab_index == 0 else self.tanda_tabs.currentWidget()
        item = current_tab.currentItem()
        
        if item:
            day_key = None
            for d, w in (self.prog_lists.items() if tab_index == 0 else self.tanda_lists.items()):
                if w == current_tab:
                    day_key = d
                    break
            
            if day_key and day_key in self.db.get("events", {}):
                del self.db["events"][day_key][item.text().split(']')[0].replace('[', '') + "]"]
                self.save_db()
                self.refresh_ui()

    def delete_event_from_list(self, list_widget, item):
        self.delete_event()

    def edit_event(self, list_widget, item):
        pass

    def system_tick(self):
        """Cada segundo: actualiza reloj y chequea si hay que disparar eventos."""
        now = datetime.now()
        self.lbl_clock.setText(now.strftime("%H:%M:%S"))
        
        # Obtener próximos eventos
        next_prog = None
        next_tanda = None
        
        for day, events in self.db.get("events", {}).items():
            for evt_id, evt in events.items():
                evt_time = evt.get('time', '00:00:00')
                if evt.get('type') == 'tanda':
                    if not next_tanda or evt_time < next_tanda['time']:
                        next_tanda = {'time': evt_time, 'day': day, 'data': evt}
                else:
                    if not next_prog or evt_time < next_prog['time']:
                        next_prog = {'time': evt_time, 'day': day, 'data': evt}
        
        # Mostrar próximos eventos
        if next_prog:
            self.lbl_next_prog.setText(f"PRÓX. PROGRAMA: {next_prog['time']} ({next_prog['day']})")
        if next_tanda:
            self.lbl_next_tanda.setText(f"PRÓX. TANDA: {next_tanda['time']} ({next_tanda['day']})")
        
        # Dispararar eventos si AUTO está ON
        if self.auto_enabled:
            time_key = now.strftime("%H:%M:%S")
            day_key = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][now.weekday()]
            
            if day_key in self.db.get("events", {}):
                for evt_id, evt in self.db["events"][day_key].items():
                    if evt.get('time') == time_key and self.last_fired != time_key:
                        self.last_fired = time_key
                        if evt.get('type') == 'tanda':
                            threading.Thread(
                                target=execute_tanda_block,
                                args=(evt_id, self.config.get("INICIO_PUBLIS_INPUT", "14"),
                                      self.config.get("PUBLIS_LISTA_ID", "15"),
                                      self.config.get("CIERRE_PUBLIS_INPUT", "16"),
                                      evt.get('list_id', '15'),
                                      evt.get('spots', 4)),
                                daemon=True
                            ).start()

    def vmix_monitor(self):
        """Monitor de estado vivo de vMix - actualiza UI."""
        global _mostrar_estado_vivo
        
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
                        active_id = active_elem.text
                        for inp in root.findall('.//input'):
                            if inp.get('number') == str(active_id):
                                name = inp.get('title', f"Input {active_id}")
                                break
                        else:
                            name = f"Input {active_id}"
                        
                        self.lbl_main.setText(f"{name.upper()} (#{active_id})")
            except Exception as e:
                pass
            time.sleep(0.1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AMixTVPro(); win.show()
    sys.exit(app.exec())
