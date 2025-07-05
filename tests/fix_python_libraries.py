#!/usr/bin/env python3
"""
Script para incluir bibliotecas Python faltantes en S3Manager
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
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def copy_python_libraries():
    """Copia las bibliotecas Python necesarias"""
    print("🔧 COPIANDO BIBLIOTECAS PYTHON")
    print("=" * 60)
    
    app_path = Path("build/S3Manager.app")
    if not app_path.exists():
        print("❌ Error: S3Manager.app no encontrada")
        return False
    
    frameworks_path = app_path / "Contents/Frameworks"
    python_path = frameworks_path / "Python.framework"
    
    # Crear directorios necesarios
    os.makedirs(python_path, exist_ok=True)
    
    # Lista de bibliotecas a copiar
    libraries = [
        ("libpython3.10.dylib", "/Library/Frameworks/Python.framework/Versions/3.10/lib/"),
        ("Python", "/Library/Frameworks/Python.framework/Versions/3.10/Python"),
    ]
    
    success = True
    
    for lib_name, source_path in libraries:
        source = Path(source_path)
        if source.is_file():
            dest = python_path / lib_name
            try:
                shutil.copy2(source, dest)
                print(f"✅ Copiada: {lib_name}")
                
                # Ajustar permisos
                os.chmod(dest, 0o755)
                print(f"✅ Permisos ajustados: {lib_name}")
                
            except Exception as e:
                print(f"❌ Error copiando {lib_name}: {e}")
                success = False
        else:
            print(f"❌ No se encontró: {source}")
            success = False
    
    # Copiar módulos Python necesarios
    site_packages = "/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages"
    modules = [
        "PySide6",
        "boto3",
        "botocore",
        "urllib3",
        "certifi",
        "dateutil",
        "jmespath",
        "s3transfer"
    ]
    
    modules_dest = python_path / "lib/python3.10/site-packages"
    os.makedirs(modules_dest, exist_ok=True)
    
    for module in modules:
        source = Path(site_packages) / module
        if source.exists():
            dest = modules_dest / module
            try:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
                print(f"✅ Módulo copiado: {module}")
            except Exception as e:
                print(f"❌ Error copiando módulo {module}: {e}")
                success = False
        else:
            print(f"❌ Módulo no encontrado: {module}")
            success = False
    
    # Verificar la instalación
    print("\n🔍 Verificando instalación...")
    
    required_files = [
        python_path / "libpython3.10.dylib",
        python_path / "Python",
        modules_dest / "PySide6",
        modules_dest / "boto3",
        modules_dest / "botocore"
    ]
    
    for file in required_files:
        if file.exists():
            print(f"✅ Verificado: {file.name}")
        else:
            print(f"❌ Falta: {file.name}")
            success = False
    
    if success:
        print("\n🎉 Bibliotecas Python instaladas correctamente")
    else:
        print("\n⚠️ Algunas bibliotecas no se pudieron instalar")
    
    return success

def update_rpath():
    """Actualiza RPATH del ejecutable"""
    print("\n🔧 ACTUALIZANDO RPATH")
    print("=" * 60)
    
    app_path = Path("build/S3Manager.app")
    executable = app_path / "Contents/MacOS/S3Manager"
    
    if not executable.exists():
        print("❌ Ejecutable no encontrado")
        return False
    
    # Añadir rpath para Python.framework
    cmd = f'install_name_tool -add_rpath "@executable_path/../Frameworks/Python.framework" "{executable}"'
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ RPATH actualizado correctamente")
        return True
    else:
        print(f"❌ Error actualizando RPATH: {stderr}")
        return False

def main():
    """Función principal"""
    print("🔧 INSTALACIÓN DE BIBLIOTECAS PYTHON")
    print("=" * 60)
    
    success = True
    
    # Copiar bibliotecas
    if not copy_python_libraries():
        success = False
    
    # Actualizar RPATH
    if not update_rpath():
        success = False
    
    if success:
        print("\n🎉 ¡INSTALACIÓN COMPLETADA!")
        print("Las bibliotecas Python han sido instaladas correctamente")
    else:
        print("\n⚠️ INSTALACIÓN INCOMPLETA")
        print("Algunas operaciones fallaron, revisa los mensajes anteriores")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
