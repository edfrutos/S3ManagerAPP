# Changelog S3Manager v1.2.4

## 🌗 Versión 1.2.4 - Tema configurable y versión para la Mac App Store (2026-11-18)

### ✨ Mejoras
- **Tema claro, oscuro o del sistema**: nuevo menú Ver > Apariencia con tres opciones: "Usar la del sistema" (por defecto), "Clara" y "Oscura". La elección se guarda entre sesiones. En modo sistema, la app cambia sola al cambiar la apariencia de macOS.
- Los botones de borrado se muestran en rojo en ambos temas, y los colores del registro se leen bien sobre fondo claro y oscuro.
- **Compatibilidad con App Sandbox** para la Mac App Store. En esa versión no se escribe en `~/.aws`, y los archivos que elige el usuario (descargas, exportar e importar perfiles y logs) se abren con el permiso del sandbox.
- **Build para la Mac App Store**: `make mas` genera el `.pkg` firmado para subirlo con Transporter. La versión Developer ID (`make release`) no cambia.

### 🐛 Correcciones
- **Texto invisible en modo oscuro**: los estilos fijaban fondos claros sin fijar el color del texto. Ahora cada tema tiene su propia hoja de estilo.
- Con App Sandbox, OpenSSL ya no intenta leer su configuración de Homebrew fuera de la app.
