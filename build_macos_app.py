#!/usr/bin/env python3
"""
Script para crear una aplicación macOS nativa (.app) del S3 Manager
Autor: EDF Developer
Fecha: 2025
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_app_bundle():
    """Crea el bundle de la aplicación macOS"""
    
    print("🚀 Creando aplicación macOS S3 Manager...")
    
    # Directorio actual
    current_dir = Path(__file__).parent
    
    # Crear directorio de build si no existe
    build_dir = current_dir / "build"
    build_dir.mkdir(exist_ok=True)
    
    # Configuración de PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--name=S3Manager",
        "--windowed",  # No mostrar consola
        "--onedir",    # Un directorio con todas las dependencias
        "--clean",     # Limpiar cache
        "--noconfirm", # No pedir confirmación
        f"--distpath={build_dir}",
        f"--workpath={build_dir}/work",
        f"--specpath={build_dir}",
        f"--add-data={current_dir}/diagnose_s3_permissions.py:.",  # Incluir módulo de diagnóstico
        f"--icon={current_dir}/icon.icns",  # Incluir icono
        "--hidden-import=boto3",
        "--hidden-import=botocore",
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        str(current_dir / "s3_manager_app.py")
    ]
    
    print("📦 Ejecutando PyInstaller...")
    try:
        result = subprocess.run(pyinstaller_args, check=True, capture_output=True, text=True)
        print("✅ PyInstaller completado exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en PyInstaller: {e}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    
    # Ruta de la aplicación generada
    app_path = build_dir / "S3Manager.app"
    
    if app_path.exists():
        print(f"✅ Aplicación creada en: {app_path}")
        
        # Crear Info.plist personalizado
        create_info_plist(app_path)
        
        # Copiar icono si existe
        copy_app_icon(app_path)
        
        print("🎉 ¡Aplicación macOS creada exitosamente!")
        print(f"📍 Ubicación: {app_path.absolute()}")
        print("\n📋 Para usar la aplicación:")
        print(f"   1. Navega a: {app_path.absolute()}")
        print("   2. Haz doble clic en S3Manager.app")
        print("   3. Si macOS bloquea la app, ve a Preferencias > Seguridad y Privacidad")
        
        return True
    else:
        print("❌ No se pudo crear la aplicación")
        return False

def create_info_plist(app_path):
    """Crea un Info.plist personalizado para la aplicación"""
    
    info_plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>es</string>
    <key>CFBundleDisplayName</key>
    <string>S3 Manager</string>
    <key>CFBundleExecutable</key>
    <string>S3Manager</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.catalogotablas.s3manager</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>S3Manager</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>© 2025 EDF Developer</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>s3</string>
            </array>
            <key>CFBundleTypeName</key>
            <string>S3 Configuration</string>
            <key>CFBundleTypeRole</key>
            <string>Editor</string>
        </dict>
    </array>
</dict>
</plist>"""
    
    info_plist_path = app_path / "Contents" / "Info.plist"
    
    try:
        with open(info_plist_path, 'w', encoding='utf-8') as f:
            f.write(info_plist_content)
        print("✅ Info.plist personalizado creado")
    except Exception as e:
        print(f"⚠️  Error creando Info.plist: {e}")

def copy_app_icon(app_path):
    """Copia el icono de la aplicación si existe"""
    
    # Buscar icono en varios formatos
    icon_sources = [
        "icon.icns",
        "app_icon.icns",
        "s3_icon.icns"
    ]
    
    resources_dir = app_path / "Contents" / "Resources"
    resources_dir.mkdir(exist_ok=True)
    
    current_dir = Path(__file__).parent
    
    for icon_name in icon_sources:
        icon_path = current_dir / icon_name
        if icon_path.exists():
            try:
                shutil.copy2(icon_path, resources_dir / "icon.icns")
                print(f"✅ Icono copiado: {icon_name}")
                return
            except Exception as e:
                print(f"⚠️  Error copiando icono: {e}")
    
    # Si no hay icono, crear uno básico
    create_basic_icon(resources_dir)

def create_basic_icon(resources_dir):
    """Crea un icono básico para la aplicación"""
    
    try:
        # Crear un icono simple usando iconutil (si está disponible)
        iconset_dir = resources_dir / "icon.iconset"
        iconset_dir.mkdir(exist_ok=True)
        
        # Crear iconos de diferentes tamaños (esto es muy básico)
        # En una implementación real, usarías imágenes PNG reales
        print("ℹ️  Creando icono básico...")
        
        # Eliminar el directorio iconset ya que no tenemos imágenes reales
        shutil.rmtree(iconset_dir)
        
        print("⚠️  No se encontró icono personalizado")
        
    except Exception as e:
        print(f"⚠️  Error creando icono básico: {e}")

def create_launcher_script():
    """Crea un script de lanzamiento adicional"""
    
    current_dir = Path(__file__).parent
    launcher_path = current_dir / "launch_s3_manager.sh"
    
    launcher_content = """#!/bin/bash
# Script de lanzamiento para S3 Manager
# Autor: Sistema de Catálogo de Tablas

echo "🚀 Iniciando S3 Manager..."

# Directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activar entorno virtual si existe
if [ -d "$DIR/../../venv310" ]; then
    source "$DIR/../../venv310/bin/activate"
    echo "✅ Entorno virtual activado"
fi

# Verificar dependencias
python3 -c "import PyQt6, boto3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencias faltantes. Instalando..."
    pip install PyQt6 boto3
fi

# Ejecutar aplicación
cd "$DIR"
python3 s3_manager_app.py

echo "👋 S3 Manager cerrado"
"""
    
    try:
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        # Hacer ejecutable
        os.chmod(launcher_path, 0o755)
        
        print(f"✅ Script de lanzamiento creado: {launcher_path}")
        
    except Exception as e:
        print(f"⚠️  Error creando script de lanzamiento: {e}")

def main():
    """Función principal"""
    
    print("🔨 CONSTRUCTOR DE APLICACIÓN MACOS S3 MANAGER")
    print("=" * 50)
    
    # Verificar que estamos en macOS
    if sys.platform != "darwin":
        print("❌ Este script solo funciona en macOS")
        sys.exit(1)
    
    # Verificar dependencias
    try:
        import PyQt6
        import boto3
        print("✅ Dependencias verificadas")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("Instala con: pip install PyQt6 boto3")
        sys.exit(1)
    
    # Verificar PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        print("✅ PyInstaller disponible")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller no encontrado")
        print("Instala con: pip install pyinstaller")
        sys.exit(1)
    
    # Crear aplicación
    success = create_app_bundle()
    
    # Crear script de lanzamiento adicional
    create_launcher_script()
    
    if success:
        print("\n🎉 ¡CONSTRUCCIÓN COMPLETADA!")
        print("📱 Tu aplicación S3 Manager está lista para usar")
    else:
        print("\n❌ Error en la construcción")
        sys.exit(1)

if __name__ == "__main__":
    main()
