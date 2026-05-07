# 🔧 Configuración de vMix

## ⚡ Configuración rápida

**URL vMix correcta:** `http://192.168.192.140:8098/`

⚠️ **IMPORTANTE:** NO incluir `/api/` - vMix rechaza ese endpoint

## ✅ Verificar en la UI

1. Abre `http://192.168.192.44:8080`
2. Presiona **🔧 TEST** en configuración
3. Si dice ✅ "Conectado" → Listo!

## 🔄 Cambiar URL

Si necesitas otra IP:
1. Campo "📡 VMIX URL:" → Ingresa nueva dirección
2. Presiona **APLICAR**
3. Presiona **🔧 TEST**

**Ejemplos válidos:**
- `http://192.168.192.140:8098/`
- `http://10.147.20.15:8098/`
- `http://vmix-server.local:8098/`

**Formato inválido:**
- ❌ `http://192.168.192.140:8098/api/`

## 📋 Diagnóstico desde línea de comandos

```bash
# En TrueNAS (SSH)
bash /mnt/vmix-schedule-44/test-vmix-connection.sh

# O manual:
curl http://192.168.192.140:8098/?Function=GetStatus
```

## 🛠️ Si falla:

1. **"No suitable Function"** → URL tiene `/api/` (quítalo)
2. **"Connection refused"** → vMix no está corriendo
3. **"Timeout"** → Red lenta o bloqueada
4. **"Cannot resolve host"** → IP/hostname incorrecto

---

**Sistema listo con URL correcta: `http://192.168.192.140:8098/`**

