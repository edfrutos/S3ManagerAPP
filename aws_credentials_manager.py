#!/usr/bin/env python3
"""
Gestor de credenciales AWS para S3Manager
Autor: EDF Developer - 2025
"""

import os
import json
from pathlib import Path
import keyring
from keyring.errors import PasswordDeleteError

class AWSCredentialsManager:
    """Gestiona el almacenamiento seguro de credenciales AWS"""
    
    SERVICE_NAME = "S3Manager"
    ACCESS_KEY_USERNAME = "AWS_ACCESS_KEY_ID"
    SECRET_KEY_USERNAME = "AWS_SECRET_ACCESS_KEY"
    
    @classmethod
    def save_credentials(cls, access_key: str, secret_key: str) -> tuple[bool, str | None]:
        """Guarda las credenciales AWS y devuelve un estado y un mensaje de error si lo hubiera."""
        # 1. Intentar guardar en el keyring del sistema (solo si no estamos en modo de prueba)
        if os.environ.get('TEST_MODE') != '1':
            try:
                keyring.set_password(cls.SERVICE_NAME, cls.ACCESS_KEY_USERNAME, access_key)
                keyring.set_password(cls.SERVICE_NAME, cls.SECRET_KEY_USERNAME, secret_key)
            except Exception:
                # Si falla, no es un error fatal. La app puede usar el archivo de credenciales.
                pass

        # 2. Actualizar variables de entorno para la sesión actual
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        
        # 3. Guardar en archivo de configuración AWS (operación crítica)
        try:
            aws_config_dir = Path.home() / '.aws'
            aws_config_dir.mkdir(mode=0o700, exist_ok=True)
            
            credentials_file = aws_config_dir / 'credentials'
            config = f"""[default]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}
"""
            
            with open(credentials_file, 'w') as f:
                f.write(config)
            
            credentials_file.chmod(0o600)
            return True, None
            
        except Exception as e:
            error_message = f"Error crítico al guardar credenciales en el archivo: {e}"
            print(error_message)
            return False, error_message
    
    @classmethod
    def load_credentials(cls) -> tuple:
        """
        Carga las credenciales AWS desde el llavero (keyring) o el archivo de configuración de AWS.
        Intenta primero con el llavero y, si falla o no hay nada, busca en ~/.aws/credentials.
        """
        access_key, secret_key = None, None

        # 1. Intentar cargar desde keyring de forma segura (solo si no estamos en modo de prueba)
        if os.environ.get('TEST_MODE') != '1':
            try:
                access_key = keyring.get_password(cls.SERVICE_NAME, cls.ACCESS_KEY_USERNAME)
                secret_key = keyring.get_password(cls.SERVICE_NAME, cls.SECRET_KEY_USERNAME)
            except Exception:
                # Ignorar errores del llavero (p.ej. acceso denegado)
                access_key, secret_key = None, None

        if access_key and secret_key:
            os.environ['AWS_ACCESS_KEY_ID'] = access_key
            os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
            return access_key, secret_key

        # 2. Si no se encontraron en keyring, intentar cargar desde archivo AWS
        try:
            credentials_file = Path.home() / '.aws/credentials'
            if credentials_file.exists():
                import configparser
                config = configparser.ConfigParser()
                config.read(credentials_file)
                
                if 'default' in config:
                    access_key = config['default'].get('aws_access_key_id')
                    secret_key = config['default'].get('aws_secret_access_key')
                    
                    if access_key and secret_key:
                        return access_key, secret_key
        except Exception as e:
            print(f"Error al procesar el archivo de credenciales de AWS: {e}")

        return None, None
    
    @classmethod
    def delete_credentials(cls) -> bool:
        """Elimina las credenciales guardadas"""
        try:
            # Eliminar de keyring
            keyring.delete_password(cls.SERVICE_NAME, cls.ACCESS_KEY_USERNAME)
            keyring.delete_password(cls.SERVICE_NAME, cls.SECRET_KEY_USERNAME)
            
            # Eliminar variables de entorno
            os.environ.pop('AWS_ACCESS_KEY_ID', None)
            os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
            
            # Eliminar de archivo AWS si existe
            credentials_file = Path.home() / '.aws/credentials'
            if credentials_file.exists():
                credentials_file.unlink()
            
            return True
            
        except PasswordDeleteError:
            # No hay problema si las credenciales no existían
            return True
        except Exception as e:
            print(f"Error eliminando credenciales: {e}")
            return False
    
    @classmethod
    def has_credentials(cls) -> bool:
        """Verifica si hay credenciales guardadas"""
        access_key, secret_key = cls.load_credentials()
        return bool(access_key and secret_key)
