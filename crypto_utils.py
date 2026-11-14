#!/usr/bin/env python3
"""
Utilidades de cifrado simétrico basado en contraseña, para S3Manager.
Autor: EDF Developer - 2025

Usado por la exportación/importación de configuración y por el cifrado
adicional (opcional) de las credenciales guardadas localmente.
"""

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Recomendación OWASP (2023) para PBKDF2-HMAC-SHA256.
PBKDF2_ITERATIONS = 600_000
SALT_SIZE = 16


class DecryptionError(Exception):
    """Contraseña incorrecta o datos cifrados corruptos/no reconocidos."""


def generate_salt() -> bytes:
    return os.urandom(SALT_SIZE)


def derive_key(password: str, salt: bytes) -> bytes:
    """Deriva una clave Fernet (32 bytes, base64-urlsafe) a partir de una
    contraseña y un salt. Operación deliberadamente costosa (PBKDF2):
    debe llamarse una única vez por contraseña (p. ej. al desbloquear
    una sesión), nunca en un bucle por cada valor a cifrar/descifrar."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


def encrypt_with_key(plaintext: bytes, key: bytes) -> bytes:
    """Cifra con una clave ya derivada (operación barata)."""
    return Fernet(key).encrypt(plaintext)


def decrypt_with_key(token: bytes, key: bytes) -> bytes:
    """Descifra con una clave ya derivada. Lanza DecryptionError si la
    clave no corresponde o los datos están corruptos."""
    try:
        return Fernet(key).decrypt(token)
    except InvalidToken:
        raise DecryptionError("Clave incorrecta o datos corruptos.")


def encrypt_with_password(plaintext: bytes, password: str) -> bytes:
    """Cifra `plaintext` con una clave derivada de `password`.
    El salt (necesario para volver a derivar la misma clave al
    descifrar) se antepone al resultado, ya que no es secreto.
    Pensado para operaciones puntuales (exportar un archivo); para
    cifrar muchos valores con la misma contraseña, deriva la clave una
    vez con `derive_key` y usa `encrypt_with_key`/`decrypt_with_key`."""
    salt = generate_salt()
    key = derive_key(password, salt)
    token = encrypt_with_key(plaintext, key)
    return salt + token


def decrypt_with_password(blob: bytes, password: str) -> bytes:
    """Descifra un blob generado por `encrypt_with_password`.
    Lanza DecryptionError si la contraseña es incorrecta o el
    contenido no es válido."""
    if len(blob) <= SALT_SIZE:
        raise DecryptionError("El archivo no tiene un formato reconocido.")
    salt, token = blob[:SALT_SIZE], blob[SALT_SIZE:]
    key = derive_key(password, salt)
    return decrypt_with_key(token, key)
