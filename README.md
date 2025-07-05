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

- ✅ Gestión completa de buckets S3
- ✅ Descarga y eliminación selectiva de archivos
- ✅ Verificación detallada de permisos
- ✅ Configuración de credenciales integrada
- ✅ Primera ejecución guiada
- ✅ Interfaz gráfica moderna
- ✅ Aplicación nativa de macOS
- ✅ Instalador DMG

## 📞 Soporte

Para problemas o sugerencias, revisa la documentación en `docs/`.

---

**Desarrollado por**: EDF Developer  
**Versión**: 1.1.0  
**Licencia**: MIT
