# 🔧 Configuración con VPN/ZeroTier

Si el servidor TrueNAS está conectado a VPN/ZeroTier para acceder a vMix, sigue estos pasos:

## 📌 Configuración actual

**IP de vMix (por VPN):** `192.168.192.140:8098`
**Endpoint correcto:** `http://192.168.192.140:8098/` (SIN `/api/`)

⚠️ **IMPORTANTE:** La URL NO debe incluir `/api/` al final - vMix no reconoce ese endpoint.

Esta configuración ya está **preconfigurada por defecto** en el sistema.

## ✅ Verificar conexión

1. Abre `http://192.168.192.44:8080` en el navegador
2. Presiona el botón **🔧 TEST** en la sección de configuración
3. Si dice **"✅ vMix CONECTADO"** → ¡Sistema listo!
4. Si dice **"❌"** → Revisa los detalles del error

## 🔍 Si necesitas cambiar la IP

1. En el campo **"📡 VMIX URL:"** ingresa la nueva dirección:
   - ✅ Correcto: `http://10.147.X.X:8098/` o `http://192.168.X.X:8098/`
   - ❌ Incorrecto: `http://10.147.X.X:8098/api/` (no agregar /api/)

2. Presiona **APLICAR**
3. Presiona **🔧 TEST** para verificar

El sistema normaliza automáticamente la URL y quita `/api/` si lo incluyes.

## 🛠️ Diagnóstico desde línea de comandos

En TrueNAS (SSH):
```bash
# Script automático completo
bash /mnt/vmix-schedule-44/test-vmix-connection.sh

# O pruebas manuales:
curl http://192.168.192.140:8098/?Function=GetStatus
```

## 📋 Respuesta esperada de vMix

La API de vMix devuelve XML:
```xml
<?xml version="1.0" encoding="utf-8"?>
<vmix>
  <version>23.x.x.x</version>
  <edition>...</edition>
  ...
</vmix>
```

Si ves "No suitable Function" significa que la URL `/api/` está incorrecta.

---

**Sistema preconfigurado y listo. URL: `http://192.168.192.140:8098/` (sin /api/)**


