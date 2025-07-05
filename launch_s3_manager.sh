#!/bin/bash
# Script de lanzamiento para S3 Manager
# Autor: Sistema de Catálogo de Tablas

echo "🚀 Iniciando S3 Manager..."

# Directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activar entorno virtual si existe
if [ -d "$DIR/../../venv310" ]; then
    source "$DIR/../../venv310/bin/activate"
    echo "✅ Entorno virtual activado"
fi

# Verificar dependencias
python3 -c "import PyQt6, boto3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencias faltantes. Instalando..."
    pip install PyQt6 boto3
fi

# Ejecutar aplicación
cd "$DIR"
python3 s3_manager_app.py

echo "👋 S3 Manager cerrado"
