#!/usr/bin/env python3
"""
Script mejorado para construir S3Manager con todas las bibliotecas incluidas
Autor: EDF Developer - 2025
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_command(command):
    """Ejecuta un comando y retorna el resultado"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def check_dependencies():
    """Verifica que todas las dependencias estén disponibles"""
    print("🔍 Verificando dependencias...")
    
    dependencies = {
        'PyInstaller': 'pyinstaller',
        'PySide6': 'PySide6',
        'boto3': 'boto3',
        'botocore': 'botocore'
    }
    
    missing = []
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name}: Disponible")
        except ImportError:
            print(f"❌ {name}: No disponible")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Faltan dependencias: {', '.join(missing)}")
        print("Instala con: pip install pyinstaller PySide6 boto3 botocore")
        return False
    
    print("✅ Todas las dependencias disponibles")
    return True

def clean_build():
    """Limpia construcciones anteriores"""
    print("\n🧹 Limpiando construcciones anteriores...")
    
    paths_to_clean = [
        "build",
        "dist",
        "__pycache__",
        "*.spec"
    ]
    
    for path in paths_to_clean:
        if path.endswith("*"):
            # Usar glob para patrones
            import glob
            for file in glob.glob(path):
                try:
                    os.remove(file)
                    print(f"✅ Eliminado: {file}")
                except:
                    pass
        else:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_dir():
                    shutil.rmtree(path_obj)
                else:
                    path_obj.unlink()
                print(f"✅ Eliminado: {path}")

def create_spec_file():
    """Crea un archivo .spec personalizado para PyInstaller"""
    print("\n📝 Creando archivo .spec personalizado...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['s3_manager_app.py'],
    pathex=[],
    binaries=[],
    datas=[('diagnose_s3_permissions.py', '.')],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets', 
        'PySide6.QtGui',
        'PySide6.QtTest',
        'boto3',
        'botocore',
        'botocore.client',
        'botocore.exceptions',
        'urllib3',
        'certifi',
        'dateutil',
        'jmespath',
        's3transfer',
        'threading',
        'tempfile',
        'pathlib',
        'datetime',
        'json',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Incluir todos los módulos de PySide6
pyside6_modules = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui', 
    'PySide6.QtTest',
    'PySide6.QtNetwork',
    'PySide6.QtOpenGL',
    'PySide6.QtPrintSupport',
    'PySide6.QtSql',
    'PySide6.QtSvg',
    'PySide6.QtXml'
]

for module in pyside6_modules:
    try:
        __import__(module)
        a.hiddenimports.append(module)
    except ImportError:
        pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='S3Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='S3Manager',
)

app = BUNDLE(
    coll,
    name='S3Manager.app',
    icon='icon.icns',
    bundle_identifier='com.edefrutos.s3manager',
    info_plist={
        'CFBundleDisplayName': 'S3 Manager',
        'CFBundleShortVersionString': '1.1.0',
        'CFBundleVersion': '1.1.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15.0',
        'NSHumanReadableCopyright': '© 2025 EDF Developer',
        'NSPrincipalClass': 'NSApplication'
    },
)
'''
    
    with open('S3Manager.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Archivo .spec creado")

def build_app():
    """Construye la aplicación usando PyInstaller"""
    print("\n🔨 Construyendo aplicación con PyInstaller...")
    
    # Usar el archivo .spec personalizado
    cmd = "pyinstaller --clean --noconfirm S3Manager.spec"
    
    print(f"🔧 Ejecutando: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ PyInstaller completado exitosamente")
        return True
    else:
        print(f"❌ Error en PyInstaller:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False

def customize_app():
    """Personaliza la aplicación construida"""
    print("\n🎨 Personalizando aplicación...")
    
    app_path = Path("dist/S3Manager.app")
    if not app_path.exists():
        print("❌ Aplicación no encontrada en dist/")
        return False
    
    # Mover a build/
    build_path = Path("build/S3Manager.app")
    if build_path.exists():
        shutil.rmtree(build_path)
    
    os.makedirs("build", exist_ok=True)
    shutil.move(str(app_path), str(build_path))
    print("✅ Aplicación movida a build/")
    
    # Verificar icono
    icon_source = Path("icon.icns")
    icon_dest = build_path / "Contents/Resources/icon.icns"
    
    if icon_source.exists() and not icon_dest.exists():
        shutil.copy2(icon_source, icon_dest)
        print("✅ Icono copiado")
    
    return True

def test_app():
    """Prueba básica de la aplicación"""
    print("\n🧪 Probando aplicación...")
    
    app_path = Path("build/S3Manager.app")
    executable = app_path / "Contents/MacOS/S3Manager"
    
    if not executable.exists():
        print("❌ Ejecutable no encontrado")
        return False
    
    # Verificar permisos
    if not os.access(executable, os.X_OK):
        print("❌ Sin permisos de ejecución")
        return False
    
    print("✅ Aplicación construida correctamente")
    return True

def main():
    """Función principal"""
    print("🔨 CONSTRUCTOR COMPLETO DE S3 MANAGER")
    print("=" * 60)
    
    steps = [
        ("Verificar dependencias", check_dependencies),
        ("Limpiar construcciones anteriores", clean_build),
        ("Crear archivo .spec", create_spec_file),
        ("Construir aplicación", build_app),
        ("Personalizar aplicación", customize_app),
        ("Probar aplicación", test_app),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Falló: {step_name}")
            return 1
    
    print("\n" + "=" * 60)
    print("🎉 ¡CONSTRUCCIÓN COMPLETADA!")
    print("=" * 60)
    print("📍 Ubicación: build/S3Manager.app")
    print("📋 Para usar la aplicación:")
    print("1. Navega a: build/S3Manager.app")
    print("2. Haz doble clic en S3Manager.app")
    print("3. Si macOS bloquea la app, ve a Preferencias > Seguridad y Privacidad")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
