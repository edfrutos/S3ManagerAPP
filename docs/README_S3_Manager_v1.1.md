# S3 Manager v1.1.0

Aplicación de escritorio profesional para gestión de buckets AWS S3 en macOS.

## 🎯 Características Principales

- ✅ **Gestión Completa**: Buckets, archivos, permisos y configuración
- ✅ **Interfaz Moderna**: GUI nativa de macOS con PySide6
- ✅ **Primera Ejecución**: Configuración guiada de credenciales AWS
- ✅ **Verificación Avanzada**: Permisos detallados y diagnósticos
- ✅ **Operaciones Selectivas**: Descarga y eliminación de archivos
- ✅ **Aplicación Nativa**: Sin dependencias externas
- ✅ **Universal Binary**: Compatible Intel x64 y Apple Silicon ARM64
- ✅ **Instalador DMG**: Distribución profesional

## 🚀 Instalación

### Opción 1: Instalador DMG (Recomendado)
1. Descargar `S3Manager.dmg`
2. Abrir el archivo DMG
3. Arrastrar S3Manager.app a Aplicaciones
4. Ejecutar desde Launchpad o Finder

### Opción 2: Desde código fuente
```bash
# Clonar o descargar el proyecto
cd S3Manager

# Instalar dependencias (solo para desarrollo)
make install

# Ejecutar aplicación
python3 s3_manager_app.py
```

## 📋 Requisitos del Sistema

- **macOS**: 10.15+ (Catalina, Big Sur, Monterey, Ventura, Sonoma, Sequoia)
- **Arquitectura**: Intel x64 o Apple Silicon (ARM64)
- **Memoria**: 4 GB RAM mínimo, 8 GB recomendado
- **Espacio**: 500 MB libres
- **Credenciales AWS**: Access Key ID y Secret Access Key

## 🔧 Desarrollo

### Comandos Disponibles
```bash
make help      # Mostrar ayuda
make install   # Instalar dependencias
make build     # Construir aplicación
make dmg       # Crear instalador DMG
make test      # Ejecutar pruebas
make clean     # Limpiar archivos generados
```

### Construcción Manual
```bash
# Construir aplicación
python3 build_macos_app.py

# Crear instalador
python3 create_dmg_installer.py

# Ejecutar pruebas
cd tests && python3 test_s3_functionality.py
```

## 📚 Documentación

- [Guía de Usuario Completa](README_S3_Manager_v1.1.md)
- [Requisitos del Sistema](SYSTEM_REQUIREMENTS_v1.1.md)
- [Reporte de Pruebas](TESTING_FINAL_REPORT_v1.1.md)
- [Historial de Cambios](CHANGELOG_v1.1.md)

## 🎮 Uso de la Aplicación

### Primera Ejecución
1. Al abrir la aplicación por primera vez, aparecerá un diálogo de configuración
2. Introducir credenciales AWS (Access Key ID y Secret Access Key)
3. Seleccionar región por defecto
4. La aplicación se conectará automáticamente

### Gestión de Buckets
- **Pestaña Buckets**: Ver todos los buckets disponibles
- **Verificar Permisos**: Comprobar accesos de lectura, escritura y eliminación
- **Ver Archivos**: Navegar al contenido del bucket

### Gestión de Archivos
- **Pestaña Archivos**: Ver contenido del bucket seleccionado
- **Selección Múltiple**: Checkboxes para seleccionar archivos
- **Descarga**: Elegir directorio de destino
- **Eliminación**: Confirmación de seguridad incluida

### Logs y Diagnósticos
- **Pestaña Logs**: Historial completo de operaciones
- **Exportar**: Guardar logs en archivo de texto
- **Diagnósticos**: Información detallada de errores

## 🧪 Pruebas

El proyecto incluye una suite completa de pruebas:

- **Funcionalidades Core**: 39 pruebas
- **Instalador DMG**: 5 pruebas
- **Distribución**: 8 pruebas
- **Rendimiento**: 7 pruebas
- **Compatibilidad**: 5 pruebas

**Total**: 64/65 pruebas exitosas (98.5%)

## 🔒 Seguridad

- Las credenciales se almacenan de forma segura en el sistema
- Conexiones HTTPS con AWS
- Validación de permisos antes de operaciones
- Confirmaciones para operaciones destructivas

## 📞 Soporte

### Problemas Comunes
1. **App no abre**: Ir a Preferencias > Seguridad y Privacidad > Permitir
2. **Credenciales inválidas**: Verificar Access Key y Secret Key
3. **Sin permisos**: Comprobar políticas IAM en AWS

### Logs de Diagnóstico
Los logs se encuentran en la pestaña "Logs" de la aplicación y pueden exportarse para análisis.

## 🏗️ Arquitectura

- **Frontend**: PySide6 (Qt para Python)
- **Backend**: boto3 para AWS S3
- **Empaquetado**: PyInstaller
- **Distribución**: DMG nativo de macOS

## 📈 Rendimiento

- **Arranque**: < 3 segundos
- **Memoria**: 150-200 MB en uso normal
- **CPU**: Optimizado para ambas arquitecturas
- **Red**: Conexiones eficientes con AWS

## 🔄 Historial de Versiones

### v1.1.0 (Actual)
- Proyecto independiente migrado
- Bibliotecas Python completas incluidas
- Sistema de construcción automatizado
- Documentación actualizada

### v1.0.0
- Lanzamiento inicial
- Funcionalidades base implementadas

---

**Desarrollado por**: EDF Developer  
**Versión**: 1.1.0  
**Fecha**: 30 Junio 2025  
**Licencia**: MIT  
**Repositorio**: Proyecto independiente S3Manager
