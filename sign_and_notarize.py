#!/usr/bin/env python3
"""Firma con Developer ID, empaqueta y notariza S3Manager.

Flujo:
  1. build_macos_app.py           -> build/S3Manager.app
  2. firma de dentro hacia fuera  (hardened runtime + timestamp)
  3. create_dmg_installer.py --skip-build -> S3Manager.dmg
  4. firma del .dmg, notarytool submit --wait, stapler staple

Requisitos (variables de entorno):
  CODESIGN_IDENTITY  SHA-1 o nombre del certificado "Developer ID
                     Application" (ver: security find-identity -v -p codesigning)
  NOTARY_PROFILE     perfil guardado con `xcrun notarytool store-credentials`

Opciones:
  --skip-build       firmar la build/S3Manager.app existente
  --no-notarize      firmar y crear el .dmg sin enviarlo a Apple
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "build" / "S3Manager.app"
DMG = ROOT / "S3Manager.dmg"
ENTITLEMENTS = ROOT / "entitlements.plist"

MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe",  # 32 bits
    b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",  # 64 bits
    b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",  # universal
}


def run(cmd, **kwargs):
    print("$ " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, **kwargs)


def is_macho(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) in MACHO_MAGICS
    except OSError:
        return False


def codesign(path, identity, entitlements=False):
    cmd = [
        "codesign", "--force", "--timestamp", "--options", "runtime",
        "--sign", identity,
    ]
    if entitlements:
        cmd += ["--entitlements", str(ENTITLEMENTS)]
    run(cmd + [str(path)], stdout=subprocess.DEVNULL)


def sign_app(identity):
    """Firma de dentro hacia fuera: binarios sueltos, luego cada
    .framework y por último la app. Se ignoran los symlinks (se firma
    el archivo real una sola vez)."""
    contents = APP / "Contents"

    binaries = [
        p for p in contents.rglob("*")
        if p.is_file() and not p.is_symlink() and is_macho(p)
        and p.parent != contents / "MacOS"
    ]
    # Los más profundos primero
    binaries.sort(key=lambda p: len(p.parts), reverse=True)
    print(f"🔏 Firmando {len(binaries)} binarios internos...")
    for b in binaries:
        codesign(b, identity)

    frameworks = [
        p for p in contents.rglob("*.framework")
        if p.is_dir() and not p.is_symlink()
    ]
    frameworks.sort(key=lambda p: len(p.parts), reverse=True)
    print(f"🔏 Firmando {len(frameworks)} frameworks...")
    for fw in frameworks:
        codesign(fw, identity)

    print("🔏 Firmando la aplicación...")
    codesign(APP, identity, entitlements=True)

    run(["codesign", "--verify", "--deep", "--strict", "--verbose=2",
         str(APP)])


def main():
    sys.stdout.reconfigure(line_buffering=True)
    identity = os.environ.get("CODESIGN_IDENTITY")
    profile = os.environ.get("NOTARY_PROFILE")
    notarize = "--no-notarize" not in sys.argv

    if not identity:
        print("❌ Falta CODESIGN_IDENTITY (security find-identity -v -p codesigning)")
        return 1
    if notarize and not profile:
        print("❌ Falta NOTARY_PROFILE (xcrun notarytool store-credentials)")
        return 1

    os.chdir(ROOT)

    if "--skip-build" not in sys.argv:
        run([sys.executable, "build_macos_app.py"])
    if not APP.is_dir():
        print(f"❌ No existe {APP}")
        return 1

    sign_app(identity)

    run([sys.executable, "create_dmg_installer.py", "--skip-build"])
    print("🔏 Firmando el .dmg...")
    run(["codesign", "--force", "--timestamp", "--sign", identity, str(DMG)])

    if not notarize:
        print("⚠️  Sin notarizar (--no-notarize). Gatekeeper lo rechazará.")
        return 0

    print("☁️  Enviando a notarización (puede tardar unos minutos)...")
    run(["xcrun", "notarytool", "submit", str(DMG),
         "--keychain-profile", profile, "--wait"])
    run(["xcrun", "stapler", "staple", str(DMG)])
    run(["xcrun", "stapler", "validate", str(DMG)])
    run(["spctl", "--assess", "--type", "open",
         "--context", "context:primary-signature", "--verbose", str(DMG)])
    print(f"\n✅ {DMG.name} firmado, notarizado y grapado")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Falló: {' '.join(str(c) for c in e.cmd)}")
        sys.exit(1)
