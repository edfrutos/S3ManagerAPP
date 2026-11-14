# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es

S3Manager: aplicación de escritorio macOS (PySide6 + boto3) para gestionar buckets AWS S3 — listar/crear/borrar buckets, descargar/borrar objetos, verificar permisos y gestionar perfiles de credenciales AWS. Se empaqueta como `.app` con PyInstaller y se distribuye en `.dmg`. Proyecto en español (UI, logs, docs, commits).

## Comandos

Entorno: Python 3.10, virtualenv en `venv310/` (no versionado).

```bash
source venv310/bin/activate          # o ./activate_env.sh (añade el repo al PYTHONPATH)
pip install -r requirements.txt      # make install

python s3_manager_app.py             # ejecutar la GUI desde código fuente
python diagnose_s3_permissions.py    # herramienta CLI interactiva (misma lógica S3)

make build                           # python3 build_macos_app.py → build/S3Manager.app (PyInstaller)
make dmg                             # build + create_dmg_installer.py → S3Manager.dmg
make clean
```

Tests (`tests/`): scripts con funciones `test_*`, ejecutables con pytest o directamente:

```bash
python -m pytest tests/                                            # todos
python -m pytest tests/test_s3_functionality.py                    # un archivo
python -m pytest tests/test_s3_functionality.py::test_list_bucket_contents   # un test
make test                                                          # ejecuta 3 scripts desde tests/
```

Importante: la mayoría de tests son de integración contra AWS real (credenciales activas y buckets concretos, p. ej. `efjdefrutos-com`) o contra la GUI/`.app` construida; no son unitarios aislados. `TEST_MODE=1` hace que `AWSCredentialsManager` no escriba en el keyring.

Lint/tipos (configurados en `pyproject.toml`, sin hook automático; no instalados en `venv310`): `ruff check .`, `black --line-length 79 .`, `mypy <archivos>`. La config de mypy es permisiva (sin exigir anotaciones); hay ~14 errores previos.

## Arquitectura

Todo el código vive en módulos planos en la raíz (sin paquete):

- **`s3_manager_app.py`** — GUI completa. `S3ManagerApp` (QMainWindow) con pestañas `BucketTab`, `FilesTab`, `LogTab`, más diálogos (`CreateBucketDialog`, `AWSProfilesDialog`, contraseña maestra). Todas las operaciones S3 pasan por un único `S3Worker(QThread)`: `start_operation(nombre, **kwargs)` → `S3Worker.run()` despacha por string (`list_buckets`, `list_files`, `download_files`, `delete_files`, `check_permissions`, `delete_bucket`, `create_bucket`) y comunica con la UI vía señales (`progress_updated`, `operation_completed`, `bucket_list_ready`, `file_list_ready`, `log_message`). Solo una operación a la vez (se rechaza si el worker está corriendo).
  - `S3ManagerApp.operation_completed` decide qué refrescar **haciendo match sobre el texto del mensaje** de éxito (`"El bucket ... han sido eliminados"`, `"eliminaron"`, `"Resultados de verificación"`). Cambiar esos mensajes en el worker o en `diagnose_s3_permissions.py` rompe el refresco de la UI.
- **`diagnose_s3_permissions.py`** — originalmente CLI interactiva; sus funciones (`test_s3_connection`, `list_bucket_contents`, `check_bucket_permissions`, `download_selected_files`, `delete_selected_files`, `delete_bucket_and_contents`, `create_s3_bucket`, …) son la capa S3 real que reutiliza la GUI y los tests. Crean clientes con `boto3.client('s3')`, es decir, dependen de la sesión por defecto de boto3. `build_macos_app.py` lo incluye explícitamente con `--add-data`.
  - `diagnose_s3_permissions_fixed.py` / `_working.py` son variantes huérfanas no referenciadas.
- **`aws_credentials_manager.py`** — `AWSCredentialsManager` (solo classmethods, estado global de proceso). Multiperfil al estilo AWS CLI:
  - Secretos solo en el keyring del sistema (servicio `S3Manager`; usuario `AWS_ACCESS_KEY_ID` para `default`, `<perfil>::AWS_ACCESS_KEY_ID` para el resto).
  - Metadatos sin secretos (perfiles, región, perfil activo, estado de contraseña maestra) en `~/.s3manager/config.json`.
  - `~/.aws/credentials` y `~/.aws/config` se reescriben (`_sync_aws_files`) con todos los perfiles para que aws-cli los use; con contraseña maestra activa el secret se sustituye por `PROTECTED_PLACEHOLDER`.
  - Activar un perfil (`_activate_in_process`) exporta variables `AWS_*` y llama a `boto3.setup_default_session(...)`; esto es imprescindible porque boto3 cachea credenciales en la sesión global y `diagnose_s3_permissions` depende de ella.
  - Contraseña maestra opcional: clave derivada (PBKDF2) cacheada solo en memoria en `_session_key`; el secret en keyring se guarda cifrado con Fernet. Al arrancar, `ensure_unlocked()` pide la contraseña antes de cargar credenciales.
  - Exportar/importar perfiles a archivo cifrado con contraseña.
- **`crypto_utils.py`** — Fernet + PBKDF2-HMAC-SHA256 (600k iteraciones). `derive_key` es caro: derivar una vez por sesión y usar `encrypt_with_key`/`decrypt_with_key`; `encrypt_with_password` antepone el salt de 16 bytes al token.
- **Empaquetado** — `build_macos_app.py` (PyInstaller `--windowed --onedir`, Info.plist propio, `icon.icns`), `create_dmg_installer.py` / `create_simple_dmg.py`. La versión vive en `app_version.py` (`__version__`), que usan la GUI y el `Info.plist` de `build_macos_app.py`; `pyproject.toml` y `README.md` la repiten a mano: mantenerlas sincronizadas.

## Notas

- El toolkit Qt es **PySide6** (`Signal` se importa con alias `pyqtSignal`). No introducir imports de PyQt6.
- La app no conecta a AWS al arrancar (evita cuelgues por red); el usuario pulsa "Actualizar". Ver `NETWORK_ISSUE_ANALYSIS.md`.
- Docs vigentes en `docs/*_v1.1*.md` y `docs/CHANGELOG_v1.1.1.md`; `docs/archive/` es obsoleto.
- `graphify-out/` contiene un grafo de conocimiento del repo (`graphify query "<pregunta>"`).
