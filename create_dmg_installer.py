#!/usr/bin/env python3
"""
Script para crear instalador DMG de S3Manager
Autor: EDF Developer - 2025
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil
import tempfile

def run_command(command, cwd=None):
    """Ejecuta un comando y muestra la salida en tiempo real"""
    print(f"🔧 Ejecutando: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd=cwd
    )
    
    for line in process.stdout:
        print(line.strip())
    
    process.wait()
    return process.returncode == 0

def create_dmg():
    """Crea el instalador DMG para S3Manager"""
    print("🎯 Creando instalador DMG para S3Manager")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("s3_manager_app.py"):
        print("❌ Error: Ejecuta este script desde el directorio tools/aws_utils")
        return False
    
    # Crear directorio temporal para el DMG
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Usando directorio temporal: {temp_path}")
        
        # Construir la aplicación
        print("\n1️⃣ Construyendo aplicación...")
        if not run_command("python3 build_macos_app.py"):
            print("❌ Error construyendo la aplicación")
            return False
        
        # Copiar la aplicación al directorio temporal
        app_path = temp_path / "S3Manager.app"
        shutil.copytree("build/S3Manager.app", app_path)
        
        # Crear archivo de bienvenida
        welcome_path = temp_path / "README.txt"
        welcome_content = """¡Bienvenido a S3Manager!

Para instalar:
1. Arrastra S3Manager.app a la carpeta Aplicaciones
2. Abre S3Manager desde Launchpad o la carpeta Aplicaciones
3. En el primer arranque, configura tus credenciales AWS:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY

¡Disfruta usando S3Manager! 🚀
"""
        welcome_path.write_text(welcome_content)
        
        # Crear archivo de configuración inicial
        first_run_path = app_path / "Contents/Resources/first_run"
        first_run_path.parent.mkdir(exist_ok=True)
        first_run_path.touch()
        
        # Crear DMG
        print("\n2️⃣ Creando DMG...")
        dmg_path = "S3Manager.dmg"
        
        # Eliminar DMG anterior si existe
        if os.path.exists(dmg_path):
            os.remove(dmg_path)
        
        # Crear DMG temporal sin comprimir
        temp_dmg = "temp.dmg"
        if os.path.exists(temp_dmg):
            os.remove(temp_dmg)
        
        # Calcular tamaño necesario (app + 200MB extra para frameworks y recursos)
        app_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
        dmg_size = ((app_size // (1024 * 1024)) + 200)
        
        # Crear DMG temporal
        create_dmg_command = f"""
        hdiutil create -size {dmg_size}m -fs HFS+ -volname "S3Manager" "{temp_dmg}"
        """
        if not run_command(create_dmg_command):
            print("❌ Error creando DMG temporal")
            return False
        
        # Montar DMG temporal
        mount_point = "/Volumes/S3Manager"
        mount_command = f"""
        hdiutil attach "{temp_dmg}" -mountpoint "{mount_point}"
        """
        if not run_command(mount_command):
            print("❌ Error montando DMG")
            return False
        
        try:
            # Copiar archivos al DMG
            print("\n3️⃣ Copiando archivos...")
            shutil.copytree(app_path, f"{mount_point}/S3Manager.app")
            shutil.copy2(welcome_path, mount_point)
            
            # Crear enlace simbólico a Aplicaciones
            os.symlink("/Applications", f"{mount_point}/Applications")
            
            # Configurar vista del DMG
            print("\n4️⃣ Configurando vista del DMG...")
            configure_view_command = f"""
            osascript -e '
                tell application "Finder"
                    tell disk "S3Manager"
                        open
                        set current view of container window to icon view
                        set toolbar visible of container window to false
                        set statusbar visible of container window to false
                        set bounds of container window to {100, 100, 600, 400}
                        set theViewOptions to icon view options of container window
                        set arrangement of theViewOptions to not arranged
                        set icon size of theViewOptions to 128
                        set position of item "S3Manager.app" of container window to {120, 150}
                        set position of item "Applications" of container window to {380, 150}
                        set position of item "README.txt" of container window to {250, 300}
                        close
                        open
                        update without registering applications
                        delay 2
                        close
                    end tell
                end tell
            '
            """
            run_command(configure_view_command)
            
        finally:
            # Desmontar DMG
            print("\n5️⃣ Desmontando DMG temporal...")
            run_command(f'hdiutil detach "{mount_point}"')
        
        # Convertir DMG temporal a DMG final comprimido
        print("\n6️⃣ Creando DMG final comprimido...")
        convert_command = f"""
        hdiutil convert "{temp_dmg}" -format UDZO -o "{dmg_path}"
        """
        if not run_command(convert_command):
            print("❌ Error creando DMG final")
            return False
        
        # Limpiar DMG temporal
        os.remove(temp_dmg)
        
        print("\n✅ DMG creado exitosamente!")
        print(f"📦 Instalador disponible en: {dmg_path}")
        return True

def main():
    """Función principal"""
    print("🔧 CREACIÓN DE INSTALADOR DMG PARA S3MANAGER")
    print("=" * 60)
    
    if sys.platform != "darwin":
        print("❌ Este script solo funciona en macOS")
        return 1
    
    success = create_dmg()
    
    if success:
        print("\n🎉 ¡Instalador DMG creado exitosamente!")
        print("Puedes distribuir S3Manager.dmg a otros usuarios.")
    else:
        print("\n❌ Error creando el instalador DMG")
        print("Revisa los mensajes de error anteriores.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
