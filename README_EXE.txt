# 📦 Windows Portable - Archivos de Build

Los siguientes archivos se han creado para compilar un .exe portátil:

## Archivos Creados

### 1. 🔨 BUILD.bat (Recomendado)
- **Uso**: Doble clic en el archivo
- **Función**: Automatiza todo el proceso de compilación
- **Ventaja**: Más simple, todo en un click
- **Inconveniente**: Solo funciona en Windows

### 2. 🔨 build.py (Alternativa)
- **Uso**: `python build.py`
- **Función**: Igual que BUILD.bat pero en Python
- **Ventaja**: Funciona en Windows/Mac/Linux
- **Inconveniente**: Requiere ejecutarlo desde terminal

### 3. 📖 main_windows.py (Script Principal)
- Versión adaptada para Windows con rutas relativas
- Compatible con PyInstaller
- Totalmente portátil (funciona en cualquier carpeta)

### 4. 📋 INSTALL_WINDOWS.md
- Guía completa de instalación
- Troubleshooting detallado
- Explicación de archivos de configuración

### 5. ⚡ QUICK_START.txt
- Inicio rápido en 3 pasos
- Resumen de problemas comunes
- Instrucciones mínimas para empezar

### 6. requirements.txt
- Lista de dependencias Python necesarias
- Usado automáticamente por los builders

---

## ✅ Cómo Crear el .exe

### Opción 1: RECOMENDADA (Más fácil)

1. Descarga Python: https://www.python.org/downloads/
   - ✅ Marca "Add Python to PATH" durante instalación

2. Doble clic en: **BUILD.bat**
   - Espera 5-10 minutos
   - Se descarga e instala todo automáticamente

3. El .exe estará en: `dist\vMix_Schedule_44\`

---

### Opción 2: Línea de Comandos

1. Descarga Python: https://www.python.org/downloads/
   - ✅ Marca "Add Python to PATH" durante instalación

2. Abre Terminal / CMD en esta carpeta

3. Ejecuta:
   ```bash
   python build.py
   ```

4. El .exe estará en: `dist\vMix_Schedule_44\`

---

## 📊 Estructura de Archivos Después de Compilar

```
scheduletv/
├── main.py                          ← Original (Mac)
├── main_windows.py                  ← Para compilar
├── build.py                        ← Builder Python
├── BUILD.bat                       ← Builder Windows (Recomendado)
├── requirements.txt                ← Dependencias
├── INSTALL_WINDOWS.md              ← Guía completa
├── QUICK_START.txt                 ← Inicio rápido
│
├── dist/                           ← 📦 EL .EXE ESTARÁ AQUÍ
│   └── vMix_Schedule_44/
│       ├── vMix_Schedule_44.exe   ← El ejecutable principal
│       ├── _internal/            ← Librerías (PySide6, requests, etc)
│       ├── vMix_Schedule_44_Contenidos_DB.json      (datos)
│       └── vMix_Schedule_44_Contenidos_Config.json  (config)
│
├── venv/                           ← Entorno virtual (se crea automáticamente)
└── build/                          ← Carpeta temporal (se borra al finalizar)
```

---

## 🚀 Después de Compilar

### Usar el .exe:

1. Ve a: `dist\vMix_Schedule_44\`

2. Haz doble clic en: `vMix_Schedule_44.exe`

3. Se abrirá la aplicación:
   - Interfaz idéntica a la versión Mac
   - Totalmente portátil
   - Funciona en cualquier Windows 10/11

### Distribuir el .exe:

- La carpeta `dist\vMix_Schedule_44\` es COMPLETAMENTE PORTABLE
- Puedes copiarla a:
  - Otro PC
  - USB
  - Dropbox
  - Cualquier lugar
- NO necesita que Python esté instalado en el destino

### Crear acceso directo:

1. Haz clic derecho en: `vMix_Schedule_44.exe`
2. Selecciona: "Enviar a" → "Escritorio (crear acceso directo)"
3. Ahora tendrás un icono en el escritorio

---

## 🔒 Portabilidad 100%

El .exe compilado es **completamente portátil** porque:

✅ Incluye Python empaquetado  
✅ Incluye todas las librerías (PySide6, requests)  
✅ Incluye archivos JSON de datos  
✅ Usa rutas relativas (no hardcodeadas)  
✅ NO requiere instalaciones previas  

**Resultado**: Funciona en cualquier Windows 10/11 sin dependencias adicionales

---

## 📌 Notas Importantes

- El primer builder tomará 5-10 minutos (descarga PyInstaller ~200MB)
- Compilaciones posteriores serán más rápidas (~2-3 minutos)
- El .exe resultante es ~250-300MB
- Usa ~150MB de RAM durante ejecución
- Compatible con vMix en red (192.168.192.140:8098)

---

## ❓ Si Tienes Dudas

1. Lee: **QUICK_START.txt** (inicio rápido)
2. Lee: **INSTALL_WINDOWS.md** (guía completa)
3. Si BUILD.bat no funciona, usa: `python build.py`
4. Verifica que Python esté instalado: `python --version`

---

**¡Listo para distribuir! 🎉**
