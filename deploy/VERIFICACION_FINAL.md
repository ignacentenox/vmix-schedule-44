# ✅ VERIFICACIÓN FINAL - vMix Schedule 44 en TrueNAS

## 📋 Checklist Post-Deploy

### 1. **Servicios Ejecutándose**
```bash
# Verificar que ambos servicios están activos (debe mostrar "active (running)")
sudo systemctl status vmix-schedule-44
sudo systemctl status nginx
```

**Resultado esperado:**
```
● vmix-schedule-44.service - vMix Schedule 44 API
   Loaded: loaded
   Active: active (running)
```

---

### 2. **Conectividad a vMix**
En la interfaz web (`http://192.168.192.44/ui/`), el indicador debe mostrar:
- ✅ Punto verde = **"vMix Conectado"** 
- ❌ Punto rojo = **"vMix Desconectado"** (verifica que vMix esté en 192.168.192.140:8098)

---

### 3. **API Respondiendo**
```bash
# Probar endpoint de status
curl -s http://127.0.0.1:5000/api/status | python3 -m json.tool
```

**Resultado esperado:**
```json
{
  "auto_enabled": true,
  "tanda_en_progreso": false,
  "timestamp": "2026-05-06T19:30:45.123456",
  "vmix": "Conectado"
}
```

---

### 4. **Nginx Sirviendo Interfaz**
```bash
# Debe mostrar HTML (comienza con "<!DOCTYPE html>")
curl -s http://192.168.192.44/ui/ | head -5
```

---

### 5. **Archivos de Datos Creados**
```bash
# Ver estructura de directorios
ls -la /opt/vmix-schedule-44/
ls -la /opt/vmix-schedule-44/data/
```

**Debe contener:**
```
-rw-r--r--  vMix_Schedule_44_Contenidos_Config.json
-rw-r--r--  vMix_Schedule_44_Contenidos_DB.json
```

---

### 6. **Logs del Sistema**
```bash
# Ver últimas 20 líneas de logs
sudo tail -20 /opt/vmix-schedule-44/logs/api.log
```

**Debe contener líneas como:**
```
2026-05-06 19:30:45,123 - INFO - 🚀 vMix Schedule 44 API iniciada
```

---

## 🚨 Troubleshooting

### **Problema: "vMix Desconectado"**
```bash
# Verificar conectividad a vMix
curl -s http://192.168.192.140:8098/api/ | head -5
```
- Si falla: vMix no está accesible desde TrueNAS
- Solución: Verificar IP 192.168.192.140:8098 en vMix

### **Problema: Nginx no sirve interfaz**
```bash
sudo systemctl restart nginx
sudo tail -f /var/log/nginx/vmix-schedule-44-error.log
```

### **Problema: API no responde**
```bash
sudo systemctl restart vmix-schedule-44
sudo tail -f /opt/vmix-schedule-44/logs/api.log
```

### **Problema: Permiso denegado**
```bash
sudo chown -R root:root /opt/vmix-schedule-44
sudo chmod -R 755 /opt/vmix-schedule-44
```

---

## 🎯 Acceso Final

| Item | Valor |
|------|-------|
| **URL Web** | http://192.168.192.44/ui/ |
| **API Backend** | http://192.168.192.44/api/ |
| **Logs** | `/opt/vmix-schedule-44/logs/api.log` |
| **Config** | `/opt/vmix-schedule-44/data/vMix_Schedule_44_Contenidos_Config.json` |
| **Base Datos** | `/opt/vmix-schedule-44/data/vMix_Schedule_44_Contenidos_DB.json` |

---

## ✨ Características Disponibles

- ✅ Monitor vMix en tiempo real
- ✅ Control AUTO ON/OFF
- ✅ Agregar eventos por día/hora
- ✅ Gestión de tandas publicitarias
- ✅ Ver logs en vivo
- ✅ API REST para integraciones
- ✅ Interfaz responsive
- ✅ Autostart al reiniciar servidor

---

## 🔄 Próximos Pasos

1. **Agregar primer evento:**
   - Abre http://192.168.192.44/ui/
   - Click en pestaña "Eventos"
   - Ingresa: Día="Monday", Hora="14:30", Input="1"
   - Click "Agregar"

2. **Activar automatización:**
   - Click botón "AUTO: OFF" para cambiar a "AUTO: ON"
   - El sistema ejecutará eventos automáticamente

3. **Monitorear:**
   - Ver logs en tiempo real en pestaña "Logs"
   - Verificar estado de vMix (punto verde/rojo)

---

**Última actualización:** 6 de mayo de 2026
**Versión:** vMix Schedule 44 v1.0 TrueNAS
