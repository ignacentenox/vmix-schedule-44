# vMix Schedule 44 - Guía de Instalación Windows

## 📋 Requisitos Previos

- **Windows 10 / Windows 11** (64-bit recomendado)
- **Python 3.8+** instalado con PATH configurado
- **vMix** ejecutándose en `http://192.168.192.140:8098`

## 🚀 Opción 1: Ejecutable Portátil (Recomendado)

### Pasos:

1. **Descargar o clonar este proyecto**
   ```
   Los archivos deben estar en una carpeta accesible
   ```

2. **Doble clic en `BUILD.bat`**
   - Esto creará el entorno virtual
   - Instalará dependencias
   - Compilará el .exe portátil
   - Tomará ~5-10 minutos

3. **Ejecutar el programa**
   ```
   dist/vMix_Schedule_44/vMix_Schedule_44.exe
   ```

4. **(Opcional) Crear acceso directo**
   - Haz clic derecho en `vMix_Schedule_44.exe`
   - "Enviar a" → "Escritorio (crear acceso directo)"

### Ventajas:
✅ No requiere Python instalado  
✅ Totalmente portátil  
✅ Funciona en cualquier Windows 10/11  
✅ Puede guardarse en USB  

### Desventajas:
❌ Archivo más grande (~400MB)  
❌ Primera ejecución más lenta (descomprime archivos)

---

## 💻 Opción 2: Ejecutar desde Python (Desarrollo)

### Pasos:

1. **Instalar Python 3.8+**
   - Descarga desde: https://www.python.org/downloads/
   - ✅ **IMPORTANTE**: Marca "Add Python to PATH"

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar**
   ```bash
   python main.py
   ```

### Ventajas:
✅ Más rápido de actualizar  
✅ Menor tamaño en disco  
✅ Ideal para desarrollo  

### Desventajas:
❌ Requiere Python instalado  
❌ No es portátil  

---

## 🔧 Configuración Inicial

### 1. Configurar vMix
- Asegúrate que vMix esté ejecutándose
- API debe estar en: `http://192.168.192.140:8098`
- Inputs configurados:
  - **14**: Jingle Entrada
  - **15**: Publicidades (Lista vMix)
  - **16**: Jingle Cierre

### 2. Agregar Eventos
- Haz clic en "+ AGREGAR EVENTO"
- Selecciona día y hora
- Para PROGRAMACIÓN: Ingresa nombre del programa
- Para TANDAS: ID de lista y cantidad de spots

### 3. Activar AUTO Mode
- Haz clic en "AUTO: ON" para iniciar la automatización
- La aplicación ejecutará eventos según schedule

---

## 📁 Estructura de Archivos

```
scheduletv/
├── main.py                              # Script original (Mac)
├── main_windows.py                      # Script adaptado para Windows (rutas relativas)
├── requirements.txt                     # Dependencias Python
├── BUILD.bat                           # Script para crear .exe
├── vMix_Schedule_44_Contenidos_DB.json # Base de datos (se crea automáticamente)
└── vMix_Schedule_44_Contenidos_Config.json # Configuración
```

---

## 🐛 Troubleshooting

### Error: "Python no está instalado"
**Solución:**
1. Descarga Python desde: https://www.python.org/downloads/
2. Instala con opción "Add Python to PATH"
3. Reinicia tu PC
4. Intenta nuevamente

### Error: "No se conecta a vMix"
**Solución:**
1. Verifica que vMix esté ejecutándose
2. Comprueba la IP: `http://192.168.192.140:8098`
3. Si la IP es diferente, edita en `main_windows.py`:
   ```python
   VMIX_URL = 'http://TU_IP_AQUI:8098/api/'
   ```

### Error: "Los eventos no se ejecutan"
**Solución:**
1. Haz clic en "AUTO: ON" (debe estar verde)
2. Verifica que el sistema esté configurado como "EN VIVO"
3. Revisa que la hora actual coincida con el evento

### El .exe no se ejecuta
**Solución:**
1. Descarga Windows Visual C++ Redistributable:
   https://support.microsoft.com/en-us/help/2977003
2. Intenta desde terminal: `dist\vMix_Schedule_44\vMix_Schedule_44.exe`
3. Copia el error que aparece

---

## 📊 Uso

### Barra Superior
- **✓ APLICAR**: Guarda configuración

### Monitor Central
- **EN VIVO**: Entrada activa actual
- **AUTO: ON/OFF**: Activar/desactivar automatización
- **Reloj**: Hora actual del sistema
- **Próximos**: Próximo programa y próxima tanda

### Tablas
- **PROGRAMACIÓN / CONTENIDOS**: Eventos de programas
- **TANDAS / PUBLICIDAD**: Bloques publicitarios programados

### Footer
- **+ AGREGAR EVENTO**: Nuevo evento
- **ELIMINAR**: Borrar evento seleccionado

---

## 📝 Archivos de Datos

### vMix_Schedule_44_Contenidos_DB.json
Almacena todos los eventos (programas y tandas)

```json
{
  "events": {
    "Lunes": {
      "09:00:00": {
        "type": "prog",
        "title": "Mi Programa",
        "time": "09:00:00"
      },
      "10:30:00": {
        "type": "tanda",
        "list_id": "18",
        "spots": 4,
        "time": "10:30:00"
      }
    }
  }
}
```

### vMix_Schedule_44_Contenidos_Config.json
Almacena configuración de inputs y parámetros

```json
{
  "PUBLIS_POR_BLOQUE": 4,
  "INICIO_PUBLIS_INPUT": "14",
  "PUBLIS_LISTA_ID": "15",
  "CIERRE_PUBLIS_INPUT": "16"
}
```

---

## 🔐 Seguridad

- ⚠️ **No modifiques** archivos .json manualmente
- 💾 **Realiza backups** regularmente de la carpeta
- 🔒 **Protege** los archivos JSON con contraseña si es necesario

---

## 📞 Soporte

Para problemas:
1. Verifica los logs en `schedule_log.txt`
2. Comprueba la conexión a vMix
3. Reinicia la aplicación
4. Contacta al administrador si persisten los errores

---

## ✅ Versiones Soportadas

- ✅ Windows 10 (Build 1909+)
- ✅ Windows 11
- ⚠️ Windows 7/8: No soportado
- ⚠️ macOS: Usa `main.py` original

---

**Última actualización**: Mayo 2026  
**Versión**: 1.0 Portable Windows
