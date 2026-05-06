# vMix Schedule 44 - Web Control Panel

Aplicación profesional de control de vMix con interfaz web moderna. Automatiza la programación de entrada, gestiona tandas publicitarias y controla la reproducción desde cualquier navegador.

🌐 **Demo:** http://192.168.192.44/ui/

---

## ✨ Características

- ✅ **Monitor en tiempo real** - Entrada actual, hora, estado de vMix
- ✅ **Gestión de eventos** - Programar cambios de entrada por día/hora
- ✅ **Control automático** - Activar/desactivar automatización con un botón
- ✅ **Tandas publicitarias** - Ejecutar jingles y spots automáticamente
- ✅ **Logs en vivo** - Seguimiento de todas las acciones
- ✅ **API REST** - Integración con sistemas externos
- ✅ **Interfaz moderna** - Responsive, tema profesional, acceso móvil
- ✅ **Autostart** - Se reinicia automáticamente con el servidor
- ✅ **JSON persistencia** - Guardar eventos sin base de datos

---

## 🚀 Instalación Rápida (1 línea)

### Opción 1: Instalación Automática (Recomendado)

En la shell de TrueNAS:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ignaciomanuel/vmix-schedule-44/main/install.sh)
```

Eso es todo. El script:
- Descarga desde GitHub
- Instala dependencias (Python, Nginx)
- Configura servicio automático
- Inicia aplicación
- Accesible en http://192.168.192.44/ui/

### Opción 2: Instalación Manual

```bash
# Clonar repositorio
git clone https://github.com/ignaciomanuel/vmix-schedule-44.git /opt/vmix-schedule-44
cd /opt/vmix-schedule-44

# Instalar dependencias
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar Nginx
sudo cp deploy/nginx.conf /usr/local/etc/nginx/vmix-schedule-44.conf

# Crear servicio
sudo cp deploy/vmix-schedule-44.service /etc/systemd/system/

# Iniciar
sudo systemctl daemon-reload
sudo systemctl enable vmix-schedule-44
sudo systemctl start vmix-schedule-44
sudo systemctl start nginx
```

---

## 📋 Requisitos

- **Sistema**: TrueNAS, FreeBSD, o Linux
- **Python**: 3.9+
- **Servidor Web**: Nginx (instalado automáticamente)
- **vMix**: Accesible en red (ej: 192.168.192.140:8098)

---

## 🎯 Uso

### 1. Abrir Interfaz Web

```
http://192.168.192.44/ui/
```

### 2. Agregar Evento

- Pestaña "Eventos"
- Día: `Monday`
- Hora: `14:30`
- Input: `1` (número de entrada en vMix)
- Click "Agregar"

### 3. Activar Automatización

- Click botón `AUTO: OFF` → cambia a `AUTO: ON`
- Sistema ejecutará eventos automáticamente

### 4. Monitorear

- Pestaña "Logs" muestra todas las acciones en tiempo real
- Indicador verde/rojo muestra estado de vMix

---

## 🔌 API REST

Endpoints disponibles:

```bash
# Ver estado
curl http://192.168.192.44/api/status

# Obtener eventos
curl http://192.168.192.44/api/events

# Agregar evento
curl -X POST http://192.168.192.44/api/events \
  -H "Content-Type: application/json" \
  -d '{"day":"Monday","time":"14:30","name":"1"}'

# Activar/desactivar AUTO
curl -X POST http://192.168.192.44/api/auto/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled":true}'

# Ver logs
curl http://192.168.192.44/api/logs
```

---

## 🔧 Configuración

### Archivo de Configuración

`/opt/vmix-schedule-44/data/vMix_Schedule_44_Contenidos_Config.json`

```json
{
  "VMIX_HOST": "192.168.192.140",
  "VMIX_PORT": 8098,
  "PUBLIS_POR_BLOQUE": 4,
  "FADE_DURATION_MS": 500
}
```

### Base de Datos de Eventos

`/opt/vmix-schedule-44/data/vMix_Schedule_44_Contenidos_DB.json`

```json
{
  "programas": {
    "Monday": [
      {"time": "14:30:00", "name": "1"}
    ]
  },
  "tandas": {}
}
```

---

## 🛠️ Comandos Útiles

```bash
# Ver estado del servicio
sudo systemctl status vmix-schedule-44

# Ver logs en vivo
sudo tail -f /opt/vmix-schedule-44/logs/api.log

# Reiniciar aplicación
sudo systemctl restart vmix-schedule-44

# Parar aplicación
sudo systemctl stop vmix-schedule-44

# Iniciar aplicación
sudo systemctl start vmix-schedule-44

# Ver nginx logs
sudo tail -f /var/log/nginx/vmix-schedule-44-error.log
```

---

## 📂 Estructura del Proyecto

```
vmix-schedule-44/
├── api.py                          # Backend Flask
├── requirements.txt                # Dependencias Python
├── install.sh                      # Script instalación automática
├── frontend/
│   └── index.html                  # Interfaz web
├── deploy/
│   ├── nginx.conf                  # Configuración Nginx
│   ├── vmix-schedule-44.service    # Servicio systemd
│   └── README_DEPLOY.md            # Documentación deploy
├── data/                           # Archivos de datos (creados en runtime)
│   ├── vMix_Schedule_44_Contenidos_Config.json
│   └── vMix_Schedule_44_Contenidos_DB.json
└── README.md                       # Este archivo
```

---

## 🐛 Troubleshooting

### "vMix Desconectado"

```bash
# Verificar conectividad
curl -s http://192.168.192.140:8098/api/ | head -5
```

Si falla, vMix no es accesible desde TrueNAS. Verificar:
- IP correcta (192.168.192.140)
- Puerto correcto (8098)
- Firewall permite conexión

### "No se puede acceder a la interfaz"

```bash
# Verificar Nginx
sudo systemctl status nginx
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx
```

### "Error de permisos"

```bash
sudo chown -R root:root /opt/vmix-schedule-44
sudo chmod -R 755 /opt/vmix-schedule-44
```

---

## 🏗️ Arquitectura

```
Navegador (http://192.168.192.44/ui/)
    ↓
Nginx (Puerto 80)
├── /ui/   → Frontend estático (HTML/CSS/JS)
└── /api/  → Proxy a backend
    ↓
Flask API (Puerto 5000, interno)
├── Scheduler automático
├── Gestión de eventos
└── Integración vMix
    ↓
vMix HTTP API (192.168.192.140:8098)
├── SelectIndex (cambiar entrada)
├── Fade/Cut (transiciones)
└── XML Status (obtener estado)
```

---

## 📊 Estadísticas

- **Backend**: Python 3.9 + Flask 2.3.0
- **Frontend**: HTML5 + CSS3 + Vanilla JS
- **Servidor Web**: Nginx 1.x
- **Base de Datos**: JSON (sin dependencias externas)
- **Tamaño**: ~50 MB (con venv)
- **Memoria**: ~100-150 MB en idle
- **CPU**: Mínimo (scheduler ejecuta cada segundo)

---

## 🔐 Seguridad

- ✅ Validación de entrada en API
- ✅ Rate limiting en scheduler
- ✅ Logging de todas las acciones
- ✅ Archivo de configuración protegido
- ⚠️ Sin autenticación (usar en red privada)

---

## 📝 Licencia

MIT License - Libre para usar, modificar y distribuir

---

## 👨‍💻 Autor

**IGNACE** - vMix Schedule 44
- Versión 1.0 | Mayo 2026
- Sistema profesional de automatización para vMix en TrueNAS

---

## 🤝 Soporte

¿Problemas? Revisa:
1. [Troubleshooting](#-troubleshooting)
2. Logs: `sudo tail -f /opt/vmix-schedule-44/logs/api.log`
3. Issues en GitHub

---

## 🚀 Próximas Características (Roadmap)

- [ ] Autenticación y multi-usuario
- [ ] Programación de tandas avanzada
- [ ] Estadísticas y reportes
- [ ] API Webhook para integraciones
- [ ] Panel móvil nativo (PWA)
- [ ] Soporte para múltiples instancias de vMix

---

## ⚡ Quick Start

```bash
# 1. Instalar (1 línea en shell de TrueNAS)
bash <(curl -fsSL https://raw.githubusercontent.com/ignaciomanuel/vmix-schedule-44/main/install.sh)

# 2. Abrir navegador
# http://192.168.192.44/ui/

# 3. Agregar evento
# Día: Monday, Hora: 14:30, Input: 1

# 4. Activar AUTO
# Click "AUTO: ON"

# 5. ¡Listo!
```

---

**Hecho con ❤️ para vMix**
