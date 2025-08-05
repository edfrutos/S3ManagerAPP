#!/bin/bash
# Script para activar el entorno virtual y configurar el PYTHONPATH
# para resolver problemas de importación en el IDE

echo "Activando entorno virtual para S3Manager..."

# Activar el entorno virtual
source venv310/bin/activate

# Configurar PYTHONPATH para incluir el directorio del proyecto
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verificar que keyring esté disponible
echo "Verificando instalación de keyring..."
python -c "import keyring; print('✓ keyring importado correctamente')" 2>/dev/null || {
    echo "✗ Error: keyring no se puede importar"
    echo "Instalando dependencias..."
    pip install -r requirements.txt
}

echo "Entorno virtual activado y configurado."
echo "Para usar en tu IDE, asegúrate de que el intérprete de Python apunte a:"
echo "$(pwd)/venv310/bin/python" 