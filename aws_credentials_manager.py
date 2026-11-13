#!/usr/bin/env python3
"""
Gestor de credenciales AWS multi-perfil para S3Manager
Autor: EDF Developer - 2025
"""

import os
import json
import configparser
from pathlib import Path

import base64

import boto3
import keyring
from keyring.errors import PasswordDeleteError

from crypto_utils import (
    DecryptionError,
    decrypt_with_key,
    decrypt_with_password,
    derive_key,
    encrypt_with_key,
    encrypt_with_password,
    generate_salt,
)

EXPORT_FORMAT_VERSION = 1

# Texto de verificación fijo: al activar la contraseña maestra se cifra
# con la clave derivada y se guarda junto al salt. Al desbloquear, se
# intenta descifrar: si el resultado coincide, la contraseña es correcta.
_MASTER_PASSWORD_VERIFIER_PLAINTEXT = b"S3Manager-master-password-check"


class AWSCredentialsManager:
    """Gestiona el almacenamiento seguro de credenciales AWS, con soporte
    para múltiples perfiles nombrados (al estilo de los perfiles de AWS CLI).

    - Las claves secretas (access key / secret key) viven únicamente en el
      keyring del sistema, una entrada por perfil.
    - El nombre de los perfiles, su región por defecto y cuál está activo
      se guardan en ``~/.s3manager/config.json`` (sin secretos).
    - ``~/.aws/credentials`` y ``~/.aws/config`` se mantienen sincronizados
      con todos los perfiles conocidos, para que herramientas externas
      (aws-cli, otros scripts) puedan usarlos con ``--profile``.
    """

    SERVICE_NAME = "S3Manager"
    DEFAULT_PROFILE = "default"
    ACCESS_KEY_USERNAME = "AWS_ACCESS_KEY_ID"
    SECRET_KEY_USERNAME = "AWS_SECRET_ACCESS_KEY"

    APP_CONFIG_DIR = Path.home() / '.s3manager'
    APP_CONFIG_FILE = APP_CONFIG_DIR / 'config.json'

    AWS_DIR = Path.home() / '.aws'
    AWS_CREDENTIALS_FILE = AWS_DIR / 'credentials'
    AWS_CONFIG_FILE = AWS_DIR / 'config'

    # Marcador escrito en ~/.aws/credentials en lugar del secret key real
    # cuando la contraseña maestra está activa, para no dejar el secreto
    # en texto plano en disco fuera del keyring cifrado.
    PROTECTED_PLACEHOLDER = '<protegida-por-S3Manager-contraseña-maestra>'

    # Clave derivada de la contraseña maestra, cacheada SOLO en memoria
    # de este proceso mientras dura la sesión (nunca se persiste).
    _session_key: bytes | None = None

    # ------------------------------------------------------------------
    # Metadata de perfiles (nombres + región). Las claves secretas NUNCA
    # se guardan aquí, solo en el keyring del sistema.
    # ------------------------------------------------------------------
    @classmethod
    def _load_app_config(cls) -> dict:
        if not cls.APP_CONFIG_FILE.exists():
            return {"active_profile": cls.DEFAULT_PROFILE, "profiles": {}}
        try:
            data = json.loads(cls.APP_CONFIG_FILE.read_text())
            data.setdefault("active_profile", cls.DEFAULT_PROFILE)
            data.setdefault("profiles", {})
            return data
        except Exception:
            return {"active_profile": cls.DEFAULT_PROFILE, "profiles": {}}

    @classmethod
    def _save_app_config(cls, config: dict) -> None:
        cls.APP_CONFIG_DIR.mkdir(mode=0o700, exist_ok=True)
        cls.APP_CONFIG_FILE.write_text(json.dumps(config, indent=2))
        cls.APP_CONFIG_FILE.chmod(0o600)

    @classmethod
    def _ensure_legacy_profile_registered(cls, config: dict) -> dict:
        """Si ya había credenciales guardadas con la versión anterior
        (un único perfil bajo el nombre de usuario clásico del keyring),
        las registra como perfil 'default' para no perderlas."""
        if config["profiles"] or os.environ.get('TEST_MODE') == '1':
            return config
        try:
            legacy_access = keyring.get_password(
                cls.SERVICE_NAME, cls.ACCESS_KEY_USERNAME
            )
        except Exception:
            legacy_access = None
        if legacy_access:
            config["profiles"][cls.DEFAULT_PROFILE] = {"region": ""}
        return config

    @classmethod
    def list_profiles(cls) -> list:
        """Devuelve los nombres de todos los perfiles guardados."""
        config = cls._ensure_legacy_profile_registered(cls._load_app_config())
        return sorted(config["profiles"].keys())

    @classmethod
    def get_active_profile(cls) -> str:
        """Devuelve el nombre del perfil actualmente activo."""
        config = cls._ensure_legacy_profile_registered(cls._load_app_config())
        active = config.get("active_profile", cls.DEFAULT_PROFILE)
        if active not in config["profiles"] and config["profiles"]:
            active = sorted(config["profiles"].keys())[0]
        return active

    @classmethod
    def get_profile_region(cls, profile: str) -> str:
        """Devuelve la región por defecto guardada para un perfil."""
        config = cls._load_app_config()
        return config.get("profiles", {}).get(profile, {}).get("region", "")

    # ------------------------------------------------------------------
    # Claves de keyring por perfil. Para 'default' se reutiliza el mismo
    # nombre de usuario que en la versión anterior (sin sufijo), para no
    # perder las credenciales ya guardadas por instalaciones existentes.
    # ------------------------------------------------------------------
    @classmethod
    def _kr_username(cls, profile: str, secret: bool) -> str:
        base = cls.SECRET_KEY_USERNAME if secret else cls.ACCESS_KEY_USERNAME
        if profile == cls.DEFAULT_PROFILE:
            return base
        return f"{profile}::{base}"

    @classmethod
    def save_credentials(cls, access_key: str, secret_key: str,
                          region: str = "", profile: str | None = None
                          ) -> tuple[bool, str | None]:
        """Guarda las credenciales de un perfil AWS (por defecto, el
        perfil actualmente activo) y devuelve (éxito, mensaje de error)."""
        profile = profile or cls.get_active_profile()

        if cls.is_master_password_enabled() and cls._session_key is None:
            return False, (
                "S3Manager está bloqueado. Desbloquéalo con la contraseña "
                "maestra (menú Archivo) antes de guardar credenciales."
            )

        stored_secret = secret_key
        if cls.is_master_password_enabled():
            stored_secret = base64.b64encode(
                encrypt_with_key(secret_key.encode('utf-8'), cls._session_key)
            ).decode('ascii')

        if os.environ.get('TEST_MODE') != '1':
            try:
                keyring.set_password(
                    cls.SERVICE_NAME, cls._kr_username(profile, False),
                    access_key,
                )
                keyring.set_password(
                    cls.SERVICE_NAME, cls._kr_username(profile, True),
                    stored_secret,
                )
            except Exception:
                # Si falla, no es un error fatal. Los datos igualmente se
                # sincronizan en ~/.aws/credentials más abajo.
                pass

        config = cls._load_app_config()
        was_empty = not config["profiles"]
        config["profiles"][profile] = {"region": region}
        if was_empty or not config.get("active_profile") \
                or config.get("active_profile") == profile:
            config["active_profile"] = profile
        cls._save_app_config(config)

        if profile == config["active_profile"]:
            cls._activate_in_process(access_key, secret_key, region)

        try:
            cls._sync_aws_files(
                overrides={profile: (access_key, secret_key, region)}
            )
            return True, None
        except Exception as e:
            error_message = f"Error crítico al guardar credenciales en el archivo: {e}"
            print(error_message)
            return False, error_message

    @classmethod
    def _activate_in_process(cls, access_key: str, secret_key: str,
                              region: str) -> None:
        """Actualiza el entorno y fuerza a boto3 a usar estas credenciales
        de inmediato, en lugar de las que tuviera cacheadas."""
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        if region:
            os.environ['AWS_DEFAULT_REGION'] = region
        else:
            os.environ.pop('AWS_DEFAULT_REGION', None)

        # boto3 cachea las credenciales resueltas en su sesión global por
        # defecto (botocore.session.Session._credentials solo se resuelve
        # si es None) y nunca las vuelve a resolver. Sin esto, boto3.client
        # ('s3') seguiría usando credenciales/región antiguas tras activar
        # un perfil o guardar unas credenciales nuevas.
        session_kwargs = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
        }
        if region:
            session_kwargs['region_name'] = region
        boto3.setup_default_session(**session_kwargs)

    @classmethod
    def load_credentials(cls, profile: str | None = None
                          ) -> tuple:
        """Lee (access_key, secret_key, region) de un perfil, sin activarlo
        en el proceso. Por defecto, lee el perfil activo."""
        profile = profile or cls.get_active_profile()
        access_key = secret_key = None

        if os.environ.get('TEST_MODE') != '1':
            try:
                access_key = keyring.get_password(
                    cls.SERVICE_NAME, cls._kr_username(profile, False)
                )
                secret_key = keyring.get_password(
                    cls.SERVICE_NAME, cls._kr_username(profile, True)
                )
            except Exception:
                access_key, secret_key = None, None

        region = cls.get_profile_region(profile)

        if access_key and secret_key:
            if cls.is_master_password_enabled():
                if cls._session_key is None:
                    # Bloqueado: no se puede descifrar hasta desbloquear.
                    return access_key, None, region
                try:
                    secret_key = decrypt_with_key(
                        base64.b64decode(secret_key), cls._session_key
                    ).decode('utf-8')
                except Exception:
                    return access_key, None, region
            return access_key, secret_key, region

        if cls.is_master_password_enabled():
            # En modo protegido el secreto solo vive (cifrado) en el
            # keyring: no hay fallback de archivo, porque ese archivo
            # nunca contiene el valor real.
            return access_key, None, region

        # Última red de seguridad: leer directamente de ~/.aws si el
        # keyring no tiene nada (p. ej. el sistema no tiene keyring
        # disponible, o venimos de una migración).
        try:
            if cls.AWS_CREDENTIALS_FILE.exists():
                creds = configparser.ConfigParser()
                creds.read(cls.AWS_CREDENTIALS_FILE)
                if profile in creds:
                    access_key = creds[profile].get('aws_access_key_id') or access_key
                    secret_key = creds[profile].get('aws_secret_access_key') or secret_key
            if not region and cls.AWS_CONFIG_FILE.exists():
                cfg = configparser.ConfigParser()
                cfg.read(cls.AWS_CONFIG_FILE)
                section = 'default' if profile == cls.DEFAULT_PROFILE else f'profile {profile}'
                if section in cfg:
                    region = cfg[section].get('region', '')
        except Exception as e:
            print(f"Error al procesar el archivo de credenciales de AWS: {e}")

        return access_key, secret_key, region

    @classmethod
    def activate_profile(cls, profile: str) -> tuple[bool, str | None]:
        """Convierte `profile` en el perfil activo y lo aplica de
        inmediato (entorno + sesión boto3)."""
        access_key, secret_key, region = cls.load_credentials(profile)
        if not access_key or not secret_key:
            if cls.is_master_password_enabled() and cls._session_key is None:
                return False, (
                    "S3Manager está bloqueado. Desbloquéalo con la "
                    "contraseña maestra (menú Archivo) para activar perfiles."
                )
            return False, f"El perfil '{profile}' no tiene credenciales guardadas."

        config = cls._load_app_config()
        config["active_profile"] = profile
        cls._save_app_config(config)

        cls._activate_in_process(access_key, secret_key, region)
        return True, None

    @classmethod
    def delete_profile(cls, profile: str) -> bool:
        """Elimina un perfil: credenciales del keyring, metadata y su
        entrada en ~/.aws. Si era el perfil activo, activa otro disponible
        (o limpia el entorno si no queda ninguno)."""
        try:
            if os.environ.get('TEST_MODE') != '1':
                for is_secret in (False, True):
                    try:
                        keyring.delete_password(
                            cls.SERVICE_NAME, cls._kr_username(profile, is_secret)
                        )
                    except PasswordDeleteError:
                        pass
                    except Exception:
                        # Backend de keyring no disponible u otro fallo no
                        # fatal: seguimos limpiando metadata y archivos.
                        pass

            config = cls._load_app_config()
            config["profiles"].pop(profile, None)
            was_active = config.get("active_profile") == profile
            if was_active:
                remaining = sorted(config["profiles"].keys())
                config["active_profile"] = remaining[0] if remaining else cls.DEFAULT_PROFILE
            cls._save_app_config(config)

            if was_active:
                if config["profiles"]:
                    cls.activate_profile(config["active_profile"])
                else:
                    os.environ.pop('AWS_ACCESS_KEY_ID', None)
                    os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
                    os.environ.pop('AWS_DEFAULT_REGION', None)
                    boto3.DEFAULT_SESSION = None

            cls._sync_aws_files()
            return True

        except Exception as e:
            print(f"Error eliminando perfil: {e}")
            return False

    @classmethod
    def delete_credentials(cls) -> bool:
        """Elimina TODOS los perfiles guardados (mantiene compatibilidad
        con el comportamiento de la versión anterior, de un único perfil)."""
        ok = True
        for profile in cls.list_profiles():
            ok = cls.delete_profile(profile) and ok
        try:
            if cls.AWS_CREDENTIALS_FILE.exists():
                cls.AWS_CREDENTIALS_FILE.unlink()
            if cls.AWS_CONFIG_FILE.exists():
                cls.AWS_CONFIG_FILE.unlink()
        except Exception as e:
            print(f"Error eliminando archivos de credenciales AWS: {e}")
            ok = False
        return ok

    @classmethod
    def has_credentials(cls, profile: str | None = None) -> bool:
        """Verifica si un perfil (por defecto, el activo) tiene credenciales."""
        access_key, secret_key, _ = cls.load_credentials(profile)
        return bool(access_key and secret_key)

    # ------------------------------------------------------------------
    # Contraseña maestra: capa extra de cifrado para el secret key de
    # cada perfil (además de lo que ya ofrece el keyring del sistema).
    # La clave derivada solo vive en memoria durante la sesión; nunca se
    # guarda en disco. Sin ella, los secretos quedan indescifrables.
    # ------------------------------------------------------------------
    @classmethod
    def is_master_password_enabled(cls) -> bool:
        config = cls._load_app_config()
        return bool(config.get("master_password", {}).get("enabled"))

    @classmethod
    def is_unlocked(cls) -> bool:
        """True si no hace falta contraseña maestra, o si ya se ha
        introducido correctamente en esta sesión del proceso."""
        return (not cls.is_master_password_enabled()) or cls._session_key is not None

    @classmethod
    def unlock(cls, password: str) -> tuple[bool, str | None]:
        """Verifica la contraseña maestra y, si es correcta, cachea la
        clave derivada en memoria para el resto de la sesión."""
        config = cls._load_app_config()
        mp = config.get("master_password", {})
        if not mp.get("enabled"):
            return True, None
        try:
            salt = base64.b64decode(mp["salt"])
            verifier = base64.b64decode(mp["verifier"])
            key = derive_key(password, salt)
            decrypt_with_key(verifier, key)
        except DecryptionError:
            return False, "Contraseña maestra incorrecta."
        except Exception as e:
            return False, f"Error al verificar la contraseña maestra: {e}"
        cls._session_key = key
        return True, None

    @classmethod
    def lock(cls) -> None:
        """Olvida la clave derivada de la sesión actual."""
        cls._session_key = None

    @classmethod
    def setup_master_password(cls, password: str) -> tuple[bool, str | None]:
        """Activa la protección con contraseña maestra: re-cifra todas
        las claves secretas ya guardadas con una clave derivada de
        `password`."""
        try:
            plain_profiles = {}
            for profile in cls.list_profiles():
                access_key, secret_key, region = cls.load_credentials(profile)
                if access_key and secret_key:
                    plain_profiles[profile] = (access_key, secret_key, region)

            salt = generate_salt()
            key = derive_key(password, salt)
            verifier = encrypt_with_key(_MASTER_PASSWORD_VERIFIER_PLAINTEXT, key)

            config = cls._load_app_config()
            config["master_password"] = {
                "enabled": True,
                "salt": base64.b64encode(salt).decode('ascii'),
                "verifier": base64.b64encode(verifier).decode('ascii'),
            }
            cls._save_app_config(config)
            cls._session_key = key

            # Vuelve a guardar cada perfil: save_credentials() ya cifrará
            # el secret_key automáticamente, porque master_password ya
            # está activo y _session_key ya está disponible.
            for profile, (access_key, secret_key, region) in plain_profiles.items():
                cls.save_credentials(access_key, secret_key, region, profile=profile)

            return True, None
        except Exception as e:
            return False, f"Error activando la contraseña maestra: {e}"

    @classmethod
    def disable_master_password(cls, password: str) -> tuple[bool, str | None]:
        """Desactiva la protección: vuelve a guardar todos los secretos
        sin cifrado adicional (siguen protegidos por el keyring)."""
        ok, error = cls.unlock(password)
        if not ok:
            return False, error

        try:
            plain_profiles = {}
            for profile in cls.list_profiles():
                access_key, secret_key, region = cls.load_credentials(profile)
                if access_key and secret_key:
                    plain_profiles[profile] = (access_key, secret_key, region)

            config = cls._load_app_config()
            config["master_password"] = {"enabled": False}
            cls._save_app_config(config)
            cls._session_key = None

            for profile, (access_key, secret_key, region) in plain_profiles.items():
                cls.save_credentials(access_key, secret_key, region, profile=profile)

            return True, None
        except Exception as e:
            return False, f"Error desactivando la contraseña maestra: {e}"

    # ------------------------------------------------------------------
    # Sincroniza ~/.aws/credentials y ~/.aws/config con TODOS los
    # perfiles conocidos.
    # ------------------------------------------------------------------
    @classmethod
    def _sync_aws_files(cls, overrides: dict | None = None) -> None:
        """Reescribe ~/.aws/credentials y ~/.aws/config con todos los
        perfiles guardados. `overrides` permite pasar directamente
        (access_key, secret_key, region) de un perfil recién guardado,
        para no depender de poder releerlo del keyring justo después
        (relevante en TEST_MODE, donde el keyring se omite)."""
        overrides = overrides or {}
        cls.AWS_DIR.mkdir(mode=0o700, exist_ok=True)

        creds = configparser.ConfigParser()
        cfg = configparser.ConfigParser()

        protected = cls.is_master_password_enabled()
        for profile in cls.list_profiles():
            if profile in overrides:
                access_key, secret_key, region = overrides[profile]
            else:
                access_key, secret_key, region = cls.load_credentials(profile)

            if not access_key:
                continue

            if protected:
                # No se escribe el secreto real en disco fuera del
                # keyring cifrado: se deja un marcador no funcional.
                secret_key = cls.PROTECTED_PLACEHOLDER
            elif not secret_key:
                continue

            creds[profile] = {
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key,
            }

            section = 'default' if profile == cls.DEFAULT_PROFILE else f'profile {profile}'
            cfg[section] = {'region': region} if region else {}

        with open(cls.AWS_CREDENTIALS_FILE, 'w') as f:
            creds.write(f)
        cls.AWS_CREDENTIALS_FILE.chmod(0o600)

        with open(cls.AWS_CONFIG_FILE, 'w') as f:
            cfg.write(f)
        cls.AWS_CONFIG_FILE.chmod(0o600)

    # ------------------------------------------------------------------
    # Exportación / importación de perfiles, cifradas con contraseña.
    # ------------------------------------------------------------------
    @classmethod
    def export_profiles(cls, password: str, profiles: list | None = None) -> bytes:
        """Exporta perfiles (todos por defecto) cifrados con `password`.
        Devuelve los bytes listos para escribir a un archivo."""
        profile_names = profiles if profiles is not None else cls.list_profiles()

        payload = {"format_version": EXPORT_FORMAT_VERSION, "profiles": {}}
        for name in profile_names:
            access_key, secret_key, region = cls.load_credentials(name)
            if not (access_key and secret_key):
                continue
            payload["profiles"][name] = {
                "access_key": access_key,
                "secret_key": secret_key,
                "region": region,
            }

        if not payload["profiles"]:
            raise ValueError("No hay perfiles con credenciales para exportar.")

        plaintext = json.dumps(payload).encode('utf-8')
        return encrypt_with_password(plaintext, password)

    @classmethod
    def import_profiles(cls, blob: bytes, password: str,
                         overwrite: bool = True) -> tuple[bool, str]:
        """Importa perfiles desde un blob cifrado generado por
        `export_profiles`. Devuelve (hubo al menos un perfil importado,
        mensaje descriptivo para mostrar al usuario)."""
        if cls.is_master_password_enabled() and cls._session_key is None:
            return False, (
                "S3Manager está bloqueado. Desbloquéalo con la contraseña "
                "maestra (menú Archivo) antes de importar perfiles."
            )
        try:
            plaintext = decrypt_with_password(blob, password)
        except DecryptionError as e:
            return False, str(e)

        try:
            payload = json.loads(plaintext)
            profiles = payload["profiles"]
        except Exception:
            return False, "El archivo no tiene el formato esperado de S3Manager."

        if not profiles:
            return False, "El archivo no contiene ningún perfil."

        existing = set(cls.list_profiles())
        imported, skipped, failed = [], [], []

        for name, data in profiles.items():
            if not overwrite and name in existing:
                skipped.append(name)
                continue
            access_key = data.get("access_key", "")
            secret_key = data.get("secret_key", "")
            region = data.get("region", "")
            if not (access_key and secret_key):
                failed.append(name)
                continue
            ok, _err = cls.save_credentials(access_key, secret_key, region, profile=name)
            (imported if ok else failed).append(name)

        parts = [f"Perfiles importados: {', '.join(imported)}." if imported
                 else "No se importó ningún perfil."]
        if skipped:
            parts.append(f"Omitidos (ya existían): {', '.join(skipped)}.")
        if failed:
            parts.append(f"Con errores: {', '.join(failed)}.")

        return bool(imported), " ".join(parts)
