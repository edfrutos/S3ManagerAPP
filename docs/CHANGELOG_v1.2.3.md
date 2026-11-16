# Changelog S3Manager v1.2.3

## 🔐 Versión 1.2.3 - Aviso de contraseña maestra y aws-cli (2026-11-16)

### ✨ Mejoras
- **Aviso al activar la contraseña maestra**: mientras está activa, S3Manager no escribe la clave secreta real en `~/.aws/credentials` (deja un marcador), así que aws-cli y otras herramientas fallan con `SignatureDoesNotMatch` para esos perfiles. Ahora se avisa antes de activarla, con la alternativa (exportar `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` o desactivarla), y hay que confirmar para continuar.
- **Aviso al desactivarla**: se indica que la clave secreta volverá a escribirse sin cifrar en `~/.aws/credentials` (permisos 600).
