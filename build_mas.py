#!/usr/bin/env python3
"""Construye la variante Mac App Store (sandbox) de S3Manager como .pkg.

Flujo:
  1. build_macos_app.py                -> build/S3Manager.app
  2. copia a build/mas/S3Manager.app   (la build Developer ID no se toca)
  3. CFBundleVersion = número de build; perfil en embedded.provisionprofile
  4. firma de dentro hacia fuera; la app con entitlements-mas.plist
  5. productbuild -> S3Manager-mas.pkg, firmado con el certificado Installer

Requisitos (variables de entorno):
  MAS_APP_IDENTITY        SHA-1 del certificado con el que se creó el perfil
                          ("Apple Distribution" o "3rd Party Mac Developer
                          Application"; ver security find-identity -v -p
                          codesigning)
  MAS_INSTALLER_IDENTITY  SHA-1 de "3rd Party Mac Developer Installer"
                          (hay duplicados: usar el SHA-1, no el nombre)
  MAS_PROFILE             ruta al .provisionprofile "Mac App Store" de
                          com.edefrutos.s3manager (no se versiona)

Opciones:
  --skip-build            usar la build/S3Manager.app existente
  --build-number N        CFBundleVersion (por defecto, la versión). Como
                          mucho tres enteros separados por puntos. App Store
                          Connect exige un valor distinto y creciente en
                          cada subida: usar un contador entero (1, 2, 3...).

Una app firmada para la Mac App Store no arranca fuera de la tienda: para
probarla, súbela a TestFlight (app Transporter).
"""

import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import sign_and_notarize as sn
from app_version import __version__

ROOT = Path(__file__).resolve().parent
SOURCE_APP = ROOT / "build" / "S3Manager.app"
MAS_DIR = ROOT / "build" / "mas"
APP = MAS_DIR / "S3Manager.app"
PKG = ROOT / "S3Manager-mas.pkg"
ENTITLEMENTS = ROOT / "entitlements-mas.plist"
BUNDLE_ID = "com.edefrutos.s3manager"
TEAM_ID = "V29BTBRY6G"

run = sn.run


def arg_value(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def check_profile(profile):
    """Comprueba que el perfil es de distribución para esta app."""
    out = subprocess.run(
        ["security", "cms", "-D", "-i", str(profile)],
        check=True, capture_output=True,
    ).stdout
    data = plistlib.loads(out)
    app_id = data.get("Entitlements", {}).get(
        "com.apple.application-identifier")
    if app_id != f"{TEAM_ID}.{BUNDLE_ID}":
        raise SystemExit(f"❌ El perfil es para {app_id}, no {BUNDLE_ID}")
    if "ProvisionedDevices" in data:
        raise SystemExit("❌ El perfil es de desarrollo; hace falta uno "
                         "de distribución Mac App Store")
    print(f"✅ Perfil '{data.get('Name')}' válido hasta "
          f"{data.get('ExpirationDate')}")


def set_build_number(build_number):
    info_path = APP / "Contents" / "Info.plist"
    with open(info_path, "rb") as f:
        info = plistlib.load(f)
    info["CFBundleVersion"] = build_number
    with open(info_path, "wb") as f:
        plistlib.dump(info, f)
    print(f"✅ CFBundleShortVersionString {info['CFBundleShortVersionString']}"
          f", CFBundleVersion {build_number}")


def main():
    sys.stdout.reconfigure(line_buffering=True)
    app_identity = os.environ.get("MAS_APP_IDENTITY")
    installer_identity = os.environ.get("MAS_INSTALLER_IDENTITY")
    profile = os.environ.get("MAS_PROFILE")
    build_number = arg_value("--build-number") or __version__
    if not re.fullmatch(r"\d+(\.\d+){0,2}", build_number):
        print(f"❌ --build-number '{build_number}' no válido: como mucho "
              "tres enteros separados por puntos (p. ej. 1, 2, 3...)")
        return 1

    missing = [n for n, v in (("MAS_APP_IDENTITY", app_identity),
                              ("MAS_INSTALLER_IDENTITY", installer_identity),
                              ("MAS_PROFILE", profile)) if not v]
    if missing:
        print("❌ Faltan variables de entorno: " + ", ".join(missing))
        return 1
    profile = Path(profile).expanduser()
    if not profile.is_file():
        print(f"❌ No existe el perfil {profile}")
        return 1
    check_profile(profile)

    os.chdir(ROOT)
    if "--skip-build" not in sys.argv:
        run([sys.executable, "build_macos_app.py"])
    if not SOURCE_APP.is_dir():
        print(f"❌ No existe {SOURCE_APP}")
        return 1

    # Copia aparte (ditto conserva los symlinks de los frameworks).
    shutil.rmtree(MAS_DIR, ignore_errors=True)
    MAS_DIR.mkdir(parents=True)
    run(["ditto", str(SOURCE_APP), str(APP)])

    set_build_number(build_number)
    shutil.copyfile(profile, APP / "Contents" / "embedded.provisionprofile")

    # La MAS rechaza archivos con com.apple.quarantine (p. ej. el perfil
    # descargado con el navegador). Se quitan todos los atributos
    # extendidos antes de firmar (la firma no añade ninguno).
    run(["xattr", "-cr", str(APP)])
    leftover = subprocess.run(["xattr", "-lr", str(APP)],
                              capture_output=True).stdout
    if b"com.apple.quarantine" in leftover:
        print("❌ Quedan archivos con com.apple.quarantine en la app")
        return 1

    sn.sign_app(app_identity, app=APP, entitlements=ENTITLEMENTS)

    print("📦 Creando el .pkg...")
    PKG.unlink(missing_ok=True)
    run(["productbuild", "--component", str(APP), "/Applications",
         "--sign", installer_identity, str(PKG)])
    run(["pkgutil", "--check-signature", str(PKG)])

    print(f"\n✅ {PKG.name} listo (versión {__version__}, build "
          f"{build_number}). Súbelo con Transporter.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Falló: {' '.join(str(c) for c in e.cmd)}")
        sys.exit(1)
