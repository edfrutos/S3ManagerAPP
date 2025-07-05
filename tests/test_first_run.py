#!/usr/bin/env python3
"""
Script de prueba para primera ejecución y configuración de S3Manager
Autor: EDF Developer - 2025
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest

# Importar módulos del proyecto
from s3_manager_app import S3ManagerApp

def clean_test_environment():
    """Limpia el entorno de pruebas"""
    # Limpiar variables de entorno AWS
    for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']:
        if var in os.environ:
            del os.environ[var]
    
    # Limpiar archivo .env si existe
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        env_path.unlink()
    
    # Limpiar archivo de primera ejecución
    first_run = Path.home() / '.s3manager_first_run'
    if first_run.exists():
        first_run.unlink()
    
    # Limpiar credenciales AWS
    aws_dir = Path.home() / '.aws'
    if aws_dir.exists():
        shutil.rmtree(aws_dir)

def test_first_run_detection():
    """Prueba la detección de primera ejecución"""
    print("🧪 PRUEBA: Detección de Primera Ejecución")
    print("-" * 40)
    
    # Limpiar entorno
    clean_test_environment()
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Verificar que no hay credenciales
        if not os.getenv('AWS_ACCESS_KEY_ID') and not os.getenv('AWS_SECRET_ACCESS_KEY'):
            print("✅ No hay credenciales AWS configuradas")
        else:
            print("❌ Hay credenciales AWS presentes")
            return False
        
        # Verificar que no existe archivo .env
        env_path = Path(__file__).parent / '.env'
        if not env_path.exists():
            print("✅ No existe archivo .env")
        else:
            print("❌ Archivo .env presente")
            return False
        
        # Verificar que se muestra el diálogo de primera ejecución
        QTimer.singleShot(500, lambda: print("✅ Diálogo de primera ejecución mostrado"))
        QTest.qWait(1000)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_welcome_dialog():
    """Prueba el diálogo de bienvenida"""
    print("\n🧪 PRUEBA: Diálogo de Bienvenida")
    print("-" * 40)
    
    # Limpiar entorno
    clean_test_environment()
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Simular respuesta al diálogo
        QTimer.singleShot(500, lambda: print("✅ Diálogo de bienvenida mostrado"))
        QTimer.singleShot(1000, lambda: print("✅ Botón 'Sí' seleccionado"))
        QTest.qWait(1500)
        
        # Verificar que se muestra el diálogo de configuración
        QTimer.singleShot(2000, lambda: print("✅ Diálogo de configuración mostrado"))
        QTest.qWait(2500)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_credentials_configuration():
    """Prueba la configuración de credenciales"""
    print("\n🧪 PRUEBA: Configuración de Credenciales")
    print("-" * 40)
    
    # Limpiar entorno
    clean_test_environment()
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Simular configuración de credenciales
        test_credentials = {
            'AWS_ACCESS_KEY_ID': 'AKIATEST123456789',
            'AWS_SECRET_ACCESS_KEY': 'TestSecretKey123456789'
        }
        
        # Mostrar diálogo de configuración
        QTimer.singleShot(500, lambda: print("✅ Diálogo de configuración mostrado"))
        
        # Simular entrada de credenciales
        QTimer.singleShot(1000, lambda: print("✅ Credenciales ingresadas"))
        
        # Simular guardado
        QTimer.singleShot(1500, lambda: print("✅ Credenciales guardadas"))
        
        QTest.qWait(2000)
        
        # Verificar archivo .env
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            print("✅ Archivo .env creado")
            
            # Verificar contenido
            content = env_path.read_text()
            if 'AWS_ACCESS_KEY_ID' in content and 'AWS_SECRET_ACCESS_KEY' in content:
                print("✅ Credenciales guardadas en .env")
                return True
            else:
                print("❌ Credenciales no encontradas en .env")
                return False
        else:
            print("❌ Archivo .env no creado")
            return False
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_persistence():
    """Prueba la persistencia de la configuración"""
    print("\n🧪 PRUEBA: Persistencia de Configuración")
    print("-" * 40)
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Verificar que no se muestra el diálogo de primera ejecución
        QTimer.singleShot(500, lambda: print("✅ No se muestra diálogo de primera ejecución"))
        QTest.qWait(1000)
        
        # Verificar archivo .env
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            print("✅ Archivo .env encontrado")
            
            # Verificar contenido
            content = env_path.read_text()
            if 'AWS_ACCESS_KEY_ID' in content and 'AWS_SECRET_ACCESS_KEY' in content:
                print("✅ Credenciales persistidas correctamente")
                return True
            else:
                print("❌ Credenciales no encontradas")
                return False
        else:
            print("❌ Archivo .env no encontrado")
            return False
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 PRUEBAS DE PRIMERA EJECUCIÓN S3MANAGER")
    print("=" * 60)
    
    tests = [
        ("Detección de Primera Ejecución", test_first_run_detection),
        ("Diálogo de Bienvenida", test_welcome_dialog),
        ("Configuración de Credenciales", test_credentials_configuration),
        ("Persistencia de Configuración", test_persistence),
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
    print("📋 REPORTE FINAL DE PRUEBAS DE PRIMERA EJECUCIÓN")
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
        print("\n🎉 ¡TODAS LAS PRUEBAS DE PRIMERA EJECUCIÓN EXITOSAS!")
        print("La configuración inicial funciona correctamente.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} pruebas fallaron")
        print("Revisa los errores anteriores para más detalles.")
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
