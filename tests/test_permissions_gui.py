#!/usr/bin/env python3
"""
Script de prueba específico para la funcionalidad "Ver Permisos" en la GUI
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

# Establecer modo de prueba para deshabilitar interacciones con el llavero (keychain)
os.environ['TEST_MODE'] = '1'

# Añadir el directorio raíz del proyecto al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from s3_manager_app import S3ManagerApp
from diagnose_s3_permissions import check_aws_credentials
import boto3

def test_permissions_gui():
    """Prueba específica de la funcionalidad Ver Permisos en la GUI"""
    print(" PRUEBA ESPECÍFICA: Funcionalidad 'Ver Permisos' en GUI")
    print("🧪 PRUEBA ESPECÍFICA: Funcionalidad 'Ver Permisos' en GUI")
    print("=" * 60)
    
    # Verificar credenciales
    if not check_aws_credentials():
        print("❌ No hay credenciales AWS disponibles")
        return False
    
    # Configurar aplicación
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
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
        print("✅ Buckets cargados en GUI")
        
        # Simular selección de bucket
        window.selected_bucket = test_bucket
        bucket_tab.permissions_btn.setEnabled(True)
        print(f"✅ Bucket seleccionado: {test_bucket}")
        
        # Verificar estado inicial de la información del bucket
        initial_info = bucket_tab.bucket_info.toPlainText()
        print(f"📋 Información inicial: {initial_info}")
        
        # Simular clic en "Verificar Permisos"
        print("🔍 Simulando verificación de permisos...")
        
        # Crear un flag para saber cuándo termina la operación
        operation_completed = False
        result_message = ""
        
        def on_operation_completed(success, message):
            nonlocal operation_completed, result_message
            operation_completed = True
            result_message = message
            print(f"📊 Operación completada: {success}")
            if success:
                print("📝 Mensaje recibido:")
                for line in message.split('\n'):
                    if line.strip():
                        print(f"   {line}")
        
        # Conectar señal
        window.worker.operation_completed.connect(on_operation_completed)
        
        # Ejecutar verificación de permisos
        window.start_operation('check_permissions', bucket_name=test_bucket)
        
        # Esperar a que termine la operación (máximo 10 segundos)
        timeout = 100  # 10 segundos
        while not operation_completed and timeout > 0:
            app.processEvents()
            QTest.qWait(100)
            timeout -= 1
        
        if operation_completed:
            print("✅ Verificación de permisos completada")
            
            # Verificar que se recibió información detallada
            if "Resultados de verificación" in result_message:
                print("✅ Mensaje detallado recibido")
                
                # Verificar que contiene información de permisos
                if "Permisos:" in result_message:
                    print("✅ Información de permisos incluida")
                    
                    # Verificar que contiene región
                    if "Región:" in result_message:
                        print("✅ Información de región incluida")
                        
                        # Esperar a que se actualice la información del bucket
                        QTest.qWait(1500)
                        
                        # Verificar información actualizada del bucket
                        updated_info = bucket_tab.bucket_info.toPlainText()
                        print(f"📋 Información actualizada: {updated_info}")
                        
                        if "Detectando..." not in updated_info:
                            print("✅ Región actualizada correctamente")
                            return True
                        else:
                            print("⚠️ Región no se actualizó")
                            return False
                    else:
                        print("❌ Información de región no incluida")
                        return False
                else:
                    print("❌ Información de permisos no incluida")
                    return False
            else:
                print("❌ Mensaje detallado no recibido")
                return False
        else:
            print("❌ Timeout: Operación no completada")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False
    
    finally:
        app.quit()

def main():
    """Función principal"""
    print("🔧 PRUEBA DE FUNCIONALIDAD 'VER PERMISOS'")
    print("=" * 50)
    
    success = test_permissions_gui()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡PRUEBA EXITOSA!")
        print("La funcionalidad 'Ver Permisos' está funcionando correctamente")
    else:
        print("❌ PRUEBA FALLIDA")
        print("La funcionalidad 'Ver Permisos' necesita corrección")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
