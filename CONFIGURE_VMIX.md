# 🔧 Cómo encontrar y configurar la URL de vMix

## Paso 1: Encontrar la IP y puerto de vMix

### En Windows (donde corre vMix):
1. **Abre vMix**
2. Ve a **Tools** → **Web Controller**
3. Verás algo como:
   ```
   http://localhost:8098
   o
   http://192.168.192.140:8098
   ```

### Encontrar IP correcta de la máquina con vMix:
- En Windows: Abre `cmd` y escribe `ipconfig`
- Busca la línea que dice `IPv4 Address`
- Ejemplo: `192.168.192.140`
- Puerto de vMix: `8098` (es el puerto por defecto)

**Resultado final: `http://192.168.192.140:8098/api/`**
(Nota el `/api/` al final)

---

## Paso 2: Configurar en vMix Schedule 44

### Desde TrueNAS (en el navegador):

1. **Abre** `http://192.168.192.44:8080`

2. **Mira la sección de Configuración** (parte superior azul/gris):

   ```
   ┌─────────────────────────────────────────────────┐
   │ VMIX URL: [_____________________] 🔧 TEST VMIX  │
   │ SPOTS: [4]  JINGLE IN: [14]  JINGLE OUT: [16]   │
   │                         [APLICAR]                │
   └─────────────────────────────────────────────────┘
   ```

3. **Ingresa** la URL completa de vMix en el campo "VMIX URL":
   - Ejemplo: `http://192.168.192.140:8098/api/`

4. **Presiona el botón "🔧 TEST VMIX"** para verificar:
   - ✅ Si sale "vMix CONECTADO" → ¡Listo!
   - ❌ Si sale "No conecta" → Revisa IP y puerto

5. **Presiona "APLICAR"** para guardar

---

## Paso 3: Verificar conectividad desde TrueNAS

Si el test falla, puedes verificar manualmente desde TrueNAS:

```bash
# SSH a TrueNAS y ejecuta:
curl http://192.168.192.140:8098/api/?Function=GetStatus

# Si funciona, debería retornar XML con el estado
# Si falla, la URL no es correcta
```

---

## 🚨 Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `Connection refused` | vMix no está corriendo | Abre vMix en Windows |
| `Cannot resolve host` | IP incorrecta | Verifica IP en `ipconfig` |
| `Timeout` | Firewall bloqueando | Desactiva firewall entre máquinas o abre puerto 8098 |
| `Connection timed out` | Red no conectada | Verifica que ambas máquinas estén en la misma red |

---

## 💡 Tips

- **Si no sabes la IP**, puedes usar hostname:
  - `http://nombre-pc:8098/api/`
  - Donde `nombre-pc` es el nombre de tu computadora

- **Puedes cambiar la URL en cualquier momento**:
  - Solo ingresa la nueva URL
  - Presiona APLICAR
  - No necesita reiniciar nada

- **Para probar desde Windows**:
  - Abre navegador en Windows
  - Ve a `http://192.168.192.44:8080`
  - Debería cargar la interfaz azul

---

**¿Necesitas ayuda?** Ejecuta en TrueNAS:
```bash
sudo systemctl status vmix-schedule-44
sudo journalctl -u vmix-schedule-44 -n 20
```
