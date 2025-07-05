#!/bin/bash
# Script de lanzamiento para S3Manager
# Ubicación: /Users/edefrutos/S3Manager

cd "/Users/edefrutos/S3Manager"

if [ -f "build/S3Manager.app/Contents/MacOS/S3Manager" ]; then
    echo "🚀 Lanzando S3Manager desde aplicación construida..."
    open "build/S3Manager.app"
else
    echo "🐍 Lanzando S3Manager desde código fuente..."
    python3 s3_manager_app.py
fi
