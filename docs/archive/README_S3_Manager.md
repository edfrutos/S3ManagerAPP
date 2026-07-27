# S3 Manager - Aplicación de Escritorio macOS

Una aplicación moderna de escritorio para gestionar buckets de Amazon S3 con interfaz gráfica intuitiva.

## 🎯 Características

### ✨ Funcionalidades Principales
- **📦 Gestión de Buckets**: Lista y selecciona buckets S3
- **📁 Exploración de Archivos**: Visualiza archivos con detalles (tamaño, fecha)
- **⬇️ Descarga Selectiva**: Selecciona uno, varios o todos los archivos
- **🗑️ Eliminación Selectiva**: Elimina archivos específicos con confirmaciones de seguridad
- **🔍 Verificación de Permisos**: Diagnóstica permisos y configuración de buckets
- **📋 Logs Detallados**: Registro completo de operaciones

### 🎨 Interfaz de Usuario
- **Diseño moderno**: Estilo similar a aplicaciones nativas de macOS
- **Pestañas organizadas**: Buckets, Archivos y Logs
- **Selección múltiple**: Checkboxes, rangos (1-5), listas (1,3,5)
- **Progreso en tiempo real**: Barras de progreso para operaciones largas
- **Confirmaciones de seguridad**: Advertencias para operaciones destructivas

## 🚀 Instalación y Uso

### Opción 1: Aplicación Nativa (.app)
```bash
# La aplicación ya está construida en:
tools/aws_utils/build/S3Manager.app

# Para usar:
1. Navega a la carpeta build/
2. Haz doble clic en S3Manager.app
3. Si macOS bloquea la app, ve a Preferencias > Seguridad y Privacidad
```

### Opción 2: Script de Python
```bash
# Ejecutar directamente desde código fuente
cd tools/aws_utils/
python3 s3_manager_app.py
```

### Opción 3: Script de Lanzamiento
```bash
# Usar el script de lanzamiento automático
./tools/aws_utils/launch_s3_manager.sh
```

## ⚙️ Configuración de AWS

### Credenciales Requeridas
La aplicación necesita credenciales AWS válidas. Configúralas usando cualquiera de estos métodos:

#### 1. Variables de Entorno
```bash
export AWS_ACCESS_KEY_ID="tu_access_key"
export AWS_SECRET_ACCESS_KEY="tu_secret_key"
export AWS_DEFAULT_REGION="tu_region"
```

#### 2. AWS CLI
```bash
aws configure
```

#### 3. Archivo de Credenciales
```bash
# Crear ~/.aws/credentials
[default]
aws_access_key_id = tu_access_key
aws_secret_access_key = tu_secret_key
region = tu_region
```

## 📖 Guía de Uso

### 1. Gestión de Buckets
- **Ver buckets**: La aplicación lista automáticamente todos tus buckets
- **Seleccionar bucket**: Haz clic en un bucket para ver sus detalles
- **Verificar permisos**: Usa el botón "🔍 Verificar Permisos"
- **Ver archivos**: Usa el botón "📁 Ver Archivos" o cambia a la pestaña Archivos

### 2. Descarga de Archivos
1. Selecciona un bucket desde la pestaña Buckets
2. Ve a la pestaña Archivos
3. Selecciona archivos usando:
   - **Checkboxes individuales**: Marca los archivos deseados
   - **Seleccionar Todo**: Botón "✅ Seleccionar Todo"
   - **Deseleccionar Todo**: Botón "❌ Deseleccionar Todo"
4. Haz clic en "⬇️ Descargar Seleccionados"
5. Elige el directorio de destino

### 3. Eliminación de Archivos
1. Selecciona archivos como en la descarga
2. Haz clic en "🗑️ Eliminar Seleccionados"
3. **⚠️ CONFIRMA** la eliminación (no se puede deshacer)
4. La aplicación pedirá confirmación múltiple para seguridad

### 4. Logs y Diagnósticos
- **Pestaña Logs**: Ve todos los eventos y operaciones
- **Exportar logs**: Guarda logs en archivo de texto
- **Limpiar logs**: Borra el historial de logs

## 🔧 Opciones de Selección Avanzadas

### Selección de Archivos
La aplicación soporta múltiples métodos de selección:

```
Ejemplos de selección:
- Individual: Marca checkbox del archivo
- Múltiple: Usa Cmd+clic en checkboxes
- Todos: Botón "Seleccionar Todo"
- Ninguno: Botón "Deseleccionar Todo"
```

### Funciones de Seguridad
- **Confirmación simple**: Para archivos individuales
- **Doble confirmación**: Para múltiples archivos
- **Confirmación especial**: Para eliminar todos los archivos
- **Advertencias visuales**: Emojis y colores de alerta
- **Resumen detallado**: Muestra qué se va a eliminar

## 🛠️ Desarrollo y Construcción

### Dependencias
```bash
pip install PyQt6 boto3 pyinstaller Pillow
```

### Construir la Aplicación
```bash
# Construir aplicación nativa
python3 build_macos_app.py

# Crear icono personalizado
python3 create_app_icon.py
```

### Estructura del Proyecto
```
tools/aws_utils/
├── s3_manager_app.py           # Aplicación principal
├── diagnose_s3_permissions.py  # Funciones de backend
├── build_macos_app.py          # Constructor de app nativa
├── create_app_icon.py          # Generador de iconos
├── launch_s3_manager.sh        # Script de lanzamiento
├── build/
│   └── S3Manager.app          # Aplicación nativa
└── test_*.py                  # Scripts de pruebas
```

## 🧪 Pruebas

### Scripts de Prueba Disponibles
```bash
# Pruebas de funcionalidad básica
python3 test_s3_functionality.py

# Pruebas de eliminación
python3 test_deletion_functionality.py

# Pruebas de integración completa
python3 test_integration_complete.py

# Pruebas de integración avanzadas
python3 test_integration_advanced.py
```

### Resultados de Pruebas
- ✅ **Descarga**: 100% exitosa (4/4 pruebas)
- ✅ **Eliminación**: 100% exitosa (4/4 pruebas)  
- ✅ **Integración**: 100% exitosa (5/5 pruebas)
- ✅ **Integración Avanzada**: 100% exitosa (5/5 pruebas)
  - ✓ Verificación de Permisos (4/4 permisos)
  - ✓ Flujo de Selección de Bucket
  - ✓ Operaciones con Archivos
  - ✓ Manejo de Errores
  - ✓ Operaciones en Hilos de Trabajo

## 🔒 Seguridad

### Medidas Implementadas
- **Credenciales seguras**: No se almacenan en la aplicación
- **Confirmaciones múltiples**: Para operaciones destructivas
- **Validación de entrada**: Previene errores de usuario
- **Logs auditables**: Registro de todas las operaciones
- **Manejo de errores**: Captura y maneja errores de AWS
  - ✓ Buckets inexistentes
  - ✓ Permisos insuficientes
  - ✓ Errores de red
  - ✓ Errores de autenticación

### Buenas Prácticas
- Usa credenciales con permisos mínimos necesarios
- Revisa siempre los archivos antes de eliminar
- Mantén backups de datos importantes
- Verifica permisos antes de operaciones masivas

## 📋 Requisitos del Sistema

### macOS
- **Versión mínima**: macOS 10.15 (Catalina)
- **Arquitectura**: Intel x64 o Apple Silicon (M1/M2)
- **Memoria**: 512 MB RAM mínimo
- **Espacio**: 100 MB para la aplicación

### Python (para desarrollo)
- **Versión**: Python 3.8 o superior
- **Dependencias**: PyQt6, boto3, pyinstaller, Pillow

## 🆘 Solución de Problemas

### Problemas Comunes

#### "La aplicación no puede abrirse"
```bash
# Solución: Permitir aplicación en Seguridad
1. Ve a Preferencias del Sistema > Seguridad y Privacidad
2. En la pestaña General, haz clic en "Abrir de todas formas"
3. O ejecuta: xattr -cr /ruta/a/S3Manager.app
```

#### "Credenciales no encontradas"
```bash
# Verificar credenciales
aws sts get-caller-identity

# Configurar si es necesario
aws configure
```

#### "Error de conexión S3"
```bash
# Verificar conectividad
ping s3.amazonaws.com

# Verificar región
aws s3 ls --region tu-region
```

#### "Aplicación se cierra inesperadamente"
```bash
# Ejecutar desde terminal para ver errores
cd tools/aws_utils/build/S3Manager.app/Contents/MacOS/
./S3Manager
```

## 📞 Soporte

### Logs de Depuración
Los logs se guardan en la pestaña Logs de la aplicación y pueden exportarse para análisis.

### Información del Sistema
- **Versión**: 1.0.0
- **Autor**: Sistema de Catálogo de Tablas
- **Fecha**: 2025
- **Licencia**: Uso interno

## 🎉 Características Destacadas

### Innovaciones Implementadas
- **Selección múltiple intuitiva**: Inspirada en Finder de macOS
- **Interfaz adaptativa**: Se ajusta al contenido dinámicamente
- **Operaciones en segundo plano**: No bloquea la interfaz
- **Feedback visual rico**: Emojis y colores para mejor UX
- **Arquitectura modular**: Fácil mantenimiento y extensión
- **Sistema de pruebas avanzado**:
  - ✓ Pruebas unitarias
  - ✓ Pruebas de integración
  - ✓ Pruebas de GUI
  - ✓ Pruebas de manejo de errores
  - ✓ Pruebas de permisos

### Comparación con CLI
| Característica | CLI Original | S3 Manager App |
|----------------|--------------|----------------|
| Interfaz | Terminal | Gráfica moderna |
| Selección | Manual/scripting | Visual/intuitiva |
| Progreso | Texto básico | Barras animadas |
| Seguridad | Confirmación simple | Múltiples niveles |
| Logs | Terminal | Interfaz dedicada |
| Usabilidad | Técnica | Usuario final |

---

**¡Disfruta usando S3 Manager!** 🚀
