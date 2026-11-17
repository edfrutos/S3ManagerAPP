# Plan: S3Manager en la Mac App Store (sandbox)

Objetivo: publicar en la Mac App Store una variante sandbox de S3Manager sin
romper la versión de descarga directa (Developer ID, `make release`).

## Situación actual

| Requisito MAS | Estado |
|---|---|
| Certificados "3rd Party Mac Developer Application" e "Installer" | ✅ en el llavero (el de Installer está **duplicado**: firmar por SHA-1) |
| App registrada en App Store Connect (`com.edefrutos.s3manager`) | ✅ |
| Perfil de aprovisionamiento "Mac App Store" | ❌ crear en developer.apple.com |
| App Sandbox | ❌ `entitlements.plist` vacío |
| Escritura fuera del contenedor | ❌ `~/.aws` (sync aws-cli) |
| `.pkg` firmado con productbuild | ❌ |
| Info.plist: `LSApplicationCategoryType`, `ITSAppUsesNonExemptEncryption` | ❌ |
| `LSMinimumSystemVersion` | ⚠️ 10.15, pero el binario es solo arm64 (requiere 11.0) |

## Qué cambia dentro del sandbox

- `Path.home()` apunta al contenedor (`~/Library/Containers/com.edefrutos.s3manager/Data`).
  `~/.s3manager/config.json` y `~/.s3manager_first_run` funcionan sin cambios, pero
  dentro del contenedor.
- `~/.aws` real **no es accesible**. `_sync_aws_files` escribiría en el `.aws` del
  contenedor, que ningún aws-cli lee. La función "compatible con aws-cli" desaparece en
  la versión MAS.
- Los diálogos nativos (`QFileDialog` sin `DontUseNativeDialog`, como ahora) conceden
  acceso al archivo o carpeta elegidos (powerbox). Afecta a descargas, exportar logs y
  exportar/importar perfiles. Con `files.user-selected.read-write` deberían funcionar.
- Llavero: el sandbox permite los ítems que crea la propia app. Los que creó la versión
  Developer ID tienen otra firma, así que pueden pedir permiso o no ser accesibles. La
  migración se hace con exportar/importar perfiles o volviendo a introducir las claves.
  **Hay que comprobarlo en el spike.**

Detección en tiempo de ejecución, sin flag de build:
`os.environ.get("APP_SANDBOX_CONTAINER_ID")` está definida solo dentro del sandbox.

## Resultados del spike (fase 0, 2026-11-17)

Build 1.2.3 firmada con Developer ID + `app-sandbox`, `network.client`,
`files.user-selected.read-write`, más una app mínima de prueba (SbxTest, PySide6 6.11).

| Prueba | Resultado |
|---|---|
| Arranque Qt, contenedor creado | ✅ |
| boto3: listar buckets, verificar permisos, listar archivos | ✅ |
| Llavero: claves guardadas por la versión Developer ID | ✅ con un aviso del Llavero («Permitir») la primera vez; no hace falta migrar |
| Descargar / exportar logs con `open()` de Python en la carpeta elegida | ❌ `[Errno 1] Operation not permitted` (Escritorio, Descargas y ESSAGER) |
| Escribir con `QFile` en la carpeta o archivo elegido | ✅ |
| `QDir.mkpath` (subcarpetas) | ❌ |
| Python con un `QFile` **abierto** dentro de la carpeta elegida | ✅ incluido `os.makedirs` de subcarpetas |
| Python tras `CFURLStartAccessingSecurityScopedResource` sobre el marcador de Qt | ✅ |
| Avisos menores | lectura denegada de `/opt/homebrew/etc/openssl@3/openssl.cnf` y `network-bind`; sin efecto visible |

**Causa:** con sandbox, QtCore 6.11 registra un `SecurityScopedFileEngine`. Guarda el
permiso del panel como marcador en
`~/Library/Application Support/SecurityScopedBookmarks.plist` (dentro del contenedor) y
solo activa el acceso mientras hay un `QFile` abierto. Lo que escribe Python directamente
(boto3 `download_file`, `open()`, `os.makedirs`) no tiene permiso.

**Solución elegida (API pública de Qt):**
- Archivo elegido (exportar logs, exportar/importar perfiles): leer y escribir con `QFile`.
- Carpeta de descargas: mantener abierto un `QFile` oculto (`.s3manager-acceso`) dentro
  de la carpeta mientras dura la descarga, y borrarlo al acabar. Así boto3 y `os.makedirs`
  funcionan, también en subcarpetas.
- Descartado: leer el plist de marcadores de Qt con ctypes. Funciona, pero depende de un
  detalle interno de Qt.

## Fases

### Fase 0: spike para reducir riesgo (½ día)
1. Firmar la build actual con Developer ID y estas entitlements:
   `app-sandbox`, `network.client`, `files.user-selected.read-write`.
   No hace falta perfil para probar en local.
2. Comprobar:
   - Qt arranca.
   - boto3 conecta (`list_buckets`).
   - keyring guarda y lee.
   - Diálogos de descarga y exportación.
   - Se crea el contenedor.
3. Resultado: lista de qué falla en el sandbox. Si keyring o Qt no funcionan, replantear
   antes de seguir.

### Fase 1: código (rama `feat/sandbox-mas`) ✅
Hecho y probado con la build sandbox local: descargas (también a ESSAGER),
exportar logs y exportar/importar perfiles. PySide6 fijado a `6.11.*`.
Pendiente de esta fase: `openssl.cnf` (se revisa en la fase 2).

- `aws_credentials_manager.py`:
  - `IS_SANDBOXED` según la variable de arriba.
  - Si está en sandbox: `_sync_aws_files` no hace nada, y `load_credentials` no usa
    `~/.aws` como respaldo.
- `s3_manager_app.py`:
  - Ocultar o ajustar los textos que prometen sincronización con aws-cli en sandbox.
  - Aviso de contraseña maestra solo si no está en sandbox (en sandbox, el marcador en
    `~/.aws` no aplica).
- Escrituras en rutas elegidas por el usuario (ver «Resultados del spike»):
  - `export_logs` y exportar/importar perfiles con `QFile`.
  - `download_selected` mantiene un `QFile` abierto en la carpeta de destino mientras
    el `S3Worker` descarga.
  - Válido en las dos variantes: sin sandbox, `QFile` se comporta como `open()`.
- Empaquetado: evitar que el Python incluido busque `openssl.cnf` en `/opt/homebrew`
  (denegado en sandbox, inocuo). Revisarlo en la fase 2.
- (Opcional, más adelante) "Importar desde ~/.aws/credentials…" con un diálogo de abrir
  archivo, para migrar perfiles de aws-cli en la versión MAS.
- `diagnose_s3_permissions.py:43` solo informa de si existe `~/.aws/credentials` (CLI).
  Sin impacto en la GUI.

### Fase 2: build MAS (`build_mas.py` + `make mas`)
- **Info.plist (ambas variantes):**
  - `LSApplicationCategoryType = public.app-category.developer-tools`
  - `ITSAppUsesNonExemptEncryption = false`
  - `LSMinimumSystemVersion = 11.0`
  - `CFBundleVersion` con número de build creciente: cada subida a ASC lo exige único.
- **Reducir el bundle** excluyendo módulos Qt que no se usan: Qml/Quick, Pdf,
  VirtualKeyboard, DBus, OpenGL. Menos binarios que firmar y que Apple analice.
- **`entitlements-mas.plist`:**
  `com.apple.security.app-sandbox`, `com.apple.security.network.client`,
  `com.apple.security.files.user-selected.read-write`,
  `com.apple.application-identifier = V29BTBRY6G.com.edefrutos.s3manager`,
  `com.apple.developer.team-identifier = V29BTBRY6G`.
- Copiar el perfil a `Contents/embedded.provisionprofile` antes de firmar.
- **Firma de dentro hacia fuera** con "3rd Party Mac Developer Application", reutilizando
  `sign_app()` con identidad y entitlements parametrizados. Las `.so`/`.dylib` van sin
  entitlements y la app con las de MAS. El hardened runtime no es obligatorio en MAS.
- **Empaquetado:**
  `productbuild --component build/S3Manager.app /Applications --sign <SHA-1 Installer> S3Manager.pkg`
- **Subida con la app Transporter** (lo más sencillo). Alternativa: `xcrun altool --upload-app`
  con API key; confirmar que sigue admitido para subidas.

### Fase 3: pruebas
- **Local:** variante sandbox firmada con Developer ID (fase 0), con todas las operaciones:
  - Listar, crear y borrar bucket.
  - Descargar a una carpeta elegida.
  - Borrar objetos.
  - Verificar permisos.
  - Perfiles: crear, cambiar, exportar e importar.
  - Contraseña maestra.
- **TestFlight para macOS:** subir el `.pkg`, instalar desde TestFlight y repetir las
  pruebas. Es la única forma de probar la firma MAS real, porque una app firmada para
  distribución MAS no arranca fuera de la tienda.
- Mantener `make release` (Developer ID) sin cambios y comprobarlo.

### Fase 4: ficha y web
- **Descripción MAS:** quitar "Compatible con aws-cli: los perfiles se sincronizan con
  ~/.aws".
- **Privacidad** (efjdev.com/privacidad): indicar que la versión de la App Store no escribe
  en `~/.aws`.
- **Capturas:** 16:10.
- **Notas para el revisor:** ya preparadas (bucket `s3manager-review-edf`).

## Riesgos y dudas abiertas

- **PyInstaller + PySide6 en la MAS:** hay apps aceptadas, pero el análisis estático de
  Apple puede marcar símbolos de Qt o Python como API privada. TestFlight lo detecta antes
  de la revisión.
- **Solo arm64:** no estoy seguro de que la MAS acepte builds solo arm64 sin restricciones
  (los Mac Intel no podrían instalarla). Alternativa: build universal2, que exige Python y
  wheels universal2.
- **Llavero:** resuelto en el spike: los ítems de la versión Developer ID son accesibles
  tras un aviso del Llavero. Confirmar con la firma MAS real en TestFlight.
- **Qt y el sandbox:** el `SecurityScopedFileEngine` de Qt es interno. Si una versión
  futura de PySide6 cambia su comportamiento, las descargas volverían a fallar.
  Fijar la versión de PySide6 y repetir la prueba de descarga en cada actualización.
- **Dos variantes con el mismo bundle id:** se pueden instalar las dos, pero comparten
  identificador. Comprobar que no colisionen en Launch Services ni en el llavero.

## Estimación
Unos 3–4 días de trabajo: fase 0 ½ día, fase 1 1 día, fase 2 1 día, fase 3 1 día
(más las esperas de TestFlight), fase 4 ½ día.

Bloqueante externo: crear el perfil "Mac App Store" en developer.apple.com
(Certificates, Identifiers & Profiles → Profiles → + → Mac App Store Connect →
App ID `com.edefrutos.s3manager` → certificado 3rd Party Mac Developer Application).
