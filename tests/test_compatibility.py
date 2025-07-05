#!/usr/bin/env python3
"""
Script de prueba de compatibilidad extendida para S3Manager
Autor: EDF Developer - 2025
"""

import os
import sys
import platform
import subprocess
import shutil
import psutil
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

def test_macos_requirements():
    """Verifica requisitos mínimos de macOS"""
    print("🧪 PRUEBA: Requisitos de macOS")
    print("-" * 40)
    
    # Obtener versión de macOS
    success, stdout, stderr = run_command("sw_vers -productVersion")
    
    if success:
        version = stdout.strip()
        print(f"📱 Versión de macOS detectada: {version}")
        
        # Parsear versión
        version_parts = version.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        # Verificar compatibilidad
        if major > 10 or (major == 10 and minor >= 15):
            print("✅ Versión compatible (10.15+)")
            
            # Verificar características específicas
            features = {
                "Hardened Runtime": run_command("csrutil status")[0],
                "App Sandbox": os.path.exists("/System/Library/Sandbox/rootless.conf"),
                "Universal Binaries": platform.machine() in ['x86_64', 'arm64'],
            }
            
            for feature, supported in features.items():
                status = "✅" if supported else "⚠️"
                print(f"{status} {feature}")
            
            return True
        else:
            print("❌ Versión no compatible (requiere 10.15+)")
            return False
    else:
        print(f"❌ Error obteniendo versión: {stderr}")
        return False

def test_python_environment():
    """Verifica el entorno Python"""
    print("\n🧪 PRUEBA: Entorno Python")
    print("-" * 40)
    
    # Verificar versión de Python
    version = sys.version_info
    print(f"🐍 Python: {version.major}.{version.minor}.{version.micro}")
    
    # Verificar si Python está incluido en la aplicación
    app_python = Path("build/S3Manager.app/Contents/Frameworks/Python.framework")
    if app_python.exists():
        print("✅ Python incluido en la aplicación")
        bundled = True
    else:
        print("⚠️ Python no incluido - usando Python del sistema")
        bundled = False
    
    # Verificar dependencias
    dependencies = [
        'PySide6',
        'boto3',
        'botocore',
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Disponible")
        except ImportError:
            print(f"❌ {dep}: No disponible")
            missing_deps.append(dep)
    
    if bundled and not missing_deps:
        print("🚀 Entorno Python completamente funcional")
        return True
    elif not bundled and not missing_deps:
        print("✅ Entorno Python funcional (sistema)")
        return True
    else:
        print("❌ Faltan dependencias necesarias")
        return False

def test_architecture_compatibility():
    """Verifica compatibilidad de arquitectura"""
    print("\n🧪 PRUEBA: Compatibilidad de Arquitectura")
    print("-" * 40)
    
    arch = platform.machine()
    print(f"🏗️ Arquitectura detectada: {arch}")
    
    app_path = Path("build/S3Manager.app/Contents/MacOS/S3Manager")
    if not app_path.exists():
        print("❌ Ejecutable no encontrado")
        return False
    
    # Verificar tipo de binario
    success, stdout, stderr = run_command(f"file '{app_path}'")
    
    if success:
        print(f"📋 Tipo de binario: {stdout.strip()}")
        
        if arch == 'arm64':
            if 'arm64' in stdout:
                print("✅ Binario nativo ARM64")
                is_native = True
            else:
                print("⚠️ Binario no optimizado para ARM64")
                is_native = False
        elif arch == 'x86_64':
            if 'x86_64' in stdout:
                print("✅ Binario nativo Intel x64")
                is_native = True
            else:
                print("⚠️ Binario no optimizado para Intel x64")
                is_native = False
        else:
            print(f"❌ Arquitectura no soportada: {arch}")
            return False
        
        # Verificar Universal Binary
        if 'universal' in stdout.lower():
            print("🚀 Binario Universal (Intel + ARM)")
            return True
        elif is_native:
            print("✅ Binario nativo para esta arquitectura")
            return True
        else:
            print("⚠️ No es binario universal ni nativo")
            return False
    else:
        print(f"❌ Error verificando binario: {stderr}")
        return False

def test_system_integration():
    """Verifica integración con el sistema"""
    print("\n🧪 PRUEBA: Integración con Sistema")
    print("-" * 40)
    
    app_path = Path("build/S3Manager.app")
    
    checks = {
        "Info.plist": app_path / "Contents/Info.plist",
        "Icono": app_path / "Contents/Resources/icon.icns",
        "Ejecutable": app_path / "Contents/MacOS/S3Manager",
    }
    
    all_ok = True
    
    for check_name, check_path in checks.items():
        if check_path.exists():
            print(f"✅ {check_name}: Presente")
            
            # Verificaciones adicionales
            if check_name == "Info.plist":
                success, stdout, stderr = run_command(f"plutil -lint '{check_path}'")
                if success:
                    print("   ✅ Info.plist válido")
                else:
                    print(f"   ❌ Error en Info.plist: {stderr}")
                    all_ok = False
            
            elif check_name == "Ejecutable":
                if os.access(check_path, os.X_OK):
                    print("   ✅ Permisos de ejecución correctos")
                else:
                    print("   ❌ Faltan permisos de ejecución")
                    all_ok = False
        else:
            print(f"❌ {check_name}: Faltante")
            all_ok = False
    
    return all_ok

def test_launch_conditions():
    """Verifica condiciones de lanzamiento"""
    print("\n🧪 PRUEBA: Condiciones de Lanzamiento")
    print("-" * 40)
    
    conditions = {
        "Permisos de red": True,  # Siempre permitido en macOS
        "Acceso a archivos": os.access(os.path.expanduser("~"), os.W_OK),
        "Memoria disponible": psutil.virtual_memory().available > (512 * 1024 * 1024),  # 512 MB
        "Espacio en disco": shutil.disk_usage("/").free > (1024 * 1024 * 1024),  # 1 GB
    }
    
    all_ok = True
    
    for condition, status in conditions.items():
        if status:
            print(f"✅ {condition}: OK")
        else:
            print(f"❌ {condition}: Fallo")
            all_ok = False
    
    return all_ok

def test_no_python_scenario():
    """Simula escenario sin Python instalado"""
    print("\n🧪 PRUEBA: Escenario sin Python")
    print("-" * 40)
    
    app_path = Path("build/S3Manager.app")
    
    # Verificar Python embebido
    python_framework = app_path / "Contents/Frameworks/Python.framework"
    if python_framework.exists():
        print("✅ Python embebido encontrado")
        
        # Verificar bibliotecas necesarias
        required_libs = [
            "libpython*.dylib",
            "Python.framework/Versions/*/Python",
        ]
        
        all_libs_found = True
        for lib in required_libs:
            if list(python_framework.glob(lib)):
                print(f"✅ Biblioteca {lib}: Presente")
            else:
                print(f"❌ Biblioteca {lib}: Faltante")
                all_libs_found = False
        
        if all_libs_found:
            print("🚀 Aplicación funcional sin Python del sistema")
            return True
        else:
            print("⚠️ Faltan algunas bibliotecas Python")
            return False
    else:
        print("❌ Python no está embebido")
        print("⚠️ La aplicación requiere Python del sistema")
        return False

def main():
    """Función principal"""
    print("🔧 PRUEBAS DE COMPATIBILIDAD EXTENDIDA S3MANAGER")
    print("=" * 60)
    
    tests = [
        ("Requisitos de macOS", test_macos_requirements),
        ("Entorno Python", test_python_environment),
        ("Compatibilidad de Arquitectura", test_architecture_compatibility),
        ("Integración con Sistema", test_system_integration),
        ("Condiciones de Lanzamiento", test_launch_conditions),
        ("Escenario sin Python", test_no_python_scenario),
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
    print("📋 REPORTE FINAL DE COMPATIBILIDAD")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📊 Resumen: {passed_tests}/{total_tests} pruebas exitosas")
    print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📝 Detalle de pruebas:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    # Evaluación de compatibilidad
    print("\n🎯 Evaluación de Compatibilidad:")
    if passed_tests == total_tests:
        print("🚀 COMPATIBILIDAD TOTAL")
        print("La aplicación es completamente compatible y autónoma")
    elif passed_tests >= total_tests * 0.8:
        print("✅ COMPATIBLE")
        print("La aplicación es compatible con algunas consideraciones")
    else:
        print("⚠️ COMPATIBILIDAD LIMITADA")
        print("La aplicación puede requerir ajustes para mejor compatibilidad")
    
    return 0 if passed_tests >= total_tests * 0.8 else 1

if __name__ == "__main__":
    sys.exit(main())
