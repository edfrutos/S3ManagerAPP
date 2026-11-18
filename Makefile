# S3Manager Makefile

# Usa el Python de venv310 si existe (aunque no esté activado), para no
# construir con un python3 del sistema sin PySide6. Se puede forzar con
# `make build PYTHON=...`.
PYTHON ?= $(if $(wildcard $(CURDIR)/venv310/bin/python),$(CURDIR)/venv310/bin/python,python3)

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
	$(PYTHON) -m pip install -r requirements.txt

build:
	$(PYTHON) build_macos_app.py

dmg: build
	$(PYTHON) create_dmg_installer.py --skip-build

# Firma Developer ID + notarización (requiere CODESIGN_IDENTITY y NOTARY_PROFILE)
release:
	$(PYTHON) sign_and_notarize.py

# Mac App Store (requiere MAS_APP_IDENTITY, MAS_INSTALLER_IDENTITY y
# MAS_PROFILE; opcional BUILD_NUMBER para CFBundleVersion)
mas:
	$(PYTHON) build_mas.py $(if $(BUILD_NUMBER),--build-number $(BUILD_NUMBER))

test:
	cd tests && $(PYTHON) test_s3_functionality.py
	cd tests && $(PYTHON) test_gui_complete.py
	cd tests && $(PYTHON) test_native_app.py

clean:
	rm -rf build/ dist/ __pycache__/ *.spec *.pkg
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
