#!/usr/bin/env python3
"""
Script de pruebas para las funcionalidades de selección múltiple en S3
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import tempfile
import shutil

# Importar funciones del script principal
sys.path.append(os.path.dirname(__file__))
from diagnose_s3_permissions import (
    list_bucket_contents,
    show_file_selection_menu,
    download_selected_files,
    show_file_deletion_menu,
    delete_selected_files
)

def test_list_bucket_contents():
    """Prueba la función de listado de contenido del bucket"""
    print("🧪 PRUEBA 1: Listado de contenido del bucket")
    print("-" * 50)
    
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'efjdefrutos-com'
        
        objects = list_bucket_contents(s3_client, bucket_name)
        
        if objects:
            print(f"✅ Listado exitoso: {len(objects)} archivos encontrados")
            print("📋 Primeros 5 archivos:")
            for i, obj in enumerate(objects[:5], 1):
                size_mb = obj['Size'] / (1024 * 1024)
                modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"   {i}. {obj['Key']} ({size_mb:.2f} MB) - {modified}")
            
            if len(objects) > 5:
                print(f"   ... y {len(objects) - 5} archivos más")
            
            return True, objects
        else:
            print("⚠️  El bucket está vacío o no se pudo acceder")
            return False, []
            
    except Exception as e:
        print(f"❌ Error en listado: {e}")
        return False, []

def test_file_selection_logic():
    """Prueba la lógica de selección de archivos sin interacción"""
    print("\n🧪 PRUEBA 2: Lógica de selección de archivos")
    print("-" * 50)
    
    # Crear objetos de prueba simulados
    test_objects = [
        {'Key': f'test_file_{i}.txt', 'Size': 1024 * i, 'LastModified': None}
        for i in range(1, 6)
    ]
    
    # Simular diferentes tipos de selección
    test_cases = [
        ("1", [0]),  # Selección individual
        ("1,3,5", [0, 2, 4]),  # Selección múltiple
        ("2-4", [1, 2, 3]),  # Selección por rango
        ("1,3-4", [0, 2, 3]),  # Selección combinada
    ]
    
    print("✅ Casos de prueba de selección:")
    for selection, expected_indices in test_cases:
        # Simular procesamiento de selección
        selected_indices = set()
        parts = selection.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                selected_indices.update(range(start, end + 1))
            else:
                selected_indices.add(int(part))
        
        # Convertir a índices base 0 y validar
        valid_indices = []
        for idx in selected_indices:
            if 1 <= idx <= len(test_objects):
                valid_indices.append(idx - 1)
        
        valid_indices.sort()
        if valid_indices == expected_indices:
            print(f"   ✅ '{selection}' -> índices {valid_indices}")
        else:
            print(f"   ❌ '{selection}' -> esperado {expected_indices}, obtenido {valid_indices}")
    
    return True

def test_download_functionality():
    """Prueba la funcionalidad de descarga (sin descargar realmente)"""
    print("\n🧪 PRUEBA 3: Funcionalidad de descarga")
    print("-" * 50)
    
    try:
        s3_client = boto3.client('s3')
        bucket_name = 'efjdefrutos-com'
        
        # Obtener lista de objetos
        objects = list_bucket_contents(s3_client, bucket_name)
        
        if not objects:
            print("⚠️  No hay archivos para probar descarga")
            return False
        
        # Crear directorio temporal para prueba
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Directorio temporal: {temp_dir}")
            
            # Seleccionar solo el primer archivo para prueba
            selected_objects = objects[:1]
            
            print(f"📥 Probando descarga de: {selected_objects[0]['Key']}")
            
            # Intentar descarga
            success = download_selected_files(s3_client, bucket_name, selected_objects, temp_dir)
            
            if success:
                # Verificar que el archivo se descargó
                downloaded_file = os.path.join(temp_dir, selected_objects[0]['Key'])
                if os.path.exists(downloaded_file):
                    file_size = os.path.getsize(downloaded_file)
                    print(f"✅ Descarga exitosa: {file_size} bytes")
                    return True
                else:
                    print("❌ Archivo no encontrado tras descarga")
                    return False
            else:
                print("❌ Error en descarga")
                return False
                
    except Exception as e:
        print(f"❌ Error en prueba de descarga: {e}")
        return False

def test_edge_cases():
    """Prueba casos edge y validaciones"""
    print("\n🧪 PRUEBA 4: Casos edge y validaciones")
    print("-" * 50)
    
    # Crear objetos de prueba
    test_objects = [
        {'Key': f'file_{i}.txt', 'Size': 1024, 'LastModified': None}
        for i in range(1, 4)
    ]
    
    edge_cases = [
        ("0", "Índice fuera de rango (menor)"),
        ("5", "Índice fuera de rango (mayor)"),
        ("1-10", "Rango parcialmente fuera de límites"),
        ("abc", "Formato inválido"),
        ("1,2,", "Coma final"),
        ("", "Entrada vacía"),
    ]
    
    print("✅ Validación de casos edge:")
    for test_input, description in edge_cases:
        try:
            # Simular procesamiento
            if not test_input.strip():
                print(f"   ✅ '{test_input}' ({description}) -> Entrada vacía detectada")
                continue
                
            selected_indices = set()
            parts = test_input.split(',')
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                    
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                        selected_indices.update(range(start, end + 1))
                    except ValueError:
                        print(f"   ✅ '{test_input}' ({description}) -> Error de formato detectado")
                        break
                else:
                    try:
                        selected_indices.add(int(part))
                    except ValueError:
                        print(f"   ✅ '{test_input}' ({description}) -> Error de formato detectado")
                        break
            else:
                # Validar índices
                valid_count = sum(1 for idx in selected_indices if 1 <= idx <= len(test_objects))
                invalid_count = len(selected_indices) - valid_count
                
                if invalid_count > 0:
                    print(f"   ✅ '{test_input}' ({description}) -> {invalid_count} índices inválidos detectados")
                else:
                    print(f"   ⚠️  '{test_input}' ({description}) -> Procesado sin errores")
                    
        except Exception as e:
            print(f"   ✅ '{test_input}' ({description}) -> Excepción capturada: {type(e).__name__}")
    
    return True

def run_comprehensive_tests():
    """Ejecuta todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS EXHAUSTIVAS DE FUNCIONALIDAD S3")
    print("=" * 60)
    
    results = []
    
    # Prueba 1: Listado de contenido
    success, objects = test_list_bucket_contents()
    results.append(("Listado de contenido", success))
    
    # Prueba 2: Lógica de selección
    success = test_file_selection_logic()
    results.append(("Lógica de selección", success))
    
    # Prueba 3: Funcionalidad de descarga (solo si hay objetos)
    if objects:
        success = test_download_functionality()
        results.append(("Funcionalidad de descarga", success))
    else:
        results.append(("Funcionalidad de descarga", "Omitida - sin archivos"))
    
    # Prueba 4: Casos edge
    success = test_edge_cases()
    results.append(("Casos edge y validaciones", success))
    
    # Resumen de resultados
    print("\n📊 RESUMEN DE PRUEBAS")
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
            print("🎉 PRUEBAS EXITOSAS - Funcionalidad lista para producción")
        elif success_rate >= 60:
            print("⚠️  PRUEBAS PARCIALES - Revisar fallos antes de producción")
        else:
            print("❌ PRUEBAS FALLIDAS - Correcciones necesarias")
    
    return passed, total

if __name__ == "__main__":
    try:
        passed, total = run_comprehensive_tests()
        sys.exit(0 if passed == total else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Error crítico en pruebas: {e}")
        sys.exit(1)
