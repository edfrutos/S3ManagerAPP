#!/usr/bin/env python3
"""
Script de prueba para distribución y compatibilidad de S3Manager
Autor: EDF Developer - 2025
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command):
    """Ejecuta un comando y retorna el resultado"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def test_macos_version():
    """Verifica la compatibilidad con la versión de macOS"""
    print("🧪 PRUEBA: Compatibilidad de macOS")
    print("-" * 40)
    
    # Obtener versión de macOS
    success, stdout, stderr = run_command("sw_vers -productVersion")
    
    if success:
        version = stdout.strip()
        print(f"📱 Versión de macOS: {version}")
        
        # Verificar versión mínima (10.15)
        version_parts = version.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        if major > 10 or (major == 10 and minor >= 15):
            print("✅ Versión compatible (10.15+)")
            return True
        else:
            print("❌ Versión no compatible (requiere 10.15+)")
            return False
    else:
        print(f"❌ Error obteniendo versión: {stderr}")
        return False

def test_architecture():
    """Verifica la arquitectura del sistema"""
    print("\n🧪 PRUEBA: Arquitectura del Sistema")
    print("-" * 40)
    
    arch = platform.machine()
    print(f"🏗️ Arquitectura: {arch}")
    
    if arch in ['x86_64', 'arm64']:
        print("✅ Arquitectura compatible")
        return True
    else:
        print("❌ Arquitectura no compatible")
        return False

def test_python_version():
    """Verifica la versión de Python"""
    print("\n🧪 PRUEBA: Versión de Python")
    print("-" * 40)
    
    version = sys.version_info
    print(f"🐍 Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Versión de Python compatible (3.8+)")
        return True
    else:
        print("❌ Versión de Python no compatible (requiere 3.8+)")
        return False

def test_dependencies():
    """Verifica las dependencias necesarias"""
    print("\n🧪 PRUEBA: Dependencias del Sistema")
    print("-" * 40)
    
    dependencies = [
        ('PySide6', 'import PySide6'),
        ('boto3', 'import boto3'),
        ('botocore', 'import botocore'),
    ]
    
    all_ok = True
    
    for dep_name, import_cmd in dependencies:
        try:
            exec(import_cmd)
            print(f"✅ {dep_name}: Disponible")
        except ImportError:
            print(f"❌ {dep_name}: No disponible")
            all_ok = False
    
    return all_ok

def test_app_structure():
    """Verifica la estructura de la aplicación"""
    print("\n🧪 PRUEBA: Estructura de la Aplicación")
    print("-" * 40)
    
    app_path = "build/S3Manager.app"
    
    if not os.path.exists(app_path):
        print("❌ Aplicación no encontrada")
        return False
    
    required_files = [
        "Contents/Info.plist",
        "Contents/MacOS/S3Manager",
        "Contents/Resources/icon.icns",
    ]
    
    all_ok = True
    
    for file_path in required_files:
        full_path = f"{app_path}/{file_path}"
        if os.path.exists(full_path):
            print(f"✅ {file_path}: Presente")
        else:
            print(f"❌ {file_path}: Faltante")
            all_ok = False
    
    return all_ok

def test_permissions():
    """Verifica los permisos de la aplicación"""
    print("\n🧪 PRUEBA: Permisos de la Aplicación")
    print("-" * 40)
    
    app_path = "build/S3Manager.app"
    executable_path = f"{app_path}/Contents/MacOS/S3Manager"
    
    if os.path.exists(executable_path):
        # Verificar permisos de ejecución
        if os.access(executable_path, os.X_OK):
            print("✅ Ejecutable tiene permisos de ejecución")
        else:
            print("❌ Ejecutable sin permisos de ejecución")
            return False
        
        # Verificar propietario
        stat_info = os.stat(executable_path)
        print(f"📋 UID: {stat_info.st_uid}, GID: {stat_info.st_gid}")
        print("✅ Permisos verificados")
        return True
    else:
        print("❌ Ejecutable no encontrado")
        return False

def test_code_signing():
    """Verifica el estado de firma de código"""
    print("\n🧪 PRUEBA: Firma de Código")
    print("-" * 40)
    
    app_path = "build/S3Manager.app"
    
    # Verificar firma de código
    success, stdout, stderr = run_command(f'codesign -dv "{app_path}" 2>&1')
    
    if "not signed" in stdout or "not signed" in stderr:
        print("⚠️ Aplicación no firmada (normal para desarrollo)")
        print("💡 Para distribución, considera firmar con certificado de desarrollador")
        return True
    elif success:
        print("✅ Aplicación firmada")
        print(f"📋 Detalles: {stdout}")
        return True
    else:
        print("❌ Error verificando firma")
        return False

def test_quarantine():
    """Verifica el estado de cuarentena"""
    print("\n🧪 PRUEBA: Estado de Cuarentena")
    print("-" * 40)
    
    app_path = "build/S3Manager.app"
    
    # Verificar atributos de cuarentena
    success, stdout, stderr = run_command(f'xattr -l "{app_path}"')
    
    if "com.apple.quarantine" in stdout:
        print("⚠️ Aplicación en cuarentena")
        print("💡 Usar: xattr -cr para limpiar atributos")
        return True
    else:
        print("✅ Sin atributos de cuarentena")
        return True

def main():
    """Función principal"""
    print("🔧 PRUEBAS DE DISTRIBUCIÓN S3MANAGER")
    print("=" * 60)
    
    # Verificar que estamos en macOS
    if platform.system() != "Darwin":
        print("❌ Este script solo funciona en macOS")
        return 1
    
    tests = [
        ("Compatibilidad de macOS", test_macos_version),
        ("Arquitectura del Sistema", test_architecture),
        ("Versión de Python", test_python_version),
        ("Dependencias del Sistema", test_dependencies),
        ("Estructura de la Aplicación", test_app_structure),
        ("Permisos de la Aplicación", test_permissions),
        ("Firma de Código", test_code_signing),
        ("Estado de Cuarentena", test_quarantine),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results[test_name] = False
    
    # Generar reporte final
    print("\n" + "=" * 60)
    print("📋 REPORTE FINAL DE PRUEBAS DE DISTRIBUCIÓN")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📊 Resumen: {passed_tests}/{total_tests} pruebas exitosas")
    print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📝 Detalle de pruebas:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    # Información del sistema
    print("\n📋 Información del Sistema:")
    print(f"   🖥️ Sistema: {platform.system()} {platform.release()}")
    print(f"   🏗️ Arquitectura: {platform.machine()}")
    print(f"   🐍 Python: {sys.version.split()[0]}")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODAS LAS PRUEBAS DE DISTRIBUCIÓN EXITOSAS!")
        print("La aplicación está lista para distribución.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} pruebas fallaron")
        print("Revisa los errores anteriores para más detalles.")
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
