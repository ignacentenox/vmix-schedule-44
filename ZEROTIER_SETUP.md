# 🔧 Configuración con VPN/ZeroTier

Si el servidor TrueNAS está conectado a VPN/ZeroTier para acceder a vMix, sigue estos pasos:

## 📌 Configuración actual

**IP de vMix (por VPN):** `192.168.192.140:8098`

Esta IP ya está **preconfigurada por defecto** en el sistema.

## ✅ Verificar conexión

1. Abre `http://192.168.192.44:8080` en el navegador
2. Presiona el botón **🔧 TEST** en la sección de configuración
3. Si dice **"✅ vMix CONECTADO"** → ¡Sistema listo!
4. Si dice **"❌"** → Revisa los detalles del error

## 🔍 Si necesitas cambiar la IP

1. En el campo **"📡 VMIX URL (ZeroTier/LAN):"** ingresa la nueva dirección
2. Presiona **APLICAR**
3. Presiona **🔧 TEST** para verificar

## 🛠️ Diagnóstico detallado

El botón TEST muestra:
- **URL:** La dirección que está usando
- **DNS:** Si la IP resuelve correctamente  
- **Error:** Razón específica si falla

### Causas comunes de error:

| Error | Causa | Solución |
|-------|-------|----------|
| `Connection refused` | vMix no está corriendo | Verifica que vMix esté ejecutándose |
| `timeout` | Red VPN lenta o caída | Verifica conexión VPN/ZeroTier |
| `error... No suitable Function` | vMix conecta pero URL mal | Verifica `/api/` al final de URL |

## 📋 Verificar desde TrueNAS (SSH)

```bash
# Probar conectividad a vMix
curl http://192.168.192.140:8098/api/?Function=GetStatus

# Ver logs de la API
tail -f /mnt/vmix-schedule-44/logs/api.log
```

---

**Sistema preconfigurado y listo. La URL `http://192.168.192.140:8098/api/` ya está activa.**

