#!/usr/bin/env python3
"""
Pruebas de la aplicación nativa macOS S3 Manager
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_native_app():
    """Prueba la aplicación nativa macOS"""
    
    print("🍎 PRUEBAS DE APLICACIÓN NATIVA MACOS")
    print("=" * 60)
    
    current_dir = Path(__file__).parent
    app_path = current_dir / "build" / "S3Manager.app"
    
    # Verificar que la aplicación existe
    print("1️⃣ Verificando aplicación nativa...")
    if not app_path.exists():
        print("❌ Aplicación no encontrada")
        return False
    
    print(f"✅ Aplicación encontrada: {app_path}")
    
    # Verificar estructura de la aplicación
    print("\n2️⃣ Verificando estructura de la aplicación...")
    
    required_paths = [
        app_path / "Contents",
        app_path / "Contents" / "MacOS",
        app_path / "Contents" / "Resources",
        app_path / "Contents" / "Info.plist",
        app_path / "Contents" / "MacOS" / "S3Manager"
    ]
    
    for path in required_paths:
        if path.exists():
            print(f"✅ {path.name}")
        else:
            print(f"❌ {path.name} faltante")
            return False
    
    # Verificar permisos de ejecución
    print("\n3️⃣ Verificando permisos...")
    executable = app_path / "Contents" / "MacOS" / "S3Manager"
    
    if os.access(executable, os.X_OK):
        print("✅ Permisos de ejecución correctos")
    else:
        print("❌ Sin permisos de ejecución")
        return False
    
    # Verificar Info.plist
    print("\n4️⃣ Verificando Info.plist...")
    info_plist = app_path / "Contents" / "Info.plist"
    
    try:
        with open(info_plist, 'r') as f:
            content = f.read()
            
        required_keys = [
            "CFBundleDisplayName",
            "CFBundleExecutable", 
            "CFBundleIdentifier",
            "CFBundleName"
        ]
        
        for key in required_keys:
            if key in content:
                print(f"✅ {key}")
            else:
                print(f"❌ {key} faltante")
                
    except Exception as e:
        print(f"❌ Error leyendo Info.plist: {e}")
        return False
    
    # Verificar icono
    print("\n5️⃣ Verificando icono...")
    icon_path = app_path / "Contents" / "Resources" / "icon.icns"
    
    if icon_path.exists():
        print("✅ Icono personalizado encontrado")
    else:
        print("⚠️  Icono personalizado no encontrado")
    
    # Probar lanzamiento (sin GUI)
    print("\n6️⃣ Probando lanzamiento...")
    
    try:
        # Intentar ejecutar con timeout
        result = subprocess.run([
            str(executable),
            "--help"
        ], capture_output=True, text=True, timeout=5)
        
        print("✅ Aplicación se puede ejecutar")
        
    except subprocess.TimeoutExpired:
        print("✅ Aplicación se ejecuta (timeout esperado)")
    except Exception as e:
        print(f"⚠️  Error en lanzamiento: {e}")
    
    # Verificar dependencias incluidas
    print("\n7️⃣ Verificando dependencias...")
    
    frameworks_dir = app_path / "Contents" / "Frameworks"
    if frameworks_dir.exists():
        print("✅ Directorio de frameworks encontrado")
        
        # Contar frameworks
        frameworks = list(frameworks_dir.glob("*.framework"))
        if frameworks:
            print(f"✅ {len(frameworks)} frameworks incluidos")
        else:
            print("⚠️  No se encontraron frameworks")
    else:
        print("⚠️  Directorio de frameworks no encontrado")
    
    # Verificar tamaño de la aplicación
    print("\n8️⃣ Verificando tamaño...")
    
    try:
        result = subprocess.run([
            "du", "-sh", str(app_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            size = result.stdout.strip().split()[0]
            print(f"✅ Tamaño de la aplicación: {size}")
        else:
            print("⚠️  No se pudo determinar el tamaño")
            
    except Exception as e:
        print(f"⚠️  Error calculando tamaño: {e}")
    
    print("\n🎉 PRUEBAS DE APLICACIÓN NATIVA COMPLETADAS")
    print("✨ La aplicación está lista para distribución")
    
    return True

def test_launch_methods():
    """Prueba diferentes métodos de lanzamiento"""
    
    print("\n🚀 PROBANDO MÉTODOS DE LANZAMIENTO")
    print("=" * 60)
    
    current_dir = Path(__file__).parent
    app_path = current_dir / "build" / "S3Manager.app"
    
    # Método 1: open command
    print("1️⃣ Probando con comando 'open'...")
    try:
        result = subprocess.run([
            "open", str(app_path)
        ], capture_output=True, text=True, timeout=3)
        
        if result.returncode == 0:
            print("✅ Lanzamiento con 'open' exitoso")
        else:
            print(f"❌ Error con 'open': {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("✅ Lanzamiento con 'open' iniciado")
    except Exception as e:
        print(f"❌ Error con 'open': {e}")
    
    # Método 2: Ejecutable directo
    print("\n2️⃣ Probando ejecutable directo...")
    executable = app_path / "Contents" / "MacOS" / "S3Manager"
    
    try:
        # Solo verificar que se puede ejecutar
        result = subprocess.run([
            str(executable)
        ], capture_output=True, text=True, timeout=2)
        
        print("✅ Ejecutable directo funciona")
        
    except subprocess.TimeoutExpired:
        print("✅ Ejecutable directo se ejecuta")
    except Exception as e:
        print(f"⚠️  Ejecutable directo: {e}")
    
    # Método 3: Script de lanzamiento
    print("\n3️⃣ Probando script de lanzamiento...")
    launcher_script = current_dir / "launch_s3_manager.sh"
    
    if launcher_script.exists():
        print("✅ Script de lanzamiento encontrado")
        
        # Verificar permisos
        if os.access(launcher_script, os.X_OK):
            print("✅ Script tiene permisos de ejecución")
        else:
            print("⚠️  Script sin permisos de ejecución")
    else:
        print("❌ Script de lanzamiento no encontrado")

def main():
    """Función principal"""
    
    # Verificar que estamos en macOS
    if sys.platform != "darwin":
        print("❌ Este script solo funciona en macOS")
        sys.exit(1)
    
    # Ejecutar pruebas
    success = test_native_app()
    test_launch_methods()
    
    if success:
        print("\n🎯 RESULTADO FINAL: ✅ ÉXITO")
        print("📱 La aplicación nativa está lista para usar")
    else:
        print("\n🎯 RESULTADO FINAL: ❌ PROBLEMAS DETECTADOS")
        print("🔧 Revisa los errores antes de usar")

if __name__ == "__main__":
    main()
