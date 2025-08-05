#!/usr/bin/env python3
"""
Script para diagnosticar permisos y configuración de S3 (Versión con configuración mejorada)
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
from datetime import datetime
import subprocess
import json

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def print_header():
    """Imprime el encabezado del diagnóstico"""
    print("=" * 60)
    print("DIAGNÓSTICO DE PERMISOS S3 (VERSIÓN MEJORADA)")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def get_aws_cli_config():
    """Obtiene la configuración de AWS CLI"""
    print("1. Obteniendo configuración de AWS CLI...")

    try:
        # Obtener región
        region = subprocess.check_output(
            ["aws", "configure", "get", "region"],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

        # Obtener perfil
        profile = subprocess.check_output(
            ["aws", "configure", "get", "profile"],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

        if not profile or profile == "<not set>":
            profile = "default"

        print(f"   ✓ Región configurada: {region}")
        print(f"   ✓ Perfil configurado: {profile}")

        return region, profile

    except subprocess.CalledProcessError as e:
        print(f"   ✗ Error obteniendo configuración: {e}")
        return "us-east-1", "default"
    except FileNotFoundError:
        print("   ✗ AWS CLI no encontrado")
        return "us-east-1", "default"


def test_s3_connection_with_cli_config():
    """Prueba la conexión con S3 usando configuración de AWS CLI"""
    print("\n2. Probando conexión con S3 usando configuración de AWS CLI...")

    region, profile = get_aws_cli_config()

    try:
        # Crear sesión usando el perfil de AWS CLI
        session = boto3.Session(profile_name=profile, region_name=region)
        s3_client = session.client(
            "s3",
            config=boto3.session.Config(
                retries=dict(max_attempts=2),
                connect_timeout=10,
                read_timeout=10,
            ),
        )

        print("   - Cliente S3 configurado con perfil AWS CLI")
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
        print(f"      - Región: {region}")
        print(f"      - Perfil: {profile}")
        return None, []


def check_aws_credentials():
    """Verifica si las credenciales de AWS están configuradas"""
    print("3. Verificando credenciales de AWS...")

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

    # Probar conexión usando configuración de AWS CLI
    s3_client, buckets = test_s3_connection_with_cli_config()

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
