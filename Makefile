# S3Manager Makefile

.PHONY: help install build dmg release mas test clean

help:
	@echo "S3Manager - Comandos disponibles:"
	@echo "  install  - Instalar dependencias"
	@echo "  build    - Construir aplicación"
	@echo "  dmg      - Crear instalador DMG (sin firmar)"
	@echo "  release  - Construir, firmar, crear DMG y notarizar"
	@echo "  mas      - Variante Mac App Store (sandbox) en S3Manager-mas.pkg"
	@echo "  test     - Ejecutar pruebas"
	@echo "  clean    - Limpiar archivos generados"

install:
	pip3 install -r requirements.txt

build:
	python3 build_macos_app.py

dmg: build
	python3 create_dmg_installer.py --skip-build

# Firma Developer ID + notarización (requiere CODESIGN_IDENTITY y NOTARY_PROFILE)
release:
	python3 sign_and_notarize.py

# Mac App Store (requiere MAS_APP_IDENTITY, MAS_INSTALLER_IDENTITY y
# MAS_PROFILE; opcional BUILD_NUMBER para CFBundleVersion)
mas:
	python3 build_mas.py $(if $(BUILD_NUMBER),--build-number $(BUILD_NUMBER))

test:
	cd tests && python3 test_s3_functionality.py
	cd tests && python3 test_gui_complete.py
	cd tests && python3 test_native_app.py

clean:
	rm -rf build/ dist/ __pycache__/ *.spec *.pkg
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
