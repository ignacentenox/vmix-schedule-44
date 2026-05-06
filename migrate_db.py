#!/usr/bin/env python3
"""Migra base de datos de tandas al nuevo formato."""

import json
import os

BASE_DIR = "/Users/ignaciomanuelcenteno/Documents/PROG/2025/CANAL44_RCUPLAY/scheduletv"
DB_FILE = os.path.join(BASE_DIR, "vMix_Schedule_44_Contenidos_DB.json")

def migrate_db():
    if not os.path.exists(DB_FILE):
        print(f"[INFO] No existe DB, creando nueva")
        new_db = {
            "programas": {d: [] for d in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]},
            "tandas": {d: [] for d in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]}
        }
        with open(DB_FILE, 'w') as f:
            json.dump(new_db, f, indent=4)
        print(f"[SUCCESS] DB creada en {DB_FILE}")
        return

    try:
        with open(DB_FILE, 'r') as f:
            db = json.load(f)
    except Exception as e:
        print(f"[ERROR] Leyendo DB: {e}")
        return

    modified = False

    # Migrar tandas
    for dia in db.get("tandas", {}):
        for tanda in db["tandas"][dia]:
            # Si tiene "name" pero no "list_id", migrar
            if "name" in tanda and "list_id" not in tanda:
                tanda["list_id"] = tanda["name"]
                del tanda["name"]
                modified = True
                print(f"[MIGRATED] {dia}: {tanda['time']} -> list_id={tanda['list_id']}")

            # Si no tiene "spots", agregar default
            if "spots" not in tanda:
                tanda["spots"] = 4
                modified = True
                print(f"[UPDATED] {dia}: {tanda['time']} -> spots=4")

    if not modified:
        print("[INFO] DB ya está actualizada")
        return

    # Guardar DB actualizada
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(db, f, indent=4)
        print(f"[SUCCESS] DB migrada correctamente")
    except Exception as e:
        print(f"[ERROR] Guardando DB: {e}")

if __name__ == '__main__':
    migrate_db()
