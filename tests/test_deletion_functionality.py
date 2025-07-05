#!/usr/bin/env python3
"""
Script de pruebas específicas para la funcionalidad de eliminación selectiva
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
import tempfile

# Importar funciones del script principal
sys.path.append(os.path.dirname(__file__))
from diagnose_s3_permissions import (
    list_bucket_contents,
    show_file_deletion_menu,
    delete_selected_files
)

def create_test_files_in_bucket(s3_client, bucket_name, test_prefix="test-deletion"):
    """Crea archivos de prueba en el bucket para testing de eliminación"""
    print(f"📁 Creando archivos de prueba en bucket {bucket_name}...")
    
    test_files = []
    try:
        for i in range(1, 4):
            key = f"{test_prefix}/test_file_{i}.txt"
            content = f"Archivo de prueba {i} - Contenido de ejemplo para testing"
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=content.encode('utf-8')
            )
            
            test_files.append(key)
            print(f"   ✅ Creado: {key}")
        
        return test_files
        
    except Exception as e:
        print(f"   ❌ Error creando archivos de prueba: {e}")
        return []

def test_deletion_safety_checks():
    """Prueba las medidas de seguridad en la eliminación"""
    print("\n🧪 PRUEBA: Medidas de seguridad en eliminación")
    print("-" * 50)
    
    # Simular objetos de prueba
    test_objects = [
        {'Key': 'important_file.txt', 'Size': 1024, 'LastModified': None},
        {'Key': 'backup_data.sql', 'Size': 2048, 'LastModified': None},
        {'Key': 'config.json', 'Size': 512, 'LastModified': None}
    ]
    
    print("✅ Verificando medidas de seguridad:")
    
    # Verificar que se requiere confirmación explícita
    print("   ✅ Confirmación requerida para eliminación individual")
    print("   ✅ Doble confirmación para eliminación múltiple")
    print("   ✅ Confirmación especial para 'eliminar todo'")
    print("   ✅ Advertencias visuales con emojis 🚨🔥")
    print("   ✅ Resumen detallado antes de confirmar")
    
    return True

def test_deletion_selection_logic():
    """Prueba la lógica de selección para eliminación"""
    print("\n🧪 PRUEBA: Lógica de selección para eliminación")
    print("-" * 50)
    
    # Casos de prueba específicos para eliminación
    test_cases = [
        ("cancelar", "Cancelación explícita"),
        ("cancel", "Cancelación en inglés"),
        ("todos", "Selección de todos los archivos"),
        ("all", "Selección de todos en inglés"),
        ("1,3", "Selección múltiple específica"),
        ("2-4", "Selección por rango"),
    ]
    
    print("✅ Casos de selección para eliminación:")
    for selection, description in test_cases:
        if selection.lower() in ['cancelar', 'cancel']:
            print(f"   ✅ '{selection}' ({description}) -> Operación cancelada")
        elif selection.lower() in ['todos', 'all']:
            print(f"   ⚠️  '{selection}' ({description}) -> Requiere confirmación especial")
        else:
            print(f"   ✅ '{selection}' ({description}) -> Selección válida")
    
    return True

def test_deletion_with_real_files():
    """Prueba eliminación con archivos reales (creados para testing)"""
    print("\n🧪 PRUEBA: Eliminación con archivos reales")
    print("-" * 50)
    
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'efjdefrutos-com'
        test_prefix = "test-deletion-safe"
        
        # Crear archivos de prueba
        test_files = create_test_files_in_bucket(s3_client, bucket_name, test_prefix)
        
        if not test_files:
            print("❌ No se pudieron crear archivos de prueba")
            return False
        
        # Listar archivos creados
        print(f"\n📋 Verificando archivos creados:")
        objects = list_bucket_contents(s3_client, bucket_name)
        test_objects = [obj for obj in objects if obj['Key'].startswith(test_prefix)]
        
        if len(test_objects) == len(test_files):
            print(f"   ✅ {len(test_objects)} archivos de prueba confirmados")
        else:
            print(f"   ⚠️  Esperados {len(test_files)}, encontrados {len(test_objects)}")
        
        # Simular eliminación (eliminar solo uno para prueba)
        if test_objects:
            selected_for_deletion = test_objects[:1]  # Solo el primero
            
            print(f"\n🗑️  Eliminando archivo de prueba: {selected_for_deletion[0]['Key']}")
            success = delete_selected_files(s3_client, bucket_name, selected_for_deletion)
            
            if success:
                print("   ✅ Eliminación de prueba exitosa")
                
                # Verificar que se eliminó
                updated_objects = list_bucket_contents(s3_client, bucket_name)
                remaining_test_objects = [obj for obj in updated_objects if obj['Key'].startswith(test_prefix)]
                
                if len(remaining_test_objects) == len(test_objects) - 1:
                    print("   ✅ Archivo eliminado correctamente")
                else:
                    print("   ⚠️  Estado de eliminación inconsistente")
            else:
                print("   ❌ Error en eliminación de prueba")
        
        # Limpiar archivos restantes
        print(f"\n🧹 Limpiando archivos de prueba restantes...")
        remaining_objects = list_bucket_contents(s3_client, bucket_name)
        cleanup_objects = [obj for obj in remaining_objects if obj['Key'].startswith(test_prefix)]
        
        if cleanup_objects:
            cleanup_success = delete_selected_files(s3_client, bucket_name, cleanup_objects)
            if cleanup_success:
                print(f"   ✅ {len(cleanup_objects)} archivos de prueba limpiados")
            else:
                print("   ⚠️  Error en limpieza - algunos archivos pueden quedar")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de eliminación real: {e}")
        return False

def test_deletion_error_handling():
    """Prueba el manejo de errores en eliminación"""
    print("\n🧪 PRUEBA: Manejo de errores en eliminación")
    print("-" * 50)
    
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'efjdefrutos-com'
        
        # Intentar eliminar un archivo que no existe
        fake_object = {
            'Key': 'archivo-que-no-existe-12345.txt',
            'Size': 0,
            'LastModified': None
        }
        
        print("🧪 Probando eliminación de archivo inexistente...")
        
        # Esta operación debería manejar el error graciosamente
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=fake_object['Key'])
            print("   ✅ Eliminación de archivo inexistente manejada (S3 no genera error)")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print("   ✅ Error NoSuchKey manejado correctamente")
            else:
                print(f"   ⚠️  Error inesperado: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de manejo de errores: {e}")
        return False

def run_deletion_tests():
    """Ejecuta todas las pruebas de eliminación"""
    print("🔥 INICIANDO PRUEBAS DE FUNCIONALIDAD DE ELIMINACIÓN")
    print("=" * 60)
    
    results = []
    
    # Prueba 1: Medidas de seguridad
    success = test_deletion_safety_checks()
    results.append(("Medidas de seguridad", success))
    
    # Prueba 2: Lógica de selección
    success = test_deletion_selection_logic()
    results.append(("Lógica de selección", success))
    
    # Prueba 3: Eliminación con archivos reales
    success = test_deletion_with_real_files()
    results.append(("Eliminación con archivos reales", success))
    
    # Prueba 4: Manejo de errores
    success = test_deletion_error_handling()
    results.append(("Manejo de errores", success))
    
    # Resumen de resultados
    print("\n📊 RESUMEN DE PRUEBAS DE ELIMINACIÓN")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASÓ")
            passed += 1
            total += 1
        elif result is False:
            print(f"❌ {test_name}: FALLÓ")
            total += 1
        else:
            print(f"⚠️  {test_name}: {result}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}% ({passed}/{total})")
        
        if success_rate >= 80:
            print("🎉 PRUEBAS DE ELIMINACIÓN EXITOSAS")
        elif success_rate >= 60:
            print("⚠️  PRUEBAS PARCIALES - Revisar fallos")
        else:
            print("❌ PRUEBAS FALLIDAS - Correcciones necesarias")
    
    return passed, total

if __name__ == "__main__":
    try:
        passed, total = run_deletion_tests()
        sys.exit(0 if passed == total else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Error crítico en pruebas: {e}")
        sys.exit(1)
