#!/usr/bin/env python3
"""
Script para diagnosticar permisos y configuración de S3
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
from datetime import datetime

def print_header():
    """Imprime el encabezado del diagnóstico"""
    print("=" * 60)
    print("DIAGNÓSTICO DE PERMISOS S3")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_aws_credentials():
    """Verifica si las credenciales de AWS están configuradas"""
    print("1. Verificando credenciales de AWS...")
    
    # Verificar variables de entorno
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION')
    
    if aws_access_key and aws_secret_key:
        print("   ✓ Credenciales encontradas en variables de entorno")
        print(f"   - AWS_ACCESS_KEY_ID: {aws_access_key[:8]}...")
        print(f"   - AWS_SECRET_ACCESS_KEY: {'*' * 20}")
        print(f"   - AWS_DEFAULT_REGION: {aws_region or 'No configurada'}")
        return True
    else:
        print("   ✗ Credenciales no encontradas en variables de entorno")
        
        # Verificar archivo de credenciales
        credentials_file = os.path.expanduser('~/.aws/credentials')
        if os.path.exists(credentials_file):
            print("   ✓ Archivo de credenciales encontrado: ~/.aws/credentials")
            return True
        else:
            print("   ✗ Archivo de credenciales no encontrado")
            return False

def test_s3_connection():
    """Prueba la conexión con S3"""
    print("\n2. Probando conexión con S3...")
    
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        print("   ✓ Conexión exitosa con S3")
        print(f"   - Buckets encontrados: {len(response['Buckets'])}")
        
        for bucket in response['Buckets']:
            print(f"     • {bucket['Name']} (creado: {bucket['CreationDate']})")
        
        return s3_client, response['Buckets']
        
    except NoCredentialsError:
        print("   ✗ Error: Credenciales no configuradas")
        return None, []
    except ClientError as e:
        print(f"   ✗ Error de cliente AWS: {e}")
        return None, []
    except Exception as e:
        print(f"   ✗ Error inesperado: {e}")
        return None, []

def check_bucket_permissions(s3_client, bucket_name):
    """Verifica permisos específicos de un bucket"""
    print(f"\n3. Verificando permisos del bucket: {bucket_name}")
    
    permissions = {
        'read': False,
        'write': False,
        'delete': False,
        'list': False
    }
    
    try:
        # Probar listado de objetos
        s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        permissions['list'] = True
        print("   ✓ Permiso de listado: OK")
    except ClientError as e:
        print(f"   ✗ Permiso de listado: Error - {e}")
    
    try:
        # Probar lectura (intentar obtener ACL del bucket)
        s3_client.get_bucket_acl(Bucket=bucket_name)
        permissions['read'] = True
        print("   ✓ Permiso de lectura: OK")
    except ClientError as e:
        print(f"   ✗ Permiso de lectura: Error - {e}")
    
    try:
        # Probar escritura (crear un objeto de prueba)
        test_key = 'test-permissions-check.txt'
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=b'Test file for permission check'
        )
        permissions['write'] = True
        print("   ✓ Permiso de escritura: OK")
        
        # Limpiar el archivo de prueba
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            permissions['delete'] = True
            print("   ✓ Permiso de eliminación: OK")
        except ClientError as e:
            print(f"   ✗ Permiso de eliminación: Error - {e}")
            
    except ClientError as e:
        print(f"   ✗ Permiso de escritura: Error - {e}")
    
    return permissions

def check_bucket_configuration(s3_client, bucket_name):
    """Verifica la configuración del bucket"""
    print(f"\n4. Verificando configuración del bucket: {bucket_name}")
    
    try:
        # Verificar región del bucket
        location = s3_client.get_bucket_location(Bucket=bucket_name)
        region = location['LocationConstraint'] or 'us-east-1'
        print(f"   - Región: {region}")
        
        # Verificar versionado
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
            status = versioning.get('Status', 'Disabled')
            print(f"   - Versionado: {status}")
        except ClientError:
            print("   - Versionado: No disponible")
        
        # Verificar encriptación
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            print("   - Encriptación: Habilitada")
        except ClientError:
            print("   - Encriptación: No configurada")
        
        # Verificar CORS
        try:
            cors = s3_client.get_bucket_cors(Bucket=bucket_name)
            print(f"   - CORS: Configurado ({len(cors['CORSRules'])} reglas)")
        except ClientError:
            print("   - CORS: No configurado")
            
    except ClientError as e:
        print(f"   ✗ Error verificando configuración: {e}")

def list_bucket_contents(s3_client, bucket_name):
    """Lista el contenido de un bucket y devuelve la lista de objetos"""
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        objects = []
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                objects.extend(page['Contents'])
        
        return objects
    except Exception as e:
        print(f"Error listando contenido del bucket: {e}")
        return []

def show_file_selection_menu(objects):
    """Muestra los archivos del bucket y permite seleccionar cuáles descargar"""
    if not objects:
        print("   El bucket está vacío")
        return []
    
    print(f"\nArchivos disponibles en el bucket ({len(objects)} archivos):")
    print("-" * 60)
    
    for i, obj in enumerate(objects, 1):
        size_mb = obj['Size'] / (1024 * 1024)
        modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{i:3d}. {obj['Key']:<40} ({size_mb:.2f} MB) - {modified}")
    
    print("-" * 60)
    print("\nOpciones de selección:")
    print("• Números individuales: 1,3,5")
    print("• Rangos: 1-5")
    print("• Combinaciones: 1,3-5,8")
    print("• Todos los archivos: 'todos' o 'all'")
    print("• Cancelar: 'cancelar' o 'cancel'")
    
    while True:
        try:
            selection = input("\nSelecciona los archivos a descargar: ").strip()
            
            if selection.lower() in ['cancelar', 'cancel']:
                return []
            
            if selection.lower() in ['todos', 'all']:
                return objects
            
            # Procesar selección
            selected_indices = set()
            parts = selection.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Rango
                    start, end = map(int, part.split('-'))
                    selected_indices.update(range(start, end + 1))
                else:
                    # Número individual
                    selected_indices.add(int(part))
            
            # Validar índices
            valid_indices = []
            for idx in selected_indices:
                if 1 <= idx <= len(objects):
                    valid_indices.append(idx - 1)  # Convertir a índice base 0
                else:
                    print(f"Advertencia: Índice {idx} fuera de rango (1-{len(objects)})")
            
            if not valid_indices:
                print("No se seleccionaron archivos válidos. Inténtalo de nuevo.")
                continue
            
            selected_objects = [objects[i] for i in valid_indices]
            
            # Mostrar resumen de selección
            print(f"\nArchivos seleccionados ({len(selected_objects)}):")
            total_size = 0
            for obj in selected_objects:
                size_mb = obj['Size'] / (1024 * 1024)
                total_size += obj['Size']
                print(f"  • {obj['Key']} ({size_mb:.2f} MB)")
            
            total_size_mb = total_size / (1024 * 1024)
            print(f"\nTamaño total a descargar: {total_size_mb:.2f} MB")
            
            confirm = input("\n¿Confirmas la descarga? (s/N): ").strip().lower()
            if confirm in ['s', 'si', 'sí', 'y', 'yes']:
                return selected_objects
            else:
                print("Descarga cancelada.")
                return []
                
        except ValueError:
            print("Formato inválido. Usa números separados por comas, rangos (1-5) o 'todos'.")
        except Exception as e:
            print(f"Error procesando selección: {e}")

def download_selected_files(s3_client, bucket_name, selected_objects, local_path):
    """Descarga los archivos seleccionados de un bucket a una carpeta local"""
    if not selected_objects:
        print("No hay archivos para descargar.")
        return True
    
    print(f"\nDescargando {len(selected_objects)} archivo(s) del bucket {bucket_name}...")
    
    try:
        # Crear directorio local si no existe
        os.makedirs(local_path, exist_ok=True)
        
        downloaded_files = 0
        total_files = len(selected_objects)
        
        for obj in selected_objects:
            # Crear estructura de directorios local
            local_file_path = os.path.join(local_path, obj['Key'])
            local_dir = os.path.dirname(local_file_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # Descargar archivo
            print(f"   Descargando: {obj['Key']}")
            s3_client.download_file(bucket_name, obj['Key'], local_file_path)
            downloaded_files += 1
            
            # Mostrar progreso
            progress = (downloaded_files / total_files) * 100
            print(f"   Progreso: {progress:.1f}% ({downloaded_files}/{total_files})")
        
        print("\n   ✓ Descarga completada")
        print(f"   Archivos descargados en: {local_path}")
        return True
        
    except Exception as e:
        print(f"\n   ✗ Error durante la descarga: {e}")
        return False

def download_bucket(s3_client, bucket_name, local_path):
    """Descarga contenido seleccionado de un bucket a una carpeta local"""
    print(f"\nListando contenido del bucket {bucket_name}...")
    
    # Listar objetos en el bucket
    objects = list_bucket_contents(s3_client, bucket_name)
    
    if not objects:
        print("   El bucket está vacío")
        return True
    
    # Si solo hay un archivo, descargarlo directamente
    if len(objects) == 1:
        obj = objects[0]
        size_mb = obj['Size'] / (1024 * 1024)
        print(f"\nSe encontró 1 archivo: {obj['Key']} ({size_mb:.2f} MB)")
        confirm = input("¿Descargar este archivo? (S/n): ").strip().lower()
        
        if confirm in ['', 's', 'si', 'sí', 'y', 'yes']:
            return download_selected_files(s3_client, bucket_name, objects, local_path)
        else:
            print("Descarga cancelada.")
            return True
    
    # Si hay múltiples archivos, mostrar menú de selección
    selected_objects = show_file_selection_menu(objects)
    
    if not selected_objects:
        print("No se seleccionaron archivos para descargar.")
        return True
    
    return download_selected_files(s3_client, bucket_name, selected_objects, local_path)

def show_file_deletion_menu(objects):
    """Muestra los archivos del bucket y permite seleccionar cuáles eliminar"""
    if not objects:
        print("   El bucket está vacío")
        return []
    
    print(f"\n⚠️  ARCHIVOS DISPONIBLES PARA ELIMINACIÓN ({len(objects)} archivos):")
    print("=" * 70)
    
    for i, obj in enumerate(objects, 1):
        size_mb = obj['Size'] / (1024 * 1024)
        modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{i:3d}. {obj['Key']:<40} ({size_mb:.2f} MB) - {modified}")
    
    print("=" * 70)
    print("\n🔥 OPCIONES DE ELIMINACIÓN:")
    print("• Números individuales: 1,3,5")
    print("• Rangos: 1-5")
    print("• Combinaciones: 1,3-5,8")
    print("• Todos los archivos: 'todos' o 'all'")
    print("• Cancelar: 'cancelar' o 'cancel'")
    
    while True:
        try:
            selection = input("\n⚠️  Selecciona los archivos a ELIMINAR: ").strip()
            
            if selection.lower() in ['cancelar', 'cancel']:
                return []
            
            if selection.lower() in ['todos', 'all']:
                print(f"\n🚨 ADVERTENCIA: Vas a eliminar TODOS los {len(objects)} archivos del bucket!")
                confirm_all = input("¿Estás COMPLETAMENTE SEGURO? Escribe 'ELIMINAR TODO' para confirmar: ").strip()
                if confirm_all == 'ELIMINAR TODO':
                    return objects
                else:
                    print("Eliminación cancelada por seguridad.")
                    continue
            
            # Procesar selección
            selected_indices = set()
            parts = selection.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Rango
                    start, end = map(int, part.split('-'))
                    selected_indices.update(range(start, end + 1))
                else:
                    # Número individual
                    selected_indices.add(int(part))
            
            # Validar índices
            valid_indices = []
            for idx in selected_indices:
                if 1 <= idx <= len(objects):
                    valid_indices.append(idx - 1)  # Convertir a índice base 0
                else:
                    print(f"Advertencia: Índice {idx} fuera de rango (1-{len(objects)})")
            
            if not valid_indices:
                print("No se seleccionaron archivos válidos. Inténtalo de nuevo.")
                continue
            
            selected_objects = [objects[i] for i in valid_indices]
            
            # Mostrar resumen de selección para eliminación
            print(f"\n🔥 ARCHIVOS SELECCIONADOS PARA ELIMINACIÓN ({len(selected_objects)}):")
            total_size = 0
            for obj in selected_objects:
                size_mb = obj['Size'] / (1024 * 1024)
                total_size += obj['Size']
                print(f"  🗑️  {obj['Key']} ({size_mb:.2f} MB)")
            
            total_size_mb = total_size / (1024 * 1024)
            print(f"\nTamaño total a eliminar: {total_size_mb:.2f} MB")
            
            print("\n🚨 ESTA ACCIÓN NO SE PUEDE DESHACER 🚨")
            confirm = input("¿Confirmas la ELIMINACIÓN de estos archivos? (s/N): ").strip().lower()
            if confirm in ['s', 'si', 'sí', 'y', 'yes']:
                # Confirmación adicional para múltiples archivos
                if len(selected_objects) > 1:
                    final_confirm = input(f"Confirmación final: ¿Eliminar {len(selected_objects)} archivos? (s/N): ").strip().lower()
                    if final_confirm in ['s', 'si', 'sí', 'y', 'yes']:
                        return selected_objects
                    else:
                        print("Eliminación cancelada.")
                        return []
                else:
                    return selected_objects
            else:
                print("Eliminación cancelada.")
                return []
                
        except ValueError:
            print("Formato inválido. Usa números separados por comas, rangos (1-5) o 'todos'.")
        except Exception as e:
            print(f"Error procesando selección: {e}")

def delete_selected_files(s3_client, bucket_name, selected_objects):
    """Elimina los archivos seleccionados de un bucket"""
    if not selected_objects:
        print("No hay archivos para eliminar.")
        return True
    
    print(f"\n🔥 Eliminando {len(selected_objects)} archivo(s) del bucket {bucket_name}...")
    
    try:
        deleted_files = 0
        total_files = len(selected_objects)
        
        # Eliminar archivos de uno en uno para mejor control
        for obj in selected_objects:
            print(f"   🗑️  Eliminando: {obj['Key']}")
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
            deleted_files += 1
            
            # Mostrar progreso
            progress = (deleted_files / total_files) * 100
            print(f"   Progreso: {progress:.1f}% ({deleted_files}/{total_files})")
        
        print("\n   ✅ Eliminación completada")
        print(f"   Archivos eliminados: {deleted_files}")
        return True
        
    except Exception as e:
        print(f"\n   ❌ Error durante la eliminación: {e}")
        return False

def delete_bucket_contents(s3_client, bucket_name, delete_bucket=False):
    """Elimina contenido seleccionado de un bucket y opcionalmente el bucket mismo"""
    print(f"\nListando contenido del bucket {bucket_name} para eliminación...")
    
    # Listar objetos en el bucket
    objects = list_bucket_contents(s3_client, bucket_name)
    
    if not objects:
        print("   El bucket está vacío")
        if delete_bucket:
            try:
                s3_client.delete_bucket(Bucket=bucket_name)
                print("   ✅ Bucket vacío eliminado")
                return True
            except Exception as e:
                print(f"   ❌ Error eliminando bucket vacío: {e}")
                return False
        return True
    
    # Si solo hay un archivo, eliminarlo directamente con confirmación
    if len(objects) == 1:
        obj = objects[0]
        size_mb = obj['Size'] / (1024 * 1024)
        print(f"\n🔥 Se encontró 1 archivo: {obj['Key']} ({size_mb:.2f} MB)")
        print("🚨 ESTA ACCIÓN NO SE PUEDE DESHACER 🚨")
        confirm = input("¿Eliminar este archivo? (s/N): ").strip().lower()
        
        if confirm in ['s', 'si', 'sí', 'y', 'yes']:
            success = delete_selected_files(s3_client, bucket_name, objects)
            if success and delete_bucket:
                try:
                    s3_client.delete_bucket(Bucket=bucket_name)
                    print("   ✅ Bucket eliminado tras vaciar contenido")
                except Exception as e:
                    print(f"   ❌ Error eliminando bucket: {e}")
            return success
        else:
            print("Eliminación cancelada.")
            return True
    
    # Si hay múltiples archivos, mostrar menú de selección
    selected_objects = show_file_deletion_menu(objects)
    
    if not selected_objects:
        print("No se seleccionaron archivos para eliminar.")
        return True
    
    success = delete_selected_files(s3_client, bucket_name, selected_objects)
    
    # Si se eliminaron todos los archivos y se solicita eliminar el bucket
    if success and delete_bucket and len(selected_objects) == len(objects):
        try:
            s3_client.delete_bucket(Bucket=bucket_name)
            print("   ✅ Bucket eliminado tras vaciar todo el contenido")
        except Exception as e:
            print(f"   ❌ Error eliminando bucket: {e}")
    
    return success

def delete_bucket_and_contents(s3_client, bucket_name):
    """
    Vacía y elimina un bucket de S3, manejando el versionado.

    Args:
        s3_client: Cliente de boto3 S3.
        bucket_name (str): El nombre del bucket a eliminar.

    Returns:
        tuple: (bool, str) donde el booleano indica el éxito y el string
               es un mensaje de estado.
    """
    try:
        # Paso 1: Vaciar el bucket. Esto es diferente si el bucket está versionado.
        print(f"Iniciando el borrado del bucket '{bucket_name}' y todo su contenido.")
        
        # Comprobar si el versionado está activado
        s3_resource = boto3.resource('s3')
        bucket_versioning = s3_resource.BucketVersioning(bucket_name)
        
        if bucket_versioning.status == 'Enabled':
            print("   - El bucket tiene el versionado activado. Eliminando todas las versiones de objetos y marcadores de borrado.")
            bucket = s3_resource.Bucket(bucket_name)
            bucket.object_versions.delete()
        else:
            print("   - El bucket no tiene el versionado activado. Eliminando todos los objetos.")
            bucket = s3_resource.Bucket(bucket_name)
            bucket.objects.all().delete()
            
        print("   ✓ Contenido del bucket eliminado con éxito.")

        # Paso 2: Eliminar el bucket ahora que está vacío.
        print("   - Intentando eliminar el bucket...")
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"   ✓ Bucket '{bucket_name}' eliminado con éxito.")
        
        return True, f"El bucket '{bucket_name}' y todo su contenido han sido eliminados."

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        error_message = e.response.get("Error", {}).get("Message")
        print(f"   ✗ Error de cliente AWS al eliminar el bucket: {error_code} - {error_message}")
        return False, f"Error de AWS ({error_code}): {error_message}"
    except Exception as e:
        print(f"   ✗ Error inesperado al eliminar el bucket: {str(e)}")
        return False, f"Error inesperado: {str(e)}"

def create_s3_bucket(bucket_name, region='us-east-1'):
    """
    Crea un nuevo bucket de S3 en la región especificada.

    :param bucket_name: Nombre del bucket a crear.
    :param region: Región de AWS donde se creará el bucket.
    :return: Tupla (bool, str) indicando éxito y mensaje.
    """
    try:
        s3_client = boto3.client('s3', region_name=region)
        
        # us-east-1 es un caso especial y no requiere el LocationConstraint
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=location
            )
        
        # Esperar a que el bucket exista para evitar race conditions
        waiter = s3_client.get_waiter('bucket_exists')
        waiter.wait(Bucket=bucket_name)
        
        return True, f"¡Éxito! El bucket '{bucket_name}' se ha creado correctamente en la región '{region}'."
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == 'BucketAlreadyOwnedByYou':
            return True, f"INFO: El bucket '{bucket_name}' ya existe y te pertenece."
        elif error_code == 'BucketAlreadyExists':
            return False, f"Error: El nombre de bucket '{bucket_name}' ya está en uso a nivel global en AWS. Prueba con otro nombre."
        elif error_code == 'InvalidBucketName':
            return False, f"Error: El nombre '{bucket_name}' no es válido. Revisa las reglas de nomenclatura de S3."
        elif error_code == 'IllegalLocationConstraintException':
            return False, f"Error: La región '{region}' parece no ser válida o tener algún problema. Verifica la región seleccionada."
        else:
            return False, f"Error inesperado de AWS al crear el bucket: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado al crear el bucket: {str(e)}"


def show_menu(s3_client, buckets):
    """Muestra un menú interactivo para operaciones de mantenimiento"""
    while True:
        print("\n" + "=" * 60)
        print("MENÚ DE MANTENIMIENTO DE BUCKETS")
        print("=" * 60)
        print("1. Diagnosticar permisos de buckets")
        print("2. Descargar contenido de un bucket")
        print("3. Eliminar contenido de un bucket")
        print("4. Eliminar bucket completo")
        print("5. Salir")
        
        try:
            opcion = input("\nSeleccione una opción (1-5): ")
            
            if opcion == "1":
                # Verificar permisos para cada bucket
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    permissions = check_bucket_permissions(s3_client, bucket_name)
                    check_bucket_configuration(s3_client, bucket_name)
                    
                    print(f"\n📊 Resumen de permisos para {bucket_name}:")
                    for perm, status in permissions.items():
                        status_icon = "✓" if status else "✗"
                        print(f"   {status_icon} {perm.capitalize()}: {'OK' if status else 'Error'}")
            
            elif opcion in ["2", "3", "4"]:
                # Mostrar buckets disponibles
                print("\nBuckets disponibles:")
                for i, bucket in enumerate(buckets, 1):
                    print(f"{i}. {bucket['Name']}")
                
                bucket_num = int(input("\nSeleccione el número de bucket: ")) - 1
                if 0 <= bucket_num < len(buckets):
                    bucket_name = buckets[bucket_num]['Name']
                    
                    if opcion == "2":
                        local_path = input("Ingrese la ruta local para la descarga: ")
                        download_bucket(s3_client, bucket_name, local_path)
                    
                    elif opcion == "3":
                        if input(f"¿Está seguro de eliminar TODO el contenido de {bucket_name}? (s/N): ").lower() == 's':
                            delete_bucket_contents(s3_client, bucket_name, delete_bucket=False)
                    
                    elif opcion == "4":
                        if input(f"¿Está seguro de eliminar el bucket {bucket_name} y TODO su contenido? (s/N): ").lower() == 's':
                            delete_bucket_contents(s3_client, bucket_name, delete_bucket=True)
                else:
                    print("Número de bucket inválido")
            
            elif opcion == "5":
                print("\nSaliendo...")
                break
            
            else:
                print("Opción inválida")
                
        except ValueError:
            print("Por favor, ingrese un número válido")
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Función principal"""
    print_header()
    
    # Verificar credenciales
    if not check_aws_credentials():
        print("\n❌ No se pueden verificar los permisos sin credenciales válidas")
        print("\nPara configurar credenciales:")
        print("1. Usar variables de entorno:")
        print("   export AWS_ACCESS_KEY_ID=tu_access_key")
        print("   export AWS_SECRET_ACCESS_KEY=tu_secret_key")
        print("   export AWS_DEFAULT_REGION=tu_region")
        print("\n2. Usar AWS CLI:")
        print("   aws configure")
        sys.exit(1)
    
    # Probar conexión
    s3_client, buckets = test_s3_connection()
    
    if not s3_client:
        print("\n❌ No se pudo establecer conexión con S3")
        sys.exit(1)
    
    if not buckets:
        print("\n⚠️  No se encontraron buckets")
        return
    
    # Mostrar menú de operaciones
    show_menu(s3_client, buckets)

if __name__ == "__main__":
    main()
