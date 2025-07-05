#!/usr/bin/env python3
"""
Script simplificado para crear DMG de S3Manager
"""

import os
import subprocess
import shutil
from pathlib import Path

def create_dmg():
    """Crea el DMG de forma simplificada"""
    print("🔧 CREANDO DMG SIMPLIFICADO")
    print("=" * 50)
    
    project_dir = Path("/Users/edefrutos/S3Manager")
    app_path = project_dir / "build/S3Manager.app"
    dmg_path = project_dir / "S3Manager.dmg"
    
    # Verificar que la aplicación existe
    if not app_path.exists():
        print("❌ Aplicación no encontrada")
        return False
    
    # Eliminar DMG existente
    if dmg_path.exists():
        dmg_path.unlink()
    
    try:
        # Crear DMG directamente desde la aplicación
        cmd = [
            "hdiutil", "create",
            "-srcfolder", str(app_path),
            "-volname", "S3Manager",
            "-format", "UDZO",
            "-imagekey", "zlib-level=9",
            str(dmg_path)
        ]
        
        print("🔧 Ejecutando hdiutil create...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ DMG creado exitosamente")
            
            # Verificar tamaño
            size_mb = dmg_path.stat().st_size / (1024 * 1024)
            print(f"📦 Tamaño: {size_mb:.1f} MB")
            print(f"📍 Ubicación: {dmg_path}")
            
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creando DMG: {e}")
        return False

if __name__ == "__main__":
    success = create_dmg()
    exit(0 if success else 1)
