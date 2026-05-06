# 🎨 vMix Schedule 44 - Branded EXE Builder

## 🎯 Con Logo de 44 Contenidos

Este builder crea un .exe profesional con:
- ✅ Logo de 44 Contenidos integrado
- ✅ Título: "vMix Schedule 44 - Powered by IGNACE"
- ✅ Totalmente portable (funciona en cualquier Windows 10/11)
- ✅ Sin instalación requerida

---

## 🚀 Generar el .exe en 3 Pasos

### **Paso 1: Descargar Python**
- Descarga: https://www.python.org/downloads/
- ✅ **IMPORTANTE**: Durante instalación, marca "Add Python to PATH"
- Instala normalmente

### **Paso 2: Ejecutar el Builder**

**OPCIÓN A (Recomendada - Más fácil):**
1. Doble clic en: **BUILD_BRANDED.bat**
2. Espera 5-10 minutos
3. ¡Listo!

**OPCIÓN B (Alternativa):**
```bash
python build_branded.py
```

### **Paso 3: Usar el .exe**
El ejecutable estará en: `dist\vMix_Schedule_44\vMix_Schedule_44.exe`

- Funciona en cualquier Windows 10/11
- Completamente portátil
- Puedes copiar la carpeta a USB

---

## 📦 Qué Incluye

```
dist/vMix_Schedule_44/
├── vMix_Schedule_44.exe          ← El ejecutable
├── app_icon.png                  ← Logo de 44 Contenidos
├── app.ico                       ← Icono para la barra de título
├── _internal/                    ← Librerías (PySide6, requests, etc)
├── vMix_Schedule_44_Contenidos_DB.json
└── vMix_Schedule_44_Contenidos_Config.json
```

**Tamaño total:** ~250-300 MB

---

## 🎨 Personalización

### Logo
- **Ubicación**: `app_icon.png`
- **Formato**: PNG con transparencia
- **Tamaño recomendado**: 512x512px
- **Automáticamente convertido a**: `app.ico` (durante compilación)

### Título
Editar en `main_windows.py` línea ~315:
```python
self.setWindowTitle("vMix Schedule 44 - Powered by IGNACE")
```

---

## 🔧 Troubleshooting

### ❌ "Python no está instalado"
**Solución:**
1. Descarga desde python.org
2. Instala con "Add Python to PATH" ✅
3. Reinicia tu PC
4. Intenta nuevamente

### ❌ "Error en compilación"
**Solución:**
1. Abre `cmd.exe` como Administrador
2. Navega a la carpeta del proyecto
3. Ejecuta: `python build_branded.py`
4. Verifica los errores mostrados

### ❌ "El .exe no se ejecuta"
**Solución:**
1. Instala Visual C++ Redistributable:
   https://support.microsoft.com/help/2977003
2. Verifica que vMix esté en: http://192.168.192.140:8098
3. Ejecuta desde terminal para ver errores: `vMix_Schedule_44.exe`

---

## 📊 Estructura de Archivos (Antes de compilar)

```
scheduletv/
├── main.py                      ← Original (Mac)
├── main_windows.py              ← Script para compilar (Windows)
├── app_icon.png                 ← Logo PNG (copiado automáticamente)
├── build_branded.py             ← Builder con logo integrado
├── BUILD_BRANDED.bat            ← Script para ejecutar desde Windows
├── requirements.txt             ← Dependencias Python
├── vMix_Schedule_44_Contenidos_DB.json
├── vMix_Schedule_44_Contenidos_Config.json
└── ... (otros archivos)
```

---

## 🎯 Después de Compilar

### Distribuir el .exe

1. **Carpeta portable:**
   - Copia: `dist\vMix_Schedule_44\` a cualquier lugar
   - Funciona en cualquier PC con Windows 10/11

2. **Crear installer (opcional):**
   - Usa NSIS o Inno Setup
   - Distribuye con el .exe portable

3. **Para USB:**
   - Copia toda la carpeta a USB
   - Ejecuta desde allí

---

## 📋 Requisitos del Sistema

- **Windows 10** o **Windows 11** (64-bit recomendado)
- **2 GB RAM** mínimo
- **500 MB libre** en disco (durante compilación)
- **Conexión a vMix** en: http://192.168.192.140:8098

---

## ✅ Verificación

Después de compilar, verifica que:
- ✅ `dist\vMix_Schedule_44\` existe
- ✅ `vMix_Schedule_44.exe` existe (~200MB)
- ✅ Doble clic en .exe abre la ventana
- ✅ El logo aparece en la barra de título
- ✅ El título dice "vMix Schedule 44 - Powered by IGNACE"

---

## 🎨 Personalización Avanzada

### Cambiar logo:
1. Reemplaza `app_icon.png` con tu imagen PNG
2. Vuelve a ejecutar `build_branded.py`

### Cambiar título:
1. Edita `main_windows.py` línea ~315
2. Busca: `self.setWindowTitle(...)`
3. Cambiar el texto
4. Vuelve a compilar

### Cambiar nombre del .exe:
1. Edita `build_branded.py` línea ~70
2. Busca: `"--name", "vMix_Schedule_44"`
3. Cambiar nombre
4. Vuelve a compilar

---

## 📞 Soporte

### Si algo falla:
1. Lee los errores en la terminal
2. Verifica que Python esté instalado: `python --version`
3. Limpia builds anteriores: `rmdir build dist`
4. Intenta nuevamente

### Archivos útiles:
- `schedule_log.txt` - Log de errores de ejecución
- `vMix_Schedule_44_Contenidos_Config.json` - Configuración guardada
- `vMix_Schedule_44_Contenidos_DB.json` - Base de datos de eventos

---

## 🏆 Resultado Final

Un programa profesional con:
- 🎨 Logo de 44 Contenidos
- 📋 Título profesional
- 🚀 Ejecución portátil
- 📦 Todo en una carpeta
- ✨ Listo para distribuir

**¡Ya puedes entregar a tus clientes!** 🎉

---

**Versión:** 1.0 Branded  
**Fecha:** Mayo 2026  
**Branding:** 44 Contenidos + IGNACE
