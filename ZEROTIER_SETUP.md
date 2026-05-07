# 🔧 Configuración con ZeroTier

Si el servidor TrueNAS está conectado a ZeroTier para acceder a vMix, sigue estos pasos:

## 1️⃣ Obtener IP de ZeroTier de vMix

En la máquina donde corre vMix (Windows/Linux):
```bash
# Linux/Mac
ip addr show | grep zt

# Windows (desde PowerShell Admin)
ipconfig | findstr "ZeroTier"
```

**Resultado esperado:** Una IP tipo `10.147.x.x.x` o `172.22.x.x`

## 2️⃣ Configurar en vMix Schedule 44

1. Abre `http://192.168.192.44:8080`
2. En el campo **"📡 VMIX URL (ZeroTier/LAN):"** ingresa:
   ```
   http://10.147.X.X.X:8098/api/
   ```
   (Reemplaza `10.147.X.X.X` con la IP de ZeroTier real)

3. Presiona **APLICAR**
4. Presiona **🔧 TEST** para verificar conectividad
   - Mostrará el DNS resolution y error específico si falla

## 3️⃣ Si falla: Pasos de diagnóstico

El botón TEST mostrará:
- **URL:** La dirección que está usando
- **DNS:** Si resuelve el hostname/IP
- **Error:** Razón específica del fallo

### Causas comunes:

| Error | Causa | Solución |
|-------|-------|----------|
| `No resolve` | Hostname/IP incorrecto | Verifica IP de ZeroTier |
| `connection_error` | vMix no responde | ¿vMix está corriendo? ¿Puerto 8098? |
| `timeout` | Red lenta o bloqueada | Verifica conectividad ZeroTier |
| `error... No suitable Function` | vMix conecta pero no entiende | Verifica que sea URL `/api/` |

## 4️⃣ Verificar conectividad ZeroTier desde TrueNAS

```bash
# SSH a TrueNAS
ping 10.147.X.X.X  # Debería responder

# Probar vMix directamente
curl http://10.147.X.X.X:8098/api/?Function=GetStatus
```

## 5️⃣ Ips alternativas

Si tienes **multiple interfaces** (local + ZeroTier):
- **Preferir ZeroTier** si está disponible (más seguro)
- **IP local** si están en la misma LAN física
- **Hostname** si ambos sistemas lo resuelven

---

**Ejemplo real:**
- vMix en Windows: IP ZeroTier = `10.147.20.15`
- TrueNAS: IP ZeroTier = `10.147.50.30`
- URL a usar: `http://10.147.20.15:8098/api/`
