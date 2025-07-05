#!/usr/bin/env python3
"""
Script de prueba para el instalador DMG de S3Manager
Autor: EDF Developer - 2025
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import time

def run_command(command, timeout=30):
    """Ejecuta un comando con timeout"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"

def test_dmg_exists():
    """Verifica que el DMG existe"""
    print("🧪 PRUEBA: Existencia del DMG")
    print("-" * 40)
    
    dmg_path = "S3Manager.dmg"
    if os.path.exists(dmg_path):
        size = os.path.getsize(dmg_path) / (1024 * 1024)
        print(f"✅ DMG encontrado: {dmg_path}")
        print(f"📏 Tamaño: {size:.1f} MB")
        return True
    else:
        print(f"❌ DMG no encontrado: {dmg_path}")
        return False

def test_dmg_mount():
    """Prueba montar y desmontar el DMG"""
    print("\n🧪 PRUEBA: Montaje del DMG")
    print("-" * 40)
    
    dmg_path = "S3Manager.dmg"
    mount_point = "/Volumes/S3Manager"
    
    # Desmontar si ya está montado
    run_command(f'hdiutil detach "{mount_point}" 2>/dev/null')
    
    # Montar DMG
    success, stdout, stderr = run_command(f'hdiutil attach "{dmg_path}" -mountpoint "{mount_point}"')
    
    if success:
        print("✅ DMG montado exitosamente")
        
        # Verificar contenido
        if os.path.exists(f"{mount_point}/S3Manager.app"):
            print("✅ S3Manager.app encontrado en DMG")
        else:
            print("❌ S3Manager.app no encontrado en DMG")
            return False
        
        if os.path.exists(f"{mount_point}/Applications"):
            print("✅ Enlace a Applications encontrado")
        else:
            print("❌ Enlace a Applications no encontrado")
        
        if os.path.exists(f"{mount_point}/README.txt"):
            print("✅ README.txt encontrado")
        else:
            print("❌ README.txt no encontrado")
        
        # Desmontar
        success_unmount, _, _ = run_command(f'hdiutil detach "{mount_point}"')
        if success_unmount:
            print("✅ DMG desmontado exitosamente")
            return True
        else:
            print("⚠️ Error desmontando DMG")
            return False
    else:
        print(f"❌ Error montando DMG: {stderr}")
        return False

def test_dmg_installation_simulation():
    """Simula la instalación desde DMG"""
    print("\n🧪 PRUEBA: Simulación de Instalación")
    print("-" * 40)
    
    dmg_path = "S3Manager.dmg"
    mount_point = "/Volumes/S3Manager"
    
    # Crear directorio temporal para simular /Applications
    with tempfile.TemporaryDirectory() as temp_apps:
        print(f"📁 Simulando instalación en: {temp_apps}")
        
        # Montar DMG
        success, _, _ = run_command(f'hdiutil attach "{dmg_path}" -mountpoint "{mount_point}"')
        
        if not success:
            print("❌ No se pudo montar DMG")
            return False
        
        try:
            # Simular arrastrar a Applications
            app_source = f"{mount_point}/S3Manager.app"
            app_dest = f"{temp_apps}/S3Manager.app"
            
            success, _, stderr = run_command(f'cp -R "{app_source}" "{app_dest}"')
            
            if success:
                print("✅ Aplicación copiada exitosamente")
                
                # Verificar estructura de la aplicación instalada
                if os.path.exists(f"{app_dest}/Contents/Info.plist"):
                    print("✅ Info.plist presente")
                else:
                    print("❌ Info.plist faltante")
                    return False
                
                if os.path.exists(f"{app_dest}/Contents/MacOS"):
                    print("✅ Directorio MacOS presente")
                else:
                    print("❌ Directorio MacOS faltante")
                    return False
                
                if os.path.exists(f"{app_dest}/Contents/Resources"):
                    print("✅ Directorio Resources presente")
                else:
                    print("❌ Directorio Resources faltante")
                    return False
                
                return True
            else:
                print(f"❌ Error copiando aplicación: {stderr}")
                return False
                
        finally:
            # Desmontar DMG
            run_command(f'hdiutil detach "{mount_point}"')

def test_dmg_integrity():
    """Verifica la integridad del DMG"""
    print("\n🧪 PRUEBA: Integridad del DMG")
    print("-" * 40)
    
    dmg_path = "S3Manager.dmg"
    
    # Verificar integridad
    success, stdout, stderr = run_command(f'hdiutil verify "{dmg_path}"')
    
    if success:
        print("✅ DMG verificado - integridad correcta")
        return True
    else:
        print(f"❌ Error de integridad: {stderr}")
        return False

def test_dmg_compatibility():
    """Prueba compatibilidad del DMG"""
    print("\n🧪 PRUEBA: Compatibilidad del DMG")
    print("-" * 40)
    
    dmg_path = "S3Manager.dmg"
    
    # Obtener información del DMG
    success, stdout, stderr = run_command(f'hdiutil imageinfo "{dmg_path}"')
    
    if success:
        print("✅ Información del DMG obtenida")
        
        # Buscar formato
        if "Format: UDZO" in stdout:
            print("✅ Formato UDZO (comprimido) - Compatible")
        else:
            print("⚠️ Formato no estándar")
        
        # Buscar sistema de archivos
        if "Apple_HFS" in stdout:
            print("✅ Sistema de archivos HFS+ - Compatible")
        else:
            print("⚠️ Sistema de archivos no estándar")
        
        return True
    else:
        print(f"❌ Error obteniendo información: {stderr}")
        return False

def main():
    """Función principal"""
    print("🔧 PRUEBAS DEL INSTALADOR DMG S3MANAGER")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("S3Manager.dmg"):
        print("❌ Error: S3Manager.dmg no encontrado")
        print("Ejecuta este script desde el directorio tools/aws_utils")
        return 1
    
    tests = [
        ("Existencia del DMG", test_dmg_exists),
        ("Montaje del DMG", test_dmg_mount),
        ("Simulación de Instalación", test_dmg_installation_simulation),
        ("Integridad del DMG", test_dmg_integrity),
        ("Compatibilidad del DMG", test_dmg_compatibility),
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
    print("📋 REPORTE FINAL DE PRUEBAS DMG")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📊 Resumen: {passed_tests}/{total_tests} pruebas exitosas")
    print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📝 Detalle de pruebas:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODAS LAS PRUEBAS DMG EXITOSAS!")
        print("El instalador DMG está completamente funcional.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} pruebas fallaron")
        print("Revisa los errores anteriores para más detalles.")
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
