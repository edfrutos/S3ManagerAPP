# Changelog S3Manager v1.2.1

## 🔏 Versión 1.2.1 - Instalador firmado y notarizado (2026-11-15)

### ✨ Distribución
- **Firma Developer ID y notarización de Apple**: el `.dmg` y la app están firmados (hardened runtime), notarizados y grapados. Gatekeeper los abre sin avisos, también sin conexión.
- **Nuevo identificador de paquete**: `com.edefrutos.s3manager` (antes `com.catalogotablas.s3manager`). macOS la trata como una app distinta: conviene borrar la versión anterior de Aplicaciones. Las credenciales del llavero se conservan.
- **`make release`** (`sign_and_notarize.py`): build, firma de dentro hacia fuera, DMG, notarización, staple y verificación con `spctl`. Requiere `CODESIGN_IDENTITY` y `NOTARY_PROFILE`.

### 🐛 Correcciones
- **Firma inválida dentro del DMG**: se escribía un marcador `first_run` dentro de la `.app` tras firmarla. La marca de primera ejecución vive ahora en `~/.s3manager_first_run`.
- **DMG de 245 MB**: al copiar la app no se conservaban los symlinks de los frameworks Qt (duplicados). Ahora se preservan: el DMG ocupa 63 MB.
- **`make dmg` construía la app dos veces**.
