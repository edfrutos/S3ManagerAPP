#!/usr/bin/env python3
"""
Script para diagnosticar permisos y configuración de S3 (Versión con endpoint específico)
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def print_header():
    """Imprime el encabezado del diagnóstico"""
    print("=" * 60)
    print("DIAGNÓSTICO DE PERMISOS S3 (ENDPOINT ESPECÍFICO)")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def test_s3_connection_with_specific_endpoint():
    """Prueba la conexión con S3 usando endpoint específico"""
    print("\n2. Probando conexión con S3 usando endpoint específico...")

    try:
        # Usar endpoint específico para evitar problemas de DNS
        s3_client = boto3.client(
            "s3",
            region_name="us-east-1",
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            config=boto3.session.Config(
                retries=dict(max_attempts=2),
                connect_timeout=10,
                read_timeout=10,
            ),
        )

        print("   - Cliente S3 configurado con endpoint específico")
        print("   - Intentando conectar...")

        response = s3_client.list_buckets()

        print("   ✓ Conexión exitosa con S3")
        print(f"   - Buckets encontrados: {len(response['Buckets'])}")

        for bucket in response["Buckets"]:
            print(
                f"     • {bucket['Name']} (creado: {bucket['CreationDate']})"
            )

        return s3_client, response["Buckets"]

    except NoCredentialsError:
        print("   ✗ Error: Credenciales no configuradas")
        print("   💡 Solución: Configura credenciales con 'aws configure'")
        return None, []
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        print(f"   ✗ Error de cliente AWS: {error_code} - {error_message}")
        return None, []
    except Exception as e:
        print(f"   ✗ Error inesperado: {e}")
        print("   🔍 Información adicional:")
        print(f"      - Tipo de error: {type(e).__name__}")
        print("      - Endpoint usado: https://s3.us-east-1.amazonaws.com")
        return None, []


def check_aws_credentials():
    """Verifica si las credenciales de AWS están configuradas"""
    print("1. Verificando credenciales de AWS...")

    # Verificar variables de entorno
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_DEFAULT_REGION")

    if aws_access_key and aws_secret_key:
        print("   ✓ Credenciales encontradas en variables de entorno")
        print(f"   - AWS_ACCESS_KEY_ID: {aws_access_key[:8]}...")
        print(f"   - AWS_SECRET_ACCESS_KEY: {'*' * 20}")
        print(f"   - AWS_DEFAULT_REGION: {aws_region or 'No configurada'}")
        return True
    else:
        print("   ✗ Credenciales no encontradas en variables de entorno")

        # Verificar archivo de credenciales
        credentials_file = os.path.expanduser("~/.aws/credentials")
        if os.path.exists(credentials_file):
            print(
                "   ✓ Archivo de credenciales encontrado: ~/.aws/credentials"
            )
            return True
        else:
            print("   ✗ Archivo de credenciales no encontrado")
            return False


def main():
    """Función principal"""
    print_header()

    # Verificar credenciales
    if not check_aws_credentials():
        print(
            "\n❌ No se pueden verificar los permisos sin credenciales válidas"
        )
        print("\nPara configurar credenciales:")
        print("1. Usar variables de entorno:")
        print("   export AWS_ACCESS_KEY_ID=tu_access_key")
        print("   export AWS_SECRET_ACCESS_KEY=tu_secret_key")
        print("   export AWS_DEFAULT_REGION=tu_region")
        print("\n2. Usar AWS CLI:")
        print("   aws configure")
        sys.exit(1)

    # Probar conexión usando endpoint específico
    s3_client, buckets = test_s3_connection_with_specific_endpoint()

    if not s3_client:
        print("\n❌ No se pudo establecer conexión con S3")
        print("\n🔧 Soluciones posibles:")
        print("1. Verificar conectividad a internet")
        print("2. Verificar configuración de DNS")
        print("3. Verificar configuración de proxy/firewall")
        print("4. Usar VPN si es necesario")
        sys.exit(1)

    if not buckets:
        print("\n⚠️  No se encontraron buckets")
        return

    print("\n✅ Diagnóstico completado exitosamente!")
    print(f"📊 Total de buckets encontrados: {len(buckets)}")


if __name__ == "__main__":
    main()
