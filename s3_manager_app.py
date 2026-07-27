#!/usr/bin/env python3
"""
Aplicación de escritorio macOS para gestión de buckets S3
Autor: EDF Developer - 2025-06-19
Fecha: 2025
"""

import sys
import os
import threading
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QProgressBar, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QSplitter, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QMenuBar, QToolBar, QLineEdit, QDialog, QInputDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QAction

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Importar funciones del script original
from diagnose_s3_permissions import (
    check_aws_credentials, test_s3_connection, list_bucket_contents,
    check_bucket_permissions, check_bucket_configuration,
    download_selected_files, delete_selected_files, delete_bucket_and_contents,
    create_s3_bucket
)

# Importar gestor de credenciales
from aws_credentials_manager import AWSCredentialsManager

class S3Worker(QThread):
    """Worker thread para operaciones S3 que no bloqueen la UI"""
    
    # Señales para comunicación con la UI
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)
    bucket_list_ready = pyqtSignal(list)
    file_list_ready = pyqtSignal(list)
    log_message = pyqtSignal(str, str)  # mensaje, tipo (info, warning, error)
    
    def __init__(self):
        super().__init__()
        self.operation = None
        self.bucket_name = None
        self.selected_files = []
        self.local_path = None
        self.s3_client = None
        self.region = None
        
    def set_operation(self, operation, **kwargs):
        """Configura la operación a realizar"""
        self.operation = operation
        self.bucket_name = kwargs.get('bucket_name')
        self.selected_files = kwargs.get('selected_files', [])
        self.local_path = kwargs.get('local_path')
        self.region = kwargs.get('region')
        
    def run(self):
        """Ejecuta la operación en el hilo separado"""
        try:
            if self.operation == 'list_buckets':
                self._list_buckets()
            elif self.operation == 'list_files':
                self._list_files()
            elif self.operation == 'download_files':
                self._download_files()
            elif self.operation == 'delete_files':
                self._delete_files()
            elif self.operation == 'check_permissions':
                self._check_permissions()
            elif self.operation == 'delete_bucket':
                self._delete_bucket()
            elif self.operation == 'create_bucket':
                self._create_bucket()
                
        except Exception as e:
            self.log_message.emit(f"Error en operación: {str(e)}", "error")
            self.operation_completed.emit(False, str(e))
    
    def _list_buckets(self):
        """Lista todos los buckets disponibles"""
        try:
            self.s3_client, buckets = test_s3_connection()
            if self.s3_client:
                self.bucket_list_ready.emit(buckets)
                self.log_message.emit(f"Se encontraron {len(buckets)} buckets", "info")
            else:
                self.operation_completed.emit(False, "No se pudo conectar a S3")
        except Exception as e:
            self.operation_completed.emit(False, str(e))
    
    def _list_files(self):
        """Lista archivos en un bucket específico"""
        try:
            if not self.s3_client:
                self.s3_client = boto3.client('s3')
            
            objects = list_bucket_contents(self.s3_client, self.bucket_name)
            self.file_list_ready.emit(objects)
            self.log_message.emit(f"Se encontraron {len(objects)} archivos en {self.bucket_name}", "info")
            
        except Exception as e:
            self.operation_completed.emit(False, str(e))
    
    def _download_files(self):
        """Descarga archivos seleccionados"""
        try:
            if not self.s3_client:
                self.s3_client = boto3.client('s3')
            
            total_files = len(self.selected_files)
            for i, file_obj in enumerate(self.selected_files):
                # Actualizar progreso
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, f"Descargando: {file_obj['Key']}")
                
                # Crear ruta local
                local_file_path = os.path.join(self.local_path, file_obj['Key'])
                local_dir = os.path.dirname(local_file_path)
                if local_dir:
                    os.makedirs(local_dir, exist_ok=True)
                
                # Descargar archivo
                self.s3_client.download_file(self.bucket_name, file_obj['Key'], local_file_path)
                
            self.progress_updated.emit(100, "Descarga completada")
            self.operation_completed.emit(True, f"Se descargaron {total_files} archivos exitosamente")
            
        except Exception as e:
            self.operation_completed.emit(False, str(e))
    
    def _delete_files(self):
        """Elimina archivos seleccionados"""
        try:
            if not self.s3_client:
                self.s3_client = boto3.client('s3')
            
            total_files = len(self.selected_files)
            for i, file_obj in enumerate(self.selected_files):
                # Actualizar progreso
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, f"Eliminando: {file_obj['Key']}")
                
                # Eliminar archivo
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_obj['Key'])
                
            self.progress_updated.emit(100, "Eliminación completada")
            self.operation_completed.emit(True, f"Se eliminaron {total_files} archivos exitosamente")
            
        except Exception as e:
            self.operation_completed.emit(False, str(e))
    
    def _check_permissions(self):
        """Verifica permisos del bucket"""
        try:
            if not self.s3_client:
                self.s3_client = boto3.client('s3')
            
            # Obtener permisos y configuración
            permissions = check_bucket_permissions(self.s3_client, self.bucket_name)
            
            # Obtener región del bucket
            location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            region = location['LocationConstraint'] or 'us-east-1'
            
            # Crear mensaje detallado
            details = [
                "📊 Resultados de verificación:",
                f"🌎 Región: {region}",
                "\n🔐 Permisos:",
                f"{'✅' if permissions['read'] else '❌'} Lectura: {'OK' if permissions['read'] else 'Error'}",
                f"{'✅' if permissions['write'] else '❌'} Escritura: {'OK' if permissions['write'] else 'Error'}",
                f"{'✅' if permissions['delete'] else '❌'} Eliminación: {'OK' if permissions['delete'] else 'Error'}",
                f"{'✅' if permissions['list'] else '❌'} Listado: {'OK' if permissions['list'] else 'Error'}"
            ]
            
            # Verificar configuración adicional
            try:
                encryption = self.s3_client.get_bucket_encryption(Bucket=self.bucket_name)
                details.append("\n🔒 Encriptación: Habilitada")
            except ClientError:
                details.append("\n⚠️ Encriptación: No configurada")
            
            message = "\n".join(details)
            self.operation_completed.emit(True, message)
            
        except Exception as e:
            self.operation_completed.emit(False, str(e))

    def _delete_bucket(self):
        """Llama a la función de borrado de bucket y emite el resultado."""
        try:
            if not self.s3_client:
                self.s3_client = boto3.client('s3')
            
            success, message = delete_bucket_and_contents(
                self.s3_client,
                self.bucket_name
            )
            self.operation_completed.emit(success, message)
            
        except Exception as e:
            self.operation_completed.emit(False, str(e))

    def _create_bucket(self):
        """Crea un nuevo bucket."""
        try:
            self.log_message.emit(f"WORKER: Intentando crear bucket '{self.bucket_name}' en región '{self.region}'...", "info")
            if not self.s3_client:
                self.s3_client = boto3.client('s3')
            
            success, message = create_s3_bucket(
                self.bucket_name,
                self.region
            )
            self.operation_completed.emit(success, message)
            
        except Exception as e:
            self.log_message.emit(f"Error en _create_bucket: {str(e)}", "error")
            self.operation_completed.emit(False, str(e))

class CreateBucketDialog(QDialog):
    """Diálogo para crear un nuevo bucket."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nuevo Bucket S3")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Nombre del bucket
        layout.addWidget(QLabel("Nombre del nuevo bucket:"))
        self.bucket_name_input = QLineEdit()
        self.bucket_name_input.setPlaceholderText("ej: mi-bucket-unico-123")
        layout.addWidget(self.bucket_name_input)

        # Selección de región
        layout.addWidget(QLabel("Región de AWS:"))
        self.region_combo = QComboBox()
        # Lista de regiones comunes. Se puede expandir.
        regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'af-south-1', 'ap-east-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 
            'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1', 'eu-north-1',
            'eu-south-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'me-south-1', 'sa-east-1'
        ]
        self.region_combo.addItems(regions)
        layout.addWidget(self.region_combo)

        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_bucket_details(self):
        """Devuelve el nombre y la región del bucket."""
        return self.bucket_name_input.text().strip(), self.region_combo.currentText()

class BucketTab(QWidget):
    """Pestaña para gestión de buckets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.buckets = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título y botón de actualizar
        header_layout = QHBoxLayout()
        title = QLabel("📦 Gestión de Buckets S3")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_buckets)
        header_layout.addWidget(refresh_btn)

        create_btn = QPushButton("➕ Crear Bucket")
        create_btn.clicked.connect(self.open_create_bucket_dialog)
        header_layout.addWidget(create_btn)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Lista de buckets
        self.bucket_list = QListWidget()
        self.bucket_list.itemClicked.connect(self.on_bucket_selected)
        layout.addWidget(self.bucket_list)
        
        # Información del bucket seleccionado
        info_group = QGroupBox("Información del Bucket")
        info_layout = QVBoxLayout()
        self.bucket_info = QTextEdit()
        self.bucket_info.setMinimumHeight(200)
        self.bucket_info.setMaximumHeight(300)
        self.bucket_info.setReadOnly(True)
        self.bucket_info.setStyleSheet("""
            QTextEdit {
                font-family: Monaco, monospace;
                font-size: 12px;
                line-height: 1.5;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }
        """)
        info_layout.addWidget(self.bucket_info)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        self.permissions_btn = QPushButton("🔍 Verificar Permisos")
        self.permissions_btn.clicked.connect(self.check_permissions)
        self.permissions_btn.setEnabled(False)
        button_layout.addWidget(self.permissions_btn)
        
        self.files_btn = QPushButton("📁 Ver Archivos")
        self.files_btn.clicked.connect(self.view_files)
        self.files_btn.setEnabled(False)
        button_layout.addWidget(self.files_btn)
        
        # Botón para eliminar el bucket seleccionado
        self.delete_bucket_btn = QPushButton("Eliminar Bucket")
        self.delete_bucket_btn.setEnabled(False)
        self.delete_bucket_btn.setStyleSheet("color: red;")
        self.delete_bucket_btn.clicked.connect(self.confirm_delete_bucket)
        button_layout.addWidget(self.delete_bucket_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # No cargar buckets automáticamente, esperar a que la UI esté lista
    
    def refresh_buckets(self):
        """Actualiza la lista de buckets"""
        self.parent.start_operation('list_buckets')
    
    def update_bucket_list(self, buckets):
        """Actualiza la UI con la lista de buckets"""
        self.buckets = buckets
        self.bucket_list.clear()
        
        for bucket in buckets:
            item = QListWidgetItem(f"📦 {bucket['Name']}")
            item.setData(Qt.ItemDataRole.UserRole, bucket)
            self.bucket_list.addItem(item)
    
    def on_bucket_selected(self, item):
        """Maneja la selección de un bucket"""
        bucket = item.data(Qt.ItemDataRole.UserRole)
        
        # Mostrar información del bucket
        info_text = f"""
Nombre: {bucket['Name']}
Fecha de creación: {bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')}
Región: Detectando...
        """
        self.bucket_info.setText(info_text.strip())
        
        # Habilitar botones
        self.permissions_btn.setEnabled(True)
        self.files_btn.setEnabled(True)
        self.delete_bucket_btn.setEnabled(True)
        
        # Guardar bucket seleccionado
        self.parent.selected_bucket = bucket['Name']
    
    def check_permissions(self):
        """Verifica permisos del bucket seleccionado"""
        if hasattr(self.parent, 'selected_bucket'):
            # Deshabilitar botón mientras se verifica
            self.permissions_btn.setEnabled(False)
            self.permissions_btn.setText("🔄 Verificando...")
            
            # Iniciar verificación
            self.parent.start_operation('check_permissions', bucket_name=self.parent.selected_bucket)
            
            # Actualizar la información del bucket después de verificar permisos
            QTimer.singleShot(1000, self.update_bucket_info)
            
            # Restaurar botón después de 2 segundos
            QTimer.singleShot(2000, lambda: self.permissions_btn.setEnabled(True))
            QTimer.singleShot(2000, lambda: self.permissions_btn.setText("🔍 Verificar Permisos"))
            
    def update_bucket_info(self):
        """Actualiza la información del bucket con los resultados de la verificación"""
        if hasattr(self.parent, 'selected_bucket'):
            try:
                s3_client = boto3.client('s3')
                location = s3_client.get_bucket_location(Bucket=self.parent.selected_bucket)
                region = location['LocationConstraint'] or 'us-east-1'
                
                # Obtener permisos actuales
                permissions = check_bucket_permissions(s3_client, self.parent.selected_bucket)
                
                # Buscar el bucket en la lista
                for bucket in self.buckets:
                    if bucket['Name'] == self.parent.selected_bucket:
                        # Crear texto de información detallada
                        info_text = f"""
📦 INFORMACIÓN DEL BUCKET

Nombre: {bucket['Name']}
Fecha de creación: {bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')}
Región: {region}

🔐 PERMISOS:
{'✅' if permissions['read'] else '❌'} Lectura: {'OK' if permissions['read'] else 'Error'}
{'✅' if permissions['write'] else '❌'} Escritura: {'OK' if permissions['write'] else 'Error'}
{'✅' if permissions['delete'] else '❌'} Eliminación: {'OK' if permissions['delete'] else 'Error'}
{'✅' if permissions['list'] else '❌'} Listado: {'OK' if permissions['list'] else 'Error'}
"""
                        # Verificar encriptación
                        try:
                            s3_client.get_bucket_encryption(Bucket=self.parent.selected_bucket)
                            info_text += "\n🔒 Encriptación: Habilitada"
                        except ClientError:
                            info_text += "\n⚠️ Encriptación: No configurada"
                        
                        self.bucket_info.setText(info_text.strip())
                        break
                        
            except Exception as e:
                self.parent.log_tab.add_log(f"Error actualizando información: {str(e)}", "error")
    
    def view_files(self):
        """Cambia a la pestaña de archivos"""
        selected_items = self.bucket_list.selectedItems()
        if selected_items:
            self.parent.switch_to_files_tab()

    def confirm_delete_bucket(self):
        """Muestra un diálogo de confirmación muy seguro para eliminar un bucket."""
        if not hasattr(self.parent, 'selected_bucket') or not self.parent.selected_bucket:
            self.parent.log_tab.add_log("Intento de borrado sin un bucket seleccionado.", "warning")
            return

        bucket_name = self.parent.selected_bucket

        title = "⚠️ Confirmación de Borrado Irreversible"
        label = (f"Está a punto de eliminar el bucket <b>{bucket_name}</b> y todo su contenido.<br>"
                 f"Esta acción no se puede deshacer.<br><br>"
                 f"Para confirmar, por favor escriba <b>{bucket_name}</b> en el campo de abajo:")
        
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.EchoMode.Normal, "")
        
        if ok:
            if text.strip() == bucket_name:
                self.delete_bucket(bucket_name)
            else:
                QMessageBox.critical(self, "Error de Confirmación", 
                                     "El nombre del bucket no coincide. Borrado cancelado.")

    def delete_bucket(self, bucket_name):
        """Inicia el proceso de borrado del bucket en un worker thread."""
        self.parent.log_tab.add_log(f"Iniciando borrado del bucket {bucket_name}...", "info")
        self.parent.start_operation('delete_bucket', bucket_name=bucket_name)

    def open_create_bucket_dialog(self):
        """Abre el diálogo para crear un nuevo bucket."""
        dialog = CreateBucketDialog(self)
        if dialog.exec():
            bucket_name, region = dialog.get_bucket_details()
            if bucket_name:
                self.create_bucket(bucket_name, region)
            else:
                QMessageBox.warning(self, "Nombre Requerido", "El nombre del bucket no puede estar vacío.")

    def create_bucket(self, bucket_name, region):
        """Inicia la creación de un nuevo bucket."""
        self.parent.log_tab.add_log(f"Iniciando creación del bucket '{bucket_name}' en la región '{region}'...", "info")
        self.parent.start_operation('create_bucket', bucket_name=bucket_name, region=region)

class FilesTab(QWidget):
    """Pestaña para gestión de archivos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_bucket = None
        self.files = []
        self.selected_files = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header con información del bucket
        header_layout = QHBoxLayout()
        self.bucket_label = QLabel("📁 Selecciona un bucket desde la pestaña Buckets")
        self.bucket_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.bucket_label)
        
        self.refresh_files_btn = QPushButton("🔄 Actualizar")
        self.refresh_files_btn.clicked.connect(self.refresh_files)
        self.refresh_files_btn.setEnabled(False)
        header_layout.addWidget(self.refresh_files_btn)
        
        layout.addLayout(header_layout)
        
        # Tabla de archivos
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["Seleccionar", "Nombre", "Tamaño (MB)", "Fecha"])
        
        # Configurar tabla
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.files_table)
        
        # Controles de selección
        selection_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("✅ Seleccionar Todo")
        self.select_all_btn.clicked.connect(self.select_all_files)
        selection_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = QPushButton("❌ Deseleccionar Todo")
        self.select_none_btn.clicked.connect(self.select_no_files)
        selection_layout.addWidget(self.select_none_btn)
        
        selection_layout.addStretch()
        
        self.selected_count_label = QLabel("0 archivos seleccionados")
        selection_layout.addWidget(self.selected_count_label)
        
        layout.addLayout(selection_layout)
        
        # Botones de acción
        action_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("⬇️ Descargar Seleccionados")
        self.download_btn.clicked.connect(self.download_selected)
        self.download_btn.setEnabled(False)
        action_layout.addWidget(self.download_btn)
        
        self.delete_btn = QPushButton("🗑️ Eliminar Seleccionados")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        action_layout.addWidget(self.delete_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
    
    def load_bucket_files(self, bucket_name):
        """Carga archivos de un bucket específico"""
        self.current_bucket = bucket_name
        self.bucket_label.setText(f"📁 Archivos en: {bucket_name}")
        self.refresh_files_btn.setEnabled(True)
        self.refresh_files()
    
    def refresh_files(self):
        """Actualiza la lista de archivos"""
        if self.current_bucket:
            self.parent.start_operation('list_files', bucket_name=self.current_bucket)
    
    def update_files_table(self, files):
        """Actualiza la tabla con la lista de archivos"""
        self.files = files
        self.files_table.setRowCount(len(files))
        
        for row, file_obj in enumerate(files):
            # Checkbox para selección
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.update_selection)
            self.files_table.setCellWidget(row, 0, checkbox)
            
            # Nombre del archivo
            name_item = QTableWidgetItem(file_obj['Key'])
            self.files_table.setItem(row, 1, name_item)
            
            # Tamaño en MB
            size_mb = file_obj['Size'] / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.2f}")
            self.files_table.setItem(row, 2, size_item)
            
            # Fecha de modificación
            date_str = file_obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
            date_item = QTableWidgetItem(date_str)
            self.files_table.setItem(row, 3, date_item)
        
        self.update_selection()
    
    def select_all_files(self):
        """Selecciona todos los archivos"""
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            checkbox.setChecked(True)
    
    def select_no_files(self):
        """Deselecciona todos los archivos"""
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            checkbox.setChecked(False)
    
    def update_selection(self):
        """Actualiza la lista de archivos seleccionados"""
        self.selected_files = []
        selected_count = 0
        
        for row in range(self.files_table.rowCount()):
            checkbox = self.files_table.cellWidget(row, 0)
            if checkbox.isChecked():
                self.selected_files.append(self.files[row])
                selected_count += 1
        
        # Actualizar UI
        self.selected_count_label.setText(f"{selected_count} archivos seleccionados")
        self.download_btn.setEnabled(selected_count > 0)
        self.delete_btn.setEnabled(selected_count > 0)
    
    def download_selected(self):
        """Descarga archivos seleccionados"""
        if not self.selected_files:
            return
        
        # Seleccionar directorio de descarga
        download_dir = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar directorio de descarga",
            str(Path.home() / "Downloads")
        )
        
        if download_dir:
            self.parent.start_operation(
                'download_files',
                bucket_name=self.current_bucket,
                selected_files=self.selected_files,
                local_path=download_dir
            )
    
    def delete_selected(self):
        """Elimina archivos seleccionados"""
        if not self.selected_files:
            return
        
        # Confirmación de eliminación
        reply = QMessageBox.question(
            self,
            "⚠️ Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar {len(self.selected_files)} archivo(s)?\n\n"
            "⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent.start_operation(
                'delete_files',
                bucket_name=self.current_bucket,
                selected_files=self.selected_files
            )

class LogTab(QWidget):
    """Pestaña para logs y diagnósticos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("📋 Logs y Diagnósticos")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Área de logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monaco", 11))
        layout.addWidget(self.log_text)
        
        # Botones
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Limpiar Logs")
        clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("💾 Exportar Logs")
        export_btn.clicked.connect(self.export_logs)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Log inicial
        self.add_log("Aplicación iniciada", "info")
    
    def add_log(self, message, log_type="info"):
        """Añade un mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if log_type == "error":
            prefix = "❌"
            color = "red"
        elif log_type == "warning":
            prefix = "⚠️"
            color = "orange"
        elif log_type == "success":
            prefix = "✅"
            color = "green"
        else:
            prefix = "ℹ️"
            color = "blue"
        
        log_entry = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color};">{prefix} {message}</span><br>'
        self.log_text.insertHtml(log_entry)
        
        # Scroll al final
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_logs(self):
        """Limpia todos los logs"""
        self.log_text.clear()
        self.add_log("Logs limpiados", "info")
    
    def export_logs(self):
        """Exporta logs a un archivo"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Logs",
            f"s3_manager_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.add_log(f"Logs exportados a: {file_path}", "success")
            except Exception as e:
                self.add_log(f"Error exportando logs: {str(e)}", "error")

class S3ManagerApp(QMainWindow):
    """Aplicación principal de gestión S3"""
    
    def __init__(self):
        super().__init__()
        self.selected_bucket = None
        self.worker = S3Worker()
        self.init_ui()
        self.setup_worker()
        
        # Cargar credenciales guardadas
        self.load_saved_credentials()
        
        # Verificar si es la primera ejecución
        self.check_first_run()
        
        # No verificar credenciales automáticamente para evitar cuelgues
        self.log_tab.add_log("Aplicación iniciada. Use el botón 'Actualizar' para cargar buckets.", "info")
        self.status_bar.showMessage("Listo - Use 'Actualizar' para conectar")
        
    def init_ui(self):
        self.setWindowTitle("S3 Manager - Gestión de Buckets AWS")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central con pestañas
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Crear pestañas
        self.bucket_tab = BucketTab(self)
        self.files_tab = FilesTab(self)
        self.log_tab = LogTab(self)
        
        # Añadir pestañas
        self.tab_widget.addTab(self.bucket_tab, "📦 Buckets")
        self.tab_widget.addTab(self.files_tab, "📁 Archivos")
        self.tab_widget.addTab(self.log_tab, "📋 Logs")
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Crear menú
        self.create_menu()
        
        # Aplicar estilo macOS
        self.apply_macos_style()
    
    def create_menu(self):
        """Crea el menú de la aplicación"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('Archivo')
        
        refresh_action = QAction('🔄 Actualizar', self)
        refresh_action.triggered.connect(self.refresh_all)
        file_menu.addAction(refresh_action)
        
        # Añadir opción de configuración
        config_action = QAction('⚙️ Configuración AWS', self)
        config_action.triggered.connect(self.show_config_dialog)
        file_menu.addAction(config_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('Salir', self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('Ayuda')
        
        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def apply_macos_style(self):
        """Aplica estilo similar a macOS"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QListWidget {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background-color: white;
            }
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def setup_worker(self):
        """Configura las conexiones del worker thread"""
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.operation_completed.connect(self.operation_completed)
        self.worker.bucket_list_ready.connect(self.bucket_tab.update_bucket_list)
        self.worker.file_list_ready.connect(self.files_tab.update_files_table)
        self.worker.log_message.connect(self.log_tab.add_log)

    def switch_to_files_tab(self):
        """Cambia a la pestaña de archivos y carga su contenido."""
        if self.selected_bucket:
            self.tab_widget.setCurrentIndex(1)  # 1 es el índice de la pestaña de archivos
            self.files_tab.load_bucket_files(self.selected_bucket)
    
    def load_saved_credentials(self):
        """Carga las credenciales guardadas al inicio"""
        try:
            access_key, secret_key = AWSCredentialsManager.load_credentials()
            if access_key and secret_key:
                self.log_tab.add_log("Credenciales AWS cargadas desde almacenamiento seguro", "success")
                self.status_bar.showMessage("✅ Credenciales cargadas")
            else:
                self.log_tab.add_log("No se encontraron credenciales guardadas", "warning")
                self.status_bar.showMessage("⚠️ Sin credenciales")
        except Exception as e:
            self.log_tab.add_log(f"Error cargando credenciales: {str(e)}", "error")
            self.status_bar.showMessage("❌ Error cargando credenciales")

    def check_credentials(self):
        """Verifica las credenciales AWS al inicio"""
        try:
            if check_aws_credentials():
                self.log_tab.add_log("Credenciales AWS verificadas correctamente", "success")
                self.status_bar.showMessage("✅ Conectado a AWS")
                # Cargar buckets después de verificar credenciales
                QTimer.singleShot(500, self.bucket_tab.refresh_buckets)
            else:
                self.log_tab.add_log("Credenciales AWS no encontradas", "error")
                self.status_bar.showMessage("❌ Sin credenciales AWS")
        except Exception as e:
            self.log_tab.add_log(f"Error verificando credenciales: {str(e)}", "error")
            self.status_bar.showMessage("❌ Error de credenciales")
    
    def start_operation(self, operation, **kwargs):
        """Inicia una operación en el worker thread"""
        if self.worker.isRunning():
            self.log_tab.add_log("Operación en curso, espera a que termine", "warning")
            return
        
        self.worker.set_operation(operation, **kwargs)
        self.worker.start()
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f"Ejecutando: {operation}")
    
    def update_progress(self, value, message):
        """Actualiza la barra de progreso"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)
        self.log_tab.add_log(message, "info")
    
    def operation_completed(self, success, message):
        """Maneja la finalización de operaciones de forma centralizada."""
        self.progress_bar.setVisible(False)

        if success:
            self.status_bar.showMessage("✅ Operación completada")

            # Caso 1: Borrado de bucket exitoso
            if "El bucket" in message and "han sido eliminados" in message:
                self.log_tab.add_log(message, "success")
                QMessageBox.information(self, "Éxito", message)
                self.bucket_tab.refresh_buckets()
            
            # Caso 2: Borrado de archivos exitoso
            elif "eliminaron" in message and self.files_tab.current_bucket:
                self.log_tab.add_log(message, "success")
                self.files_tab.refresh_files()

            # Caso 3: Verificación de permisos
            elif "Resultados de verificación" in message:
                self.log_tab.add_log("Verificación de permisos completada:", "success")
                for line in message.split('\n'):
                    if line.strip():
                        self.log_tab.add_log(f"  {line}", "info")
            
            # Otros casos de éxito
            else:
                self.log_tab.add_log(message, "success")
        else:
            # Manejo de errores
            self.log_tab.add_log(f"Error: {message}", "error")
            self.status_bar.showMessage("❌ Error en operación")
            QMessageBox.critical(self, "Error en la Operación", message)
    
    def refresh_all(self):
        """Actualiza toda la información"""
        self.bucket_tab.refresh_buckets()
        if self.files_tab.current_bucket:
            self.files_tab.refresh_files()
    
    def check_first_run(self):
        """Verifica si es la primera ejecución y muestra configuración si es necesario"""
        # Verificar si existe archivo de primera ejecución
        first_run_file = Path(__file__).parent / "first_run"
        app_first_run = Path.home() / ".s3manager_first_run"
        
        # Verificar si hay credenciales usando el gestor
        has_credentials = AWSCredentialsManager.has_credentials()
        
        if first_run_file.exists() or not app_first_run.exists() or not has_credentials:
            # Es primera ejecución o no hay credenciales
            QTimer.singleShot(500, self.show_first_run_dialog)
            
            # Eliminar archivo de primera ejecución si existe
            if first_run_file.exists():
                try:
                    first_run_file.unlink()
                except:
                    pass
            
            # Crear archivo de marca para futuras ejecuciones
            try:
                app_first_run.touch()
            except:
                pass
    
    def show_first_run_dialog(self):
        """Muestra el diálogo de primera ejecución"""
        reply = QMessageBox.question(
            self,
            "🎉 ¡Bienvenido a S3Manager!",
            """¡Gracias por usar S3Manager!

Para comenzar, necesitas configurar tus credenciales de AWS S3.

¿Te gustaría configurarlas ahora?

Nota: Puedes cambiarlas más tarde desde el menú Archivo → Configuración AWS""",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_config_dialog()
    
    def show_config_dialog(self):
        """Muestra el diálogo de configuración AWS"""
        dialog = AWSConfigDialog(self)
        if dialog.exec():
            self.check_credentials()
            self.refresh_all()
    
    def show_about(self):
        """Muestra información sobre la aplicación"""
        QMessageBox.about(
            self,
            "Acerca de S3 Manager",
            """
            <h3>S3 Manager</h3>
            <p>Aplicación de gestión de buckets AWS S3</p>
            <p><b>Versión:</b> 1.0.0</p>
            <p><b>Autor:</b> EDF Developer</p>
            <p><b>Fecha:</b> 2025</p>
            
            <h4>Funcionalidades:</h4>
            <ul>
                <li>✅ Listado de buckets S3</li>
                <li>✅ Verificación de permisos</li>
                <li>✅ Descarga selectiva de archivos</li>
                <li>✅ Eliminación selectiva de archivos</li>
                <li>✅ Interfaz gráfica moderna</li>
                <li>✅ Logs detallados</li>
            </ul>
            """
        )

class AWSConfigDialog(QDialog):
    """Diálogo para configurar credenciales AWS"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz del diálogo"""
        self.setWindowTitle("Configuración AWS S3")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("CONFIGURACIÓN DE AWS S3")
        title_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Subtítulo
        subtitle_label = QLabel("Credenciales y configuración de Amazon S3")
        subtitle_label.setStyleSheet("color: gray;")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(10)
        
        # Cargar credenciales existentes
        existing_access_key, existing_secret_key = AWSCredentialsManager.load_credentials()
        
        # Campo Access Key ID
        access_key_layout = QHBoxLayout()
        access_key_label = QLabel("AWS_ACCESS_KEY_ID:")
        self.access_key_input = QLineEdit()
        self.access_key_input.setText(existing_access_key or '')
        access_key_layout.addWidget(access_key_label)
        access_key_layout.addWidget(self.access_key_input)
        layout.addLayout(access_key_layout)
        
        # Campo Secret Access Key
        secret_key_layout = QHBoxLayout()
        secret_key_label = QLabel("AWS_SECRET_ACCESS_KEY:")
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_key_input.setText(existing_secret_key or '')
        secret_key_layout.addWidget(secret_key_label)
        secret_key_layout.addWidget(self.secret_key_input)
        layout.addLayout(secret_key_layout)
        
        layout.addSpacing(20)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.save_config)
        save_btn.setDefault(True)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_config(self):
        """Guarda la configuración AWS"""
        access_key = self.access_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()
        
        if not access_key or not secret_key:
            QMessageBox.warning(
                self,
                "Campos Requeridos",
                "Por favor, complete ambos campos de credenciales AWS."
            )
            return
        
        # Guardar usando el gestor de credenciales
        success, error_message = AWSCredentialsManager.save_credentials(access_key, secret_key)
        if success:
            QMessageBox.information(
                self,
                "Configuración Guardada (V2)",
                "¡Éxito! Las credenciales AWS se han guardado correctamente en la nueva versión."
            )
            self.accept()
        else:
            detailed_error = f"No se pudieron guardar las credenciales.\n\nRazón: {error_message}"
            QMessageBox.critical(
                self,
                "Error al Guardar",
                detailed_error
            )

def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("S3 Manager")
    app.setApplicationVersion("1.1.1")
    app.setOrganizationName("Sistema de Catálogo de Tablas")
    
    # Crear y mostrar ventana principal
    window = S3ManagerApp()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
