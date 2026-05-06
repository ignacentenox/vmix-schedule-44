#!/usr/bin/env python3
"""Test de renderizado de interfaz UI sin ejecutar el loop de vMix."""

import sys
import os

# Ajustar rutas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Desactivar vMix durante la prueba
os.environ['TEST_MODE'] = '1'

try:
    from PySide6.QtWidgets import QApplication
    from main import AMixTVPro
    
    # Crear aplicación sin ejecutar eventloop
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    window = AMixTVPro()
    
    # Validar que la UI se haya creado correctamente
    assert window.isVisible() == False, "La ventana debería estar oculta en test"
    assert window.main_tabs is not None, "main_tabs no fue creado"
    assert window.btn_vivo is not None, "btn_vivo no fue creado"
    assert window.btn_auto is not None, "btn_auto no fue creado"
    assert window.lbl_clock is not None, "lbl_clock no fue creado"
    assert window.vu is not None, "VU meter no fue creado"
    
    # Validar tamaños
    assert window.width() == 1000, f"Ancho esperado 1000, obtenido {window.width()}"
    assert window.height() == 700, f"Altura esperada 700, obtenida {window.height()}"
    
    # Validar botones
    assert window.btn_vivo.width() == 90, f"btn_vivo ancho esperado 90, obtenido {window.btn_vivo.width()}"
    assert window.btn_vivo.height() == 35, f"btn_vivo altura esperada 35, obtenida {window.btn_vivo.height()}"
    
    # Validar tabs
    assert len(window.prog_lists) == 7, f"Esperados 7 días en prog_lists, obtenidos {len(window.prog_lists)}"
    assert len(window.tanda_lists) == 7, f"Esperados 7 días en tanda_lists, obtenidos {len(window.tanda_lists)}"
    
    print("✅ VALIDACIONES PASADAS:")
    print(f"  ✓ Interfaz UI renderizada correctamente")
    print(f"  ✓ Dimensiones: {window.width()}x{window.height()}")
    print(f"  ✓ Botones EN VIVO y AUTO: OK")
    print(f"  ✓ Tabs de días (7): OK")
    print(f"  ✓ VU Meter: OK")
    print(f"  ✓ Reloj: OK")
    
except Exception as e:
    print(f"❌ ERROR en test UI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
