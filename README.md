# S3 Manager

Aplicación de escritorio para gestión de buckets AWS S3 en macOS.

## 🚀 Instalación Rápida

### Opción 1: Usar DMG (Recomendado)
1. Descargar `S3Manager.dmg`
2. Abrir el archivo DMG
3. Arrastrar S3Manager.app a Aplicaciones
4. Ejecutar desde Launchpad

### Opción 2: Ejecutar desde código fuente
```bash
python3 s3_manager_app.py
```

## 📋 Requisitos

- **macOS**: 10.15+ (Catalina o superior)
- **Arquitectura**: Intel x64 o Apple Silicon (ARM64)
- **Python**: 3.8+ (solo para desarrollo)

## 🔧 Desarrollo

### Construir aplicación
```bash
python3 build_macos_app.py
```

### Crear instalador DMG
```bash
python3 create_dmg_installer.py
```

### Ejecutar pruebas
```bash
cd tests
python3 test_s3_functionality.py
```

## 📚 Documentación

- [Requisitos del Sistema](docs/SYSTEM_REQUIREMENTS.md)
- [Guía de Usuario](docs/README_S3_Manager.md)
- [Reporte de Pruebas](docs/TESTING_FINAL_REPORT.md)

## 🎯 Funcionalidades

- ✅ **Visualización y gestión de buckets S3**: Lista todos tus buckets y muestra información detallada.
- ✅ **Creación de buckets**: Crea nuevos buckets directamente desde la aplicación, seleccionando la región de AWS.
- ✅ **Borrado seguro de buckets**: Elimina buckets y todo su contenido con un diálogo de confirmación para evitar borrados accidentales.
- ✅ **Gestión de archivos**: Descarga y eliminación selectiva de archivos dentro de un bucket.
- ✅ **Verificación de permisos**: Comprueba los permisos de lectura, escritura, borrado y listado para cada bucket.
- ✅ **Configuración de credenciales integrada**: Guarda de forma segura tus credenciales de AWS.
- ✅ **Interfaz gráfica moderna**: Diseñada para ser intuitiva y fácil de usar en macOS.
- ✅ **Aplicación nativa de macOS**: Empaquetada como una aplicación `.app` con instalador `.dmg`.

## 📞 Soporte

Para problemas o sugerencias, revisa la documentación en `docs/`.

---

**Desarrollado por**: EDF Developer  
**Versión**: 1.1.0  
**Licencia**: MIT
