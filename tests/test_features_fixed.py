#!/usr/bin/env python3
"""
Script de prueba completo para todas las funcionalidades de S3Manager
Incluye: Ver Permisos y Configuración de Credenciales
Autor: EDF Developer - 2025
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest

# Importar módulos del proyecto
from s3_manager_app import S3ManagerApp, AWSConfigDialog
from diagnose_s3_permissions import check_aws_credentials
import boto3

def test_permissions_display(app):
    """Prueba la visualización de permisos en la GUI"""
    print("🧪 PRUEBA: Visualización de Permisos")
    print("-" * 40)
    
    # Verificar credenciales
    if not check_aws_credentials():
        print("❌ No hay credenciales AWS disponibles")
        return False
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Obtener buckets disponibles
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        if not buckets:
            print("❌ No hay buckets disponibles para probar")
            return False
        
        test_bucket = buckets[0]['Name']
        print(f"🎯 Probando con bucket: {test_bucket}")
        
        # Simular carga de buckets en la GUI
        bucket_tab = window.bucket_tab
        bucket_tab.update_bucket_list(buckets)
        
        # Simular selección de bucket
        window.selected_bucket = test_bucket
        bucket_tab.permissions_btn.setEnabled(True)
        
        # Verificar información inicial
        initial_info = bucket_tab.bucket_info.toPlainText()
        print(f"📋 Información inicial: {len(initial_info)} caracteres")
        
        # Simular verificación de permisos
        print("🔍 Ejecutando verificación de permisos...")
        bucket_tab.check_permissions()
        
        # Esperar a que se complete la operación
        QTest.qWait(3000)  # 3 segundos
        
        # Verificar información actualizada
        updated_info = bucket_tab.bucket_info.toPlainText()
        print(f"📋 Información actualizada: {len(updated_info)} caracteres")
        
        # Verificar que la información se actualizó
        if len(updated_info) > len(initial_info):
            print("✅ Información de permisos actualizada")
            
            # Verificar contenido específico
            if "PERMISOS:" in updated_info:
                print("✅ Sección de permisos presente")
                
                if "Región:" in updated_info and "Detectando..." not in updated_info:
                    print("✅ Región detectada correctamente")
                    return True
                else:
                    print("❌ Región no detectada")
                    return False
            else:
                print("❌ Sección de permisos no presente")
                return False
        else:
            print("❌ Información no se actualizó")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_config_dialog(app):
    """Prueba el diálogo de configuración de credenciales"""
    print("\n🧪 PRUEBA: Diálogo de Configuración")
    print("-" * 40)
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Crear diálogo de configuración
        dialog = AWSConfigDialog(window)
        print("✅ Diálogo de configuración creado")
        
        # Verificar campos del diálogo
        if hasattr(dialog, 'access_key_input') and hasattr(dialog, 'secret_key_input'):
            print("✅ Campos de credenciales presentes")
            
            # Verificar que los campos tienen valores actuales
            current_access_key = dialog.access_key_input.text()
            current_secret_key = dialog.secret_key_input.text()
            
            if current_access_key:
                print(f"✅ Access Key cargado: {current_access_key[:8]}...")
            else:
                print("⚠️ Access Key vacío")
            
            if current_secret_key:
                print("✅ Secret Key cargado (oculto)")
            else:
                print("⚠️ Secret Key vacío")
            
            # Verificar que el campo secret key está oculto
            if dialog.secret_key_input.echoMode() == dialog.secret_key_input.EchoMode.Password:
                print("✅ Secret Key está oculto correctamente")
            else:
                print("❌ Secret Key no está oculto")
                return False
            
            return True
        else:
            print("❌ Campos de credenciales no encontrados")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def test_menu_integration(app):
    """Prueba la integración del menú de configuración"""
    print("\n🧪 PRUEBA: Integración de Menú")
    print("-" * 40)
    
    try:
        # Crear ventana principal
        window = S3ManagerApp()
        print("✅ Aplicación GUI creada")
        
        # Verificar que el menú tiene la opción de configuración
        menubar = window.menuBar()
        file_menu = None
        
        for action in menubar.actions():
            if action.text() == 'Archivo':
                file_menu = action.menu()
                break
        
        if file_menu:
            print("✅ Menú Archivo encontrado")
            
            # Buscar acción de configuración
            config_action = None
            for action in file_menu.actions():
                if 'Configuración AWS' in action.text():
                    config_action = action
                    break
            
            if config_action:
                print("✅ Opción 'Configuración AWS' encontrada en menú")
                return True
            else:
                print("❌ Opción 'Configuración AWS' no encontrada")
                return False
        else:
            print("❌ Menú Archivo no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 PRUEBAS COMPLETAS DE FUNCIONALIDADES S3MANAGER")
    print("=" * 60)
    
    # Configurar aplicación una sola vez
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
    tests = [
        ("Visualización de Permisos", test_permissions_display),
        ("Diálogo de Configuración", test_config_dialog),
        ("Integración de Menú", test_menu_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func(app)
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results[test_name] = False
    
    # Generar reporte final
    print("\n" + "=" * 60)
    print("📋 REPORTE FINAL DE PRUEBAS")
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
        print("\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("Las funcionalidades están completamente operativas.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} pruebas fallaron")
        print("Revisa los errores anteriores para más detalles.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
