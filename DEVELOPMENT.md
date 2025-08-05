# Configuración del Entorno de Desarrollo - S3Manager

## Resolución del Error de Importación de `keyring`

### Problema
El error "No se ha podido resolver la importación 'keyring'" indica que el IDE no está reconociendo el entorno virtual correctamente.

### Solución

#### 1. Activar el Entorno Virtual
```bash
# Ejecutar el script de activación
./activate_env.sh

# O activar manualmente
source venv310/bin/activate
```

#### 2. Configurar el IDE

**Para VS Code:**
- El archivo `.vscode/settings.json` ya está configurado
- Asegúrate de que VS Code use el intérprete correcto:
  - `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac)
  - Buscar "Python: Select Interpreter"
  - Seleccionar: `./venv310/bin/python`

**Para otros IDEs:**
- Configurar el intérprete de Python para que apunte a: `./venv310/bin/python`
- Asegurarse de que el PYTHONPATH incluya: `./venv310/lib/python3.10/site-packages`

#### 3. Verificar la Instalación
```bash
# Verificar que keyring esté disponible
python -c "import keyring; print('keyring disponible')"

# Verificar que AWSCredentialsManager funcione
python -c "from aws_credentials_manager import AWSCredentialsManager; print('AWSCredentialsManager disponible')"
```

### Dependencias Instaladas
- `keyring>=25.0.0` - Para almacenamiento seguro de credenciales
- `PySide6>=6.5.0` - Para la interfaz gráfica
- `boto3>=1.26.0` - Para interacción con AWS S3
- `botocore>=1.29.0` - Dependencia de boto3
- `pyinstaller>=5.0.0` - Para crear ejecutables
- `psutil>=5.9.0` - Para monitoreo del sistema

### Estructura del Proyecto
```
S3Manager/
├── venv310/                    # Entorno virtual
├── aws_credentials_manager.py  # Gestor de credenciales AWS
├── s3_manager_app.py          # Aplicación principal
├── requirements.txt           # Dependencias
├── activate_env.sh           # Script de activación
└── .vscode/settings.json     # Configuración del IDE
```

### Comandos Útiles
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python s3_manager_app.py

# Ejecutar tests
python -m pytest tests/

# Crear ejecutable
pyinstaller --onefile s3_manager_app.py
``` 