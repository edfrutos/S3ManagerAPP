# Changelog S3Manager v1.2.0

## 👥 Versión 1.2.0 - Perfiles AWS y contraseña maestra (2026-11-14)

### ✨ Nuevas Funcionalidades
- **Perfiles AWS múltiples**: crear, editar, eliminar y cambiar de perfil desde la GUI (selector en la barra superior y diálogo de gestión).
- **Sincronización con `~/.aws`**: todos los perfiles se escriben en `~/.aws/credentials` y `~/.aws/config`, compatibles con aws-cli.
- **Contraseña maestra opcional**: los secrets del llavero se guardan cifrados (PBKDF2-HMAC-SHA256 + Fernet). La app pide la contraseña al arrancar y puede bloquearse.
- **Exportar/importar perfiles**: a un archivo cifrado con contraseña.

### 🐛 Correcciones
- **Verificar permisos se ejecutaba dos veces** por clic (la segunda en el hilo de la interfaz, bloqueándola). Ahora se ejecuta una vez y el panel usa ese resultado; el botón se restaura al terminar la operación.
- **Objeto de prueba de escritura** con nombre único (`.s3manager-permcheck-<uuid>.txt`): ya no puede sobrescribir un objeto real llamado `test-permissions-check.txt`.
- **Cierre con operación en curso**: la app espera al worker en lugar de destruir el `QThread` en ejecución.
- **Barra de progreso** que quedaba visible tras listar buckets o archivos con éxito.
- **Versión inconsistente**: "Acerca de" y el `Info.plist` mostraban 1.0.0.

### 🔧 Mejoras Técnicas
- Toolkit Qt unificado en **PySide6** (lanzador, comprobación del build y tests usaban PyQt6).
- Versión centralizada en `app_version.py`.
- Configuración de mypy unificada en `pyproject.toml` (se elimina `mypy.ini`).
- Nueva dependencia: `cryptography>=41.0.0`.
