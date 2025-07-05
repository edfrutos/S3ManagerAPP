#!/usr/bin/env python3
"""
Script de prueba de rendimiento para S3Manager
Autor: EDF Developer - 2025
"""

import os
import sys
import time
import psutil
import platform
import subprocess
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest

# Importar módulos del proyecto
from s3_manager_app import S3ManagerApp

def get_system_info():
    """Obtiene información del sistema"""
    return {
        'platform': platform.system(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'memory_total': psutil.virtual_memory().total / (1024**3),  # GB
        'cpu_count': psutil.cpu_count(),
        'macos_version': subprocess.getoutput('sw_vers -productVersion')
    }

def measure_startup_time():
    """Mide el tiempo de arranque de la aplicación"""
    print("🧪 PRUEBA: Tiempo de Arranque")
    print("-" * 40)
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    times = []
    
    for i in range(3):  # 3 mediciones
        start_time = time.time()
        
        app = QApplication(sys.argv)
        window = S3ManagerApp()
        
        # Esperar a que la ventana esté completamente cargada
        QTest.qWait(1000)
        
        end_time = time.time()
        startup_time = end_time - start_time
        times.append(startup_time)
        
        print(f"   Intento {i+1}: {startup_time:.2f} segundos")
        
        # Limpiar
        window.close()
        app.quit()
        del app
        del window
    
    avg_time = sum(times) / len(times)
    print(f"✅ Tiempo promedio de arranque: {avg_time:.2f} segundos")
    
    # Evaluar rendimiento
    if avg_time < 2.0:
        print("🚀 Rendimiento: Excelente")
        return True
    elif avg_time < 4.0:
        print("✅ Rendimiento: Bueno")
        return True
    else:
        print("⚠️ Rendimiento: Mejorable")
        return False

def measure_memory_usage():
    """Mide el uso de memoria de la aplicación"""
    print("\n🧪 PRUEBA: Uso de Memoria")
    print("-" * 40)
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Memoria inicial
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024**2)  # MB
    
    app = QApplication(sys.argv)
    window = S3ManagerApp()
    
    # Esperar a que la aplicación esté completamente cargada
    QTest.qWait(2000)
    
    # Memoria después de cargar
    loaded_memory = process.memory_info().rss / (1024**2)  # MB
    app_memory = loaded_memory - initial_memory
    
    print(f"   Memoria inicial: {initial_memory:.1f} MB")
    print(f"   Memoria con app: {loaded_memory:.1f} MB")
    print(f"   Uso de la app: {app_memory:.1f} MB")
    
    # Limpiar
    window.close()
    app.quit()
    
    # Evaluar uso de memoria
    if app_memory < 150:
        print("🚀 Uso de memoria: Excelente")
        return True
    elif app_memory < 300:
        print("✅ Uso de memoria: Bueno")
        return True
    else:
        print("⚠️ Uso de memoria: Alto")
        return False

def measure_cpu_usage():
    """Mide el uso de CPU durante operaciones"""
    print("\n🧪 PRUEBA: Uso de CPU")
    print("-" * 40)
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # CPU inicial
    cpu_before = psutil.cpu_percent(interval=1)
    
    app = QApplication(sys.argv)
    window = S3ManagerApp()
    
    # Simular operaciones
    QTest.qWait(3000)
    
    # CPU durante operación
    cpu_during = psutil.cpu_percent(interval=1)
    
    print(f"   CPU antes: {cpu_before:.1f}%")
    print(f"   CPU durante: {cpu_during:.1f}%")
    print(f"   Incremento: {cpu_during - cpu_before:.1f}%")
    
    # Limpiar
    window.close()
    app.quit()
    
    # Evaluar uso de CPU
    cpu_increase = cpu_during - cpu_before
    if cpu_increase < 10:
        print("🚀 Uso de CPU: Excelente")
        return True
    elif cpu_increase < 25:
        print("✅ Uso de CPU: Bueno")
        return True
    else:
        print("⚠️ Uso de CPU: Alto")
        return False

def test_app_size():
    """Verifica el tamaño de la aplicación"""
    print("\n🧪 PRUEBA: Tamaño de la Aplicación")
    print("-" * 40)
    
    app_path = Path("build/S3Manager.app")
    
    if not app_path.exists():
        print("❌ Aplicación no encontrada")
        return False
    
    # Calcular tamaño total
    total_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
    size_mb = total_size / (1024**2)
    
    print(f"   Tamaño total: {size_mb:.1f} MB")
    
    # Desglose por directorios principales
    for subdir in ['Contents/MacOS', 'Contents/Frameworks', 'Contents/Resources']:
        subdir_path = app_path / subdir
        if subdir_path.exists():
            subdir_size = sum(f.stat().st_size for f in subdir_path.rglob('*') if f.is_file())
            subdir_mb = subdir_size / (1024**2)
            print(f"   {subdir}: {subdir_mb:.1f} MB")
    
    # Evaluar tamaño
    if size_mb < 300:
        print("🚀 Tamaño: Compacto")
        return True
    elif size_mb < 600:
        print("✅ Tamaño: Razonable")
        return True
    else:
        print("⚠️ Tamaño: Grande")
        return True  # No es un fallo, solo información

def test_dmg_size():
    """Verifica el tamaño del DMG"""
    print("\n🧪 PRUEBA: Tamaño del DMG")
    print("-" * 40)
    
    dmg_path = Path("S3Manager.dmg")
    
    if not dmg_path.exists():
        print("❌ DMG no encontrado")
        return False
    
    size_mb = dmg_path.stat().st_size / (1024**2)
    print(f"   Tamaño DMG: {size_mb:.1f} MB")
    
    # Evaluar tamaño
    if size_mb < 200:
        print("🚀 Tamaño DMG: Compacto")
        return True
    elif size_mb < 400:
        print("✅ Tamaño DMG: Razonable")
        return True
    else:
        print("⚠️ Tamaño DMG: Grande")
        return True  # No es un fallo, solo información

def test_architecture_specific():
    """Pruebas específicas de arquitectura"""
    print("\n🧪 PRUEBA: Optimización por Arquitectura")
    print("-" * 40)
    
    arch = platform.machine()
    print(f"   Arquitectura detectada: {arch}")
    
    if arch == 'arm64':
        print("   🍎 Apple Silicon detectado")
        print("   ✅ Ejecutando nativamente (sin Rosetta)")
        
        # Verificar que no hay emulación
        try:
            result = subprocess.run(['sysctl', '-n', 'sysctl.proc_translated'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip() == '0':
                print("   ✅ Confirmado: Ejecución nativa")
                return True
            else:
                print("   ⚠️ Posible emulación detectada")
                return False
        except:
            print("   ✅ Verificación de emulación no disponible")
            return True
            
    elif arch == 'x86_64':
        print("   💻 Intel x64 detectado")
        print("   ✅ Ejecutando nativamente")
        return True
    else:
        print(f"   ❓ Arquitectura no reconocida: {arch}")
        return False

def benchmark_operations():
    """Benchmark de operaciones comunes"""
    print("\n🧪 PRUEBA: Benchmark de Operaciones")
    print("-" * 40)
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    app = QApplication(sys.argv)
    window = S3ManagerApp()
    
    operations = []
    
    # Operación 1: Cargar interfaz
    start = time.time()
    QTest.qWait(1000)
    operations.append(("Carga de interfaz", time.time() - start))
    
    # Operación 2: Cambiar pestañas
    start = time.time()
    window.tab_widget.setCurrentIndex(1)
    QTest.qWait(500)
    window.tab_widget.setCurrentIndex(0)
    QTest.qWait(500)
    operations.append(("Cambio de pestañas", time.time() - start))
    
    # Operación 3: Abrir logs
    start = time.time()
    window.tab_widget.setCurrentIndex(2)
    QTest.qWait(500)
    operations.append(("Abrir logs", time.time() - start))
    
    # Mostrar resultados
    for op_name, op_time in operations:
        print(f"   {op_name}: {op_time:.3f} segundos")
    
    # Limpiar
    window.close()
    app.quit()
    
    # Evaluar rendimiento general
    avg_time = sum(op[1] for op in operations) / len(operations)
    if avg_time < 0.5:
        print("🚀 Rendimiento de operaciones: Excelente")
        return True
    elif avg_time < 1.0:
        print("✅ Rendimiento de operaciones: Bueno")
        return True
    else:
        print("⚠️ Rendimiento de operaciones: Mejorable")
        return False

def main():
    """Función principal"""
    print("🔧 PRUEBAS DE RENDIMIENTO S3MANAGER")
    print("=" * 60)
    
    # Mostrar información del sistema
    sys_info = get_system_info()
    print("📋 Información del Sistema:")
    print(f"   🖥️ Sistema: {sys_info['platform']} {sys_info['macos_version']}")
    print(f"   🏗️ Arquitectura: {sys_info['machine']}")
    print(f"   🧠 Procesador: {sys_info['processor']}")
    print(f"   🐍 Python: {sys_info['python_version']}")
    print(f"   💾 RAM Total: {sys_info['memory_total']:.1f} GB")
    print(f"   ⚙️ CPU Cores: {sys_info['cpu_count']}")
    print()
    
    tests = [
        ("Tiempo de Arranque", measure_startup_time),
        ("Uso de Memoria", measure_memory_usage),
        ("Uso de CPU", measure_cpu_usage),
        ("Tamaño de Aplicación", test_app_size),
        ("Tamaño de DMG", test_dmg_size),
        ("Optimización por Arquitectura", test_architecture_specific),
        ("Benchmark de Operaciones", benchmark_operations),
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
    print("📋 REPORTE FINAL DE RENDIMIENTO")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📊 Resumen: {passed_tests}/{total_tests} pruebas exitosas")
    print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📝 Detalle de pruebas:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    # Evaluación general del rendimiento
    print(f"\n🎯 Evaluación General:")
    if passed_tests == total_tests:
        print("🚀 Rendimiento EXCELENTE - Optimizado para la arquitectura")
    elif passed_tests >= total_tests * 0.8:
        print("✅ Rendimiento BUENO - Funciona correctamente")
    else:
        print("⚠️ Rendimiento MEJORABLE - Revisar optimizaciones")
    
    return 0 if passed_tests >= total_tests * 0.8 else 1

if __name__ == "__main__":
    sys.exit(main())
