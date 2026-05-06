# 📺 vMix Schedule 44 - Sistema de Automatización Profesional

## 🎯 Descripción Ejecutiva

**vMix Schedule 44** es un sistema completo de automatización y planificación para transmisiones televisivas, diseñado específicamente para integración con vMix. Permite programar contenidos, gestionar tandas publicitarias y automatizar transiciones de forma profesional y confiable.

**Desarrollado por:** IGNACE  
**Branding:** 44 Contenidos  
**Versión:** 1.0 Branded  
**Formato:** Aplicación portable (Windows 10/11) + Scripts Python (Mac/Linux)

---

## ✨ Características Principales

### 🎬 Automatización Completa
- ✅ Programación semanal de eventos (Lunes a Domingo)
- ✅ Ejecución automática a hora exacta (sistema de scheduler)
- ✅ Monitoreo en tiempo real de reproducción
- ✅ Control preciso de transiciones con fade/cut
- ✅ Log completo de todas las operaciones

### 📺 Gestión de Contenidos
- ✅ Programación de programas de TV por día/hora
- ✅ Asignación dinámica de inputs vMix
- ✅ Base de datos persistente (JSON)
- ✅ Interfaz intuitiva para agregar/modificar/eliminar eventos

### 📢 Tandas Publicitarias Inteligentes
- ✅ Bloque de 4 pasos atómicos:
  1. Jingle de entrada (automático)
  2. Reproducción de N spots publicitarios
  3. Jingle de cierre (automático)
  4. Restauración de entrada anterior
- ✅ Configuración flexible de spots por tanda
- ✅ Detección automática de fin de reproducción
- ✅ Prevención de tandas superpuestas (thread-safe)

### 🎛️ Integración vMix Profesional
- ✅ Control HTTP/XML de vMix en tiempo real
- ✅ Manejo de timeouts dinámicos
- ✅ Reintentos con backoff exponencial
- ✅ Soporte para múltiples inputs
- ✅ Control de audio (VU meter)

### 📊 Interfaz Gráfica Avanzada
- ✅ Tema profesional oscuro (dark mode)
- ✅ Monitor de estado en vivo (entrada activa, próximos eventos)
- ✅ Reloj digital gigante (HH:MM:SS)
- ✅ Indicador de próximo programa y próxima tanda
- ✅ Niveles de audio en tiempo real

### 🤖 Sistema Inteligente de AUTO
- ✅ Toggle ON/OFF de ejecución automática
- ✅ Visualización clara del estado (verde ON / rojo OFF)
- ✅ Fallback manual (botón EN VIVO para controlar vMix manualmente)

---

## 🛠️ Funcionalidades Detalladas

### 1️⃣ **Programación Semanal**

```
INTERFAZ:
├─ PROGRAMACIÓN / CONTENIDOS (tab 1)
│  ├─ Lunes
│  ├─ Martes
│  ├─ Miércoles
│  ├─ Jueves
│  ├─ Viernes
│  ├─ Sábado
│  └─ Domingo
│
└─ TANDAS / PUBLICIDAD (tab 2)
   ├─ Lunes
   ├─ Martes
   ...
   └─ Domingo
```

**Funcionalidad:**
- Agregar evento: Click "+ AGREGAR EVENTO" → Dialogo de configuración
- Modificar: Click derecho → "✏️ MODIFICAR"
- Eliminar: Click derecho → "🗑️ ELIMINAR" o selecciona + "ELIMINAR"
- Almacenamiento: JSON persistente (datos se guardan automáticamente)

### 2️⃣ **Configuración de Programas**

```
Formato almacenado:
{
  "time": "HH:MM:SS",
  "name": "INPUT_ID_VMIX"
}

Ejemplo:
{
  "time": "10:00:00",
  "name": "12"
}
```

**Acciones:**
- A la hora exacta: Sistema fade a input especificado
- Durabilidad: Indefinida (hasta que otro evento la remplace)
- Logs: Registrados en `schedule_log.txt`

### 3️⃣ **Configuración de Tandas**

```
Formato almacenado:
{
  "time": "HH:MM:SS",
  "list_id": "15",
  "spots": 4
}
```

**Ejemplo de Ejecución (Tanda de 4 Spots):**

```
[PASO 1] JINGLE DE ENTRADA (ID: 14)
└─ Fade 500ms → Jingle entrada (3s aprox)
└─ Espera completación

[PASO 2] REPRODUCIR 4 SPOTS (Lista ID: 15)
├─ Spot 1: Fade 500ms + espera fin
├─ Spot 2: Cut + espera fin
├─ Spot 3: Cut + espera fin
└─ Spot 4: Cut + espera fin
└─ Total spots: ~46s × 4 = 184s

[PASO 3] JINGLE DE CIERRE (ID: 16)
└─ Fade 500ms → Jingle cierre (5s aprox)
└─ Espera completación

[PASO 4] RESTAURAR ENTRADA ANTERIOR
└─ Fade 500ms → Entrada original
└─ Tiempo total: ~187.5 segundos (3 minutos 7 segundos)
```

**Características de Seguridad:**
- Lock global (_tanda_lock) previene tandas simultáneas
- Detección de reproducción completada (XML state='Completed' o posición ≥95%)
- Timeout dinámico basado en duración real del video
- Logging detallado de cada paso

### 4️⃣ **Panel de Control Superior**

```
┌─────────────────────────────────────────────────────────┐
│ SPOTS: [4] | JINGLE IN: [14] | JINGLE OUT: [16] | APLICAR│
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- SPOTS: Cantidad de spots por tanda (1-20)
- JINGLE IN: ID entrada jingle de comienzo (input 14)
- JINGLE OUT: ID entrada jingle de cierre (input 16)
- APLICAR CAMBIOS: Guarda configuración en `vMix_Schedule_44_Contenidos_Config.json`

### 5️⃣ **Monitor Central (Status)**

```
┌──────────────────────────────────────────────────────────┐
│  EN VIVO  │   NOMBRE ENTRADA (vMix actual)      │ 15:23:47 │
│  AUTO: ON │  PRÓX. PROG: Input 5 @ 15:30:00    │          │
│           │  PRÓX. TANDA: Lista 15 @ 16:00:00  │          │
└──────────────────────────────────────────────────────────┘
```

**Campos:**
- **EN VIVO:** Entrada que está reproduciendo actualmente en vMix
- **AUTO: ON/OFF:** Estado del sistema de automatización
  - Verde/ON = Ejecuta eventos automáticamente
  - Rojo/OFF = Modo manual (solo controles manuales)
- **Reloj:** Hora actual con precisión de segundos
- **PRÓX. PROGRAMA:** Siguiente programa programado (hora + tiempo restante)
- **PRÓX. TANDA:** Siguiente tanda publicitaria (hora + tiempo restante)

### 6️⃣ **Monitoreo en Tiempo Real**

Durante ejecución de tanda, el monitor muestra:

```
┌─ ENTRADA ACTUAL: Lista 15
├─ PROCESO DE TANDA: 02:15 (Lista 15, 4 spots)
├─ VOLVIENDO A: Entrada 5
└─ Estado: En progreso...
```

Actualización: Cada 1 segundo

### 7️⃣ **Niveles de Audio (VU Meter)**

- Monitoreo en tiempo real del master audio de vMix
- Barras L/R (left/right) en el footer
- Color cian (#00f2ff) para indicador visual
- Rango: 0.0 (silencio) a 1.0 (máximo)

---

## 📋 Requisitos del Sistema

### Mínimos
- **Windows 10** o **Windows 11** (64-bit recomendado)
- **2 GB RAM**
- **500 MB libre en disco** (más la base de datos de eventos)
- **Conexión de red** a vMix

### Recomendados
- **Windows 11** (64-bit)
- **4 GB+ RAM**
- **1 GB libre en disco**
- **Conexión Ethernet** (mejor que WiFi para latencia)

### Dependencias Internas (incluidas en .exe)
- PySide6 6.11.0 (GUI)
- requests 2.31.0 (HTTP)
- Python 3.10+ (runtime)

---

## 🚀 Instalación y Uso

### Opción 1: Executable Portable (RECOMENDADO)

```bash
1. Descargar: dist/vMix_Schedule_44/
2. Copiar a carpeta deseada o USB
3. Ejecutar: vMix_Schedule_44.exe
4. ¡Listo! (sin instalación requerida)
```

**Ventajas:**
- ✅ Sin instalación
- ✅ Portátil (funciona en cualquier carpeta/USB)
- ✅ Tamaño: ~250 MB
- ✅ Standalone (incluye todas las librerías)

### Opción 2: Desde Python (Mac/Linux)

```bash
# Pre-requisitos: Python 3.10+

# 1. Clonar/descargar proyecto
cd /ruta/al/proyecto

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# o
venv\Scripts\activate.bat  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python3 main.py
```

### Opción 3: Compilar .exe Personalizado

```bash
# En Windows:
BUILD_BRANDED.bat

# O con Python (cualquier OS):
python build_branded.py
```

---

## ⚙️ Configuración

### Archivo: `vMix_Schedule_44_Contenidos_Config.json`

```json
{
    "PUBLIS_POR_BLOQUE": 4,
    "INICIO_PUBLIS_INPUT": "14",
    "PUBLIS_LISTA_ID": "15",
    "CIERRE_PUBLIS_INPUT": "16",
    "FADE_DURATION_MS": 500,
    "PUBLIS_CLIP_TIMEOUT": 300,
    "INICIO_PUBLIS_TIMEOUT": 11,
    "CIERRE_PUBLIS_TIMEOUT": 5
}
```

**Parámetros:**
- `PUBLIS_POR_BLOQUE`: Número de spots por tanda (1-20)
- `INICIO_PUBLIS_INPUT`: ID entrada jingle inicio (recomendado: 14)
- `PUBLIS_LISTA_ID`: ID lista de spots en vMix (recomendado: 15)
- `CIERRE_PUBLIS_INPUT`: ID entrada jingle cierre (recomendado: 16)
- `FADE_DURATION_MS`: Duración fade en milisegundos (recomendado: 500ms)
- `PUBLIS_CLIP_TIMEOUT`: Timeout máximo por spot (segundos)
- `INICIO_PUBLIS_TIMEOUT`: Timeout jingle inicio (segundos)
- `CIERRE_PUBLIS_TIMEOUT`: Timeout jingle cierre (segundos)

### Archivo: `vMix_Schedule_44_Contenidos_DB.json`

```json
{
    "programas": {
        "Lunes": [
            {"time": "10:00:00", "name": "5"},
            {"time": "11:00:00", "name": "7"}
        ],
        "Martes": [],
        ...
    },
    "tandas": {
        "Lunes": [
            {"time": "10:45:00", "list_id": "15", "spots": 4},
            {"time": "11:45:00", "list_id": "15", "spots": 3}
        ],
        ...
    }
}
```

---

## 🎯 Casos de Uso

### 1. **Transmisión de TV en Vivo**
```
10:00:00 → Programa deportivo (Input 5)
10:45:00 → Tanda publicitaria (4 spots, 3 minutos)
10:48:00 → Vuelve programa (Input 5)
12:00:00 → Programa de noticias (Input 8)
12:45:00 → Tanda publicitaria (4 spots, 3 minutos)
```

### 2. **Evento en Vivo con Transiciones Automáticas**
```
14:00:00 → Entrada del evento (Input 12)
14:15:00 → Banda en vivo (Input 15)
14:45:00 → Publicidades (Tanda de 4 spots)
14:48:00 → Cierre (Input 18)
```

### 3. **Transmisión 24/7 Automatizada**
- Programar toda la semana
- Activar AUTO: ON
- Sistema ejecuta eventos sin intervención
- Fallback manual con botón "EN VIVO"

---

## 🔒 Seguridad y Confiabilidad

### Mecanismos de Protección

1. **Thread Safety**
   - Lock global (_tanda_lock) previene condiciones de carrera
   - Un solo bloque de tanda simultáneo

2. **Detección de Errores**
   - Reintentos automáticos con backoff exponencial
   - Timeouts dinámicos basados en duración real
   - Fallback a duración aproximada si falla detección

3. **Logging Completo**
   - Archivo: `schedule_log.txt`
   - Timestamp en cada operación
   - Nivel de detalle: DEBUG, INFO, WARNING, ERROR
   - Facilita debugging y auditoría

4. **Persistencia de Datos**
   - Base de datos JSON (formato estándar)
   - Respaldos automáticos
   - Compatible con control de versiones

---

## 📊 Arquitectura Técnica

### Componentes Principales

```
┌─────────────────────────────────────────────┐
│       vMix Schedule 44 (GUI Principal)      │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  AMixTVPro (QMainWindow)             │  │
│  │  - UI layout (1200x850px)            │  │
│  │  - Event management                  │  │
│  │  - Database I/O                      │  │
│  └──────────────────────────────────────┘  │
│           ↑              ↓                  │
│  ┌──────────────────────────────────────┐  │
│  │  Threads (daemon)                    │  │
│  │  - vmix_monitor()   (100ms updates)  │  │
│  │  - system_tick()    (1000ms events)  │  │
│  │  - execute_tanda()  (4-step block)   │  │
│  └──────────────────────────────────────┘  │
│           ↑              ↓                  │
│  ┌──────────────────────────────────────┐  │
│  │  vMix HTTP API Layer                 │  │
│  │  - call_vmix() (with retry logic)    │  │
│  │  - esperar_fin_reproduccion()        │  │
│  │  - obtener_estado_completo()         │  │
│  └──────────────────────────────────────┘  │
│           ↓              ↑                  │
└─────────────────────────────────────────────┘
            ↕
        vMix HTTP API
    (192.168.192.140:8098)
```

### Tecnologías Utilizadas

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| GUI | PySide6 | 6.11.0 |
| HTTP Client | requests | 2.31.0 |
| XML Parser | xml.etree.ElementTree | Built-in |
| Threading | threading | Built-in |
| Base de Datos | JSON | Built-in |
| Runtime | Python | 3.10+ |

---

## 📈 Métricas y Performance

### Tiempos de Ejecución Típicos

| Operación | Tiempo Típico |
|-----------|----------------|
| Fade entre inputs | 500ms + transición |
| Detección fin video | 100ms (cada check) |
| Tanda 4 spots (46s c/u) | ~187.5 segundos |
| Monitor UI update | 100ms |
| Scheduler check | 1000ms |
| Retry con backoff | 1.5s × intento |

### Uso de Recursos

| Recurso | Consumo Típico |
|---------|----------------|
| RAM | 100-200 MB (idle) |
| CPU | <5% (idle) |
| Conexión | ~1 MB/min (queries API) |
| Disco | 1-50 MB (DB + logs) |

---

## 🐛 Troubleshooting

### Problema: "Conexión rechazada a vMix"

**Solución:**
1. Verificar vMix corriendo en http://192.168.192.140:8098
2. Verificar firewall permite conexión local
3. Cambiar IP en código si vMix está en otro servidor

```python
# main.py línea 22
VMIX_URL = 'http://192.168.192.140:8098/api/'
```

### Problema: "Tanda no se ejecuta automáticamente"

**Solución:**
1. Verificar AUTO: ON (botón debe estar verde)
2. Verificar hora exacta sincronizada en sistema
3. Verificar evento creado correctamente en UI
4. Revisar `schedule_log.txt` para errores

### Problema: "Spots se cortan o no se reproducen"

**Solución:**
1. Verificar IDs de input en configuración
2. Aumentar PUBLIS_CLIP_TIMEOUT en config
3. Verificar lista tiene suficientes spots
4. Revisar logs para timeouts específicos

### Problema: "El .exe no inicia"

**Solución:**
1. Instalar Visual C++ Redistributable (2019+)
   https://support.microsoft.com/help/2977003
2. Ejecutar en terminal para ver error específico
3. Verificar Python 3.10+ instalado (para versión script)
4. Revisar permisos de carpeta (Write access)

---

## 📝 Mantenimiento

### Archivos Generados

```
proyecto/
├── schedule_log.txt                          # Log de operaciones
├── vMix_Schedule_44_Contenidos_Config.json   # Configuración
├── vMix_Schedule_44_Contenidos_DB.json       # Base de datos eventos
└── app_icon.png                              # Logo integrado
```

### Limpieza Recomendada

```bash
# Limpiar logs antiguos (mantener últimos 7 días)
# Respaldar config antes de cambios importantes
# Revisar DB cada 2-3 meses por eventos obsoletos
```

### Actualización

1. Descargar nueva versión
2. Respaldar `vMix_Schedule_44_Contenidos_DB.json`
3. Respaldar `vMix_Schedule_44_Contenidos_Config.json`
4. Reemplazar ejecutable
5. Restaurar archivos JSON
6. Probar funcionamiento

---

## 🎓 Capacitación

### Para Operadores

1. **Interfaz Básica:** 5 minutos
   - Agregar/editar/eliminar eventos
   - Encender/apagar AUTO
   - Botón EN VIVO para control manual

2. **Configuración Simple:** 5 minutos
   - Cambiar cantidad de spots
   - Ajustar jingles (IDs de input)
   - Aplicar cambios

3. **Troubleshooting Rápido:** 10 minutos
   - Cómo reconocer errores comunes
   - Cuándo usar modo manual
   - Contactar soporte

### Para Técnicos

1. **Instalación:** 15 minutos
   - Descargar/compilar .exe
   - Configurar IP de vMix
   - Probar conectividad

2. **Configuración Avanzada:** 30 minutos
   - Editar JSON directamente
   - Ajustar timeouts
   - Optimizar para setup específico

3. **Mantenimiento:** Mensual
   - Revisar logs
   - Limpiar datos obsoletos
   - Actualizar si hay nuevas versiones

---

## 📞 Soporte y Contacto

### Documentación
- README_BRANDED_EXE.md - Instrucciones de compilación
- INSTALL_WINDOWS.md - Guía completa de instalación
- schedule_log.txt - Historial de operaciones

### Desarrollo
**Desarrollador:** IGNACE  
**Branding:** 44 Contenidos  
**Tecnología:** Python + PySide6 + vMix API

---

## 📄 Especificaciones de Versión

| Item | Detalle |
|------|---------|
| **Versión** | 1.0 Branded |
| **Compilada** | 4 de mayo de 2026 |
| **Estado** | Production Ready |
| **Licencia** | Propietaria (44 Contenidos) |
| **Soporte** | 12 meses |
| **Garantía** | Funcionalidad core |

---

## ✅ Checklist de Deployment

Antes de usar en producción:

- [ ] vMix instalado y funcionando
- [ ] Dirección IP de vMix confirmada
- [ ] IDs de inputs configurados correctamente
- [ ] Lista de spots creada en vMix (con mínimo 1 spot)
- [ ] Jingles de entrada y cierre cargados
- [ ] Eventos programados al menos 1 hora adelante
- [ ] AUTO activado (si se desea automatización)
- [ ] Monitor de status visible
- [ ] Reloj del sistema sincronizado (NTP)
- [ ] Logs monitoreados primera hora

---

## 🎉 Conclusión

**vMix Schedule 44** es una solución completa, profesional y confiable para la automatización de transmisiones televisivas. Diseñado con seguridad, precisión y facilidad de uso en mente.

**Características que destacan:**
- ✨ Automatización completa e inteligente
- 🔒 Thread-safe y altamente confiable
- 📊 Monitoreo en tiempo real
- 🎨 Interfaz moderna y profesional
- 🚀 Portátil (funciona en cualquier Windows)
- 📈 Escalable (fácil de extender)

**Gracias por usar vMix Schedule 44. Powered by IGNACE. Branded by 44 Contenidos.** 🎬

---

**Documento generado:** 4 de mayo de 2026  
**Versión:** 1.0  
**Clasificación:** Público
