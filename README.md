# vMix Schedule 44

Sistema de programación automática para vMix con interfaz web.

## 🚀 Instalación Rápida (TrueNAS)

```bash
curl -fsSL https://raw.githubusercontent.com/ignacentenox/vmix-schedule-44/main/install.sh | sudo sh
```

Acceso: **http://192.168.192.44/ui/**

## 📋 Requisitos

- TrueNAS / FreeBSD / Linux
- Python 3.9+
- Nginx

## ✨ Características

- Monitor en tiempo real
- Programación de eventos
- Control automático
- Tandas publicitarias
- API REST
- JSON persistencia

## 📖 Documentación

Ver archivo `install.sh` para detalles técnicos.

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
