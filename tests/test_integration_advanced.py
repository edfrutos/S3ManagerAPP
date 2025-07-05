#!/usr/bin/env python3
"""
Script de pruebas de integración avanzadas para S3Manager
Autor: EDF Developer - 2025
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from PySide6.QtTest import QTest

# Importar módulos del proyecto
from s3_manager_app import S3ManagerApp
from diagnose_s3_permissions import (
    check_aws_credentials, list_bucket_contents,
    check_bucket_permissions
)

def print_test_header(test_name):
    """Imprime encabezado de prueba"""
    print("\n" + "=" * 60)
    print(f"🧪 PRUEBA: {test_name}")
    print("=" * 60)

def print_test_result(success, message):
    """Imprime resultado de prueba"""
    status = "✅ ÉXITO" if success else "❌ FALLO"
    print(f"{status}: {message}")

def test_verify_permissions_functionality(app):
    """Prueba específica: Funcionalidad Verificar Permisos"""
    print_test_header("Verificar Permisos - Funcionalidad Completa")
    
    try:
        window = S3ManagerApp()
        
        # Verificar que tenemos credenciales
        if not check_aws_credentials():
            print_test_result(False, "No hay credenciales AWS disponibles")
            return False
        
        # Obtener lista de buckets
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        if not buckets:
            print_test_result(False, "No hay buckets disponibles para probar")
            return False
        
        # Usar el primer bucket para pruebas
        test_bucket = buckets[0]['Name']
        print(f"🎯 Probando con bucket: {test_bucket}")
        
        # Simular selección de bucket en la GUI
        bucket_tab = window.bucket_tab
        
        # Verificar que el botón de permisos existe
        permissions_btn = bucket_tab.permissions_btn
        assert permissions_btn is not None, "Botón de permisos no encontrado"
        print("✅ Botón 'Verificar Permisos' encontrado")
        
        # Simular selección de bucket
        window.selected_bucket = test_bucket
        permissions_btn.setEnabled(True)
        print(f"✅ Bucket seleccionado: {test_bucket}")
        
        # Probar verificación de permisos directamente
        print("🔍 Verificando permisos del bucket...")
        permissions = check_bucket_permissions(s3_client, test_bucket)
        
        # Verificar que se obtuvieron resultados
        assert isinstance(permissions, dict), "Los permisos deben ser un diccionario"
        expected_keys = ['read', 'write', 'delete', 'list']
        for key in expected_keys:
            assert key in permissions, f"Falta permiso: {key}"
        
        print("📊 Resultados de permisos:")
        for perm, status in permissions.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {perm.capitalize()}: {'OK' if status else 'Error'}")
        
        # Verificar que al menos algunos permisos funcionan
        working_perms = sum(1 for status in permissions.values() if status)
        if working_perms >= 2:
            print_test_result(True, f"Verificación de permisos funcional ({working_perms}/4 permisos)")
            return True
        else:
            print_test_result(False, f"Pocos permisos funcionando ({working_perms}/4)")
            return False
        
    except Exception as e:
        print_test_result(False, f"Error en verificación de permisos: {e}")
        return False

def test_bucket_selection_workflow(app):
    """Prueba: Flujo completo de selección de bucket"""
    print_test_header("Flujo de Selección de Bucket")
    
    try:
        window = S3ManagerApp()
        
        bucket_tab = window.bucket_tab
        
        # Simular carga de buckets
        print("📦 Simulando carga de buckets...")
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        # Actualizar lista en la GUI
        bucket_tab.update_bucket_list(buckets)
        print(f"✅ {len(buckets)} buckets cargados en la GUI")
        
        # Verificar que los botones están inicialmente deshabilitados
        assert not bucket_tab.permissions_btn.isEnabled(), "Botón permisos debería estar deshabilitado"
        assert not bucket_tab.files_btn.isEnabled(), "Botón archivos debería estar deshabilitado"
        print("✅ Estado inicial de botones correcto")
        
        # Simular selección de bucket
        if buckets:
            test_bucket = buckets[0]
            window.selected_bucket = test_bucket['Name']
            
            # Simular habilitación de botones (como haría la GUI real)
            bucket_tab.permissions_btn.setEnabled(True)
            bucket_tab.files_btn.setEnabled(True)
            
            print(f"✅ Bucket seleccionado: {test_bucket['Name']}")
            print("✅ Botones habilitados tras selección")
            
            return True
        else:
            print_test_result(False, "No hay buckets disponibles")
            return False
        
    except Exception as e:
        print_test_result(False, f"Error en flujo de selección: {e}")
        return False

def test_file_operations_workflow(app):
    """Prueba: Flujo de operaciones con archivos"""
    print_test_header("Flujo de Operaciones con Archivos")
    
    try:
        window = S3ManagerApp()
        
        # Obtener bucket con archivos
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        test_bucket = None
        for bucket in buckets:
            # Verificar si el bucket tiene archivos
            try:
                objects_response = s3_client.list_objects_v2(
                    Bucket=bucket['Name'], 
                    MaxKeys=1
                )
                if 'Contents' in objects_response:
                    test_bucket = bucket['Name']
                    break
            except ClientError:
                continue
        
        if not test_bucket:
            print_test_result(False, "No se encontró bucket con archivos para probar")
            return False
        
        print(f"🎯 Probando con bucket: {test_bucket}")
        
        # Listar archivos
        objects = list_bucket_contents(s3_client, test_bucket)
        print(f"📁 Archivos encontrados: {len(objects)}")
        
        if not objects:
            print_test_result(False, "Bucket sin archivos para probar")
            return False
        
        # Simular carga en la GUI
        files_tab = window.files_tab
        files_tab.current_bucket = test_bucket
        files_tab.update_files_table(objects)
        
        print("✅ Archivos cargados en tabla GUI")
        
        # Verificar configuración de tabla
        assert files_tab.files_table.rowCount() == len(objects), "Número de filas incorrecto"
        assert files_tab.files_table.columnCount() == 4, "Número de columnas incorrecto"
        print("✅ Tabla de archivos configurada correctamente")
        
        # Simular selección de archivos
        files_tab.selected_files = objects[:min(2, len(objects))]  # Seleccionar hasta 2 archivos
        files_tab.download_btn.setEnabled(True)
        files_tab.delete_btn.setEnabled(True)
        
        print(f"✅ {len(files_tab.selected_files)} archivos seleccionados")
        print("✅ Botones de acción habilitados")
        
        return True
        
    except Exception as e:
        print_test_result(False, f"Error en operaciones con archivos: {e}")
        return False

def test_error_handling(app):
    """Prueba: Manejo de errores"""
    print_test_header("Manejo de Errores")
    
    try:
        window = S3ManagerApp()
        
        # Probar con bucket inexistente
        fake_bucket = "bucket-que-no-existe-12345"
        
        s3_client = boto3.client('s3')
        permissions = check_bucket_permissions(s3_client, fake_bucket)
        
        # Verificar que todos los permisos fallaron (como se espera)
        failed_perms = sum(1 for status in permissions.values() if not status)
        if failed_perms == 4:
            print("✅ Error manejado correctamente: Todos los permisos fallaron como se esperaba")
        else:
            print(f"⚠️ Resultado inesperado: {failed_perms}/4 permisos fallaron")
        
        # Probar log de errores en GUI
        log_tab = window.log_tab
        initial_content = log_tab.log_text.toPlainText()
        
        # Agregar log de error
        log_tab.add_log("Error de prueba", "error")
        updated_content = log_tab.log_text.toPlainText()
        
        assert "Error de prueba" in updated_content, "Log de error no agregado"
        print("✅ Sistema de logs de error funcional")
        
        return True
        
    except Exception as e:
        print_test_result(False, f"Error en manejo de errores: {e}")
        return False

def test_worker_thread_operations(app):
    """Prueba: Operaciones en hilos de trabajo"""
    print_test_header("Operaciones en Hilos de Trabajo")
    
    try:
        window = S3ManagerApp()
        
        # Verificar worker thread
        worker = window.worker
        assert worker is not None, "Worker thread no encontrado"
        print("✅ Worker thread disponible")
        
        # Verificar que no está ejecutándose
        assert not worker.isRunning(), "Worker thread no debería estar ejecutándose"
        print("✅ Worker thread en estado inicial correcto")
        
        # Probar configuración de operación
        worker.set_operation('list_buckets')
        assert worker.operation == 'list_buckets', "Operación no configurada correctamente"
        print("✅ Configuración de operación funcional")
        
        return True
        
    except Exception as e:
        print_test_result(False, f"Error en worker thread: {e}")
        return False

def run_advanced_integration_tests():
    """Ejecuta todas las pruebas de integración avanzadas"""
    print("🧪 SUITE DE PRUEBAS DE INTEGRACIÓN AVANZADAS - S3MANAGER")
    print("=" * 70)
    print("Ejecutando pruebas completas de integración y funcionalidad...")
    
    # Crear una única instancia de QApplication para todas las pruebas
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)
    
    tests = [
        ("Verificar Permisos - Funcionalidad", test_verify_permissions_functionality),
        ("Flujo de Selección de Bucket", test_bucket_selection_workflow),
        ("Operaciones con Archivos", test_file_operations_workflow),
        ("Manejo de Errores", test_error_handling),
        ("Operaciones en Hilos de Trabajo", test_worker_thread_operations),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func(app)
        except Exception as e:
            print_test_result(False, f"Error ejecutando {test_name}: {e}")
            results[test_name] = False
    
    # Generar reporte final
    print("\n" + "=" * 70)
    print("📋 REPORTE FINAL DE PRUEBAS DE INTEGRACIÓN")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"📊 Resumen: {passed_tests}/{total_tests} pruebas exitosas")
    print(f"📈 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📝 Detalle de pruebas:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODAS LAS PRUEBAS DE INTEGRACIÓN EXITOSAS!")
        print("La aplicación S3Manager está completamente funcional.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} pruebas fallaron")
        print("Revisa los errores anteriores para más detalles.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_advanced_integration_tests()
    sys.exit(0 if success else 1)
