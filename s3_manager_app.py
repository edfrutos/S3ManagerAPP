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
from app_version import __version__

# Regiones AWS habituales, usadas tanto al crear buckets como al
# configurar la región por defecto de un perfil.
AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'af-south-1', 'ap-east-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-south-1',
    'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1', 'eu-north-1',
    'eu-south-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'me-south-1', 'sa-east-1'
]

class S3Worker(QThread):
    """Worker thread para operaciones S3 que no bloqueen la UI"""
    
    # Señales para comunicación con la UI
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)
    bucket_list_ready = pyqtSignal(list)
    file_list_ready = pyqtSignal(list)
    log_message = pyqtSignal(str, str)  # mensaje, tipo (info, warning, error)
    # bucket, {'region': str, 'permissions': dict, 'encryption': bool}
    permissions_ready = pyqtSignal(str, dict)
    
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
                # operation_completed oculta la barra de progreso y
                # registra el mensaje en el log.
                self.operation_completed.emit(
                    True, f"Se encontraron {len(buckets)} buckets"
                )
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
            self.operation_completed.emit(
                True,
                f"Se encontraron {len(objects)} archivos en {self.bucket_name}",
            )
            
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
        """Verifica permisos, región y cifrado del bucket (una sola vez)."""
        try:
            if not self.s3_client:
                self.s3_client = boto3.client('s3')

            permissions = check_bucket_permissions(
                self.s3_client, self.bucket_name
            )

            location = self.s3_client.get_bucket_location(
                Bucket=self.bucket_name
            )
            region = location['LocationConstraint'] or 'us-east-1'

            try:
                self.s3_client.get_bucket_encryption(Bucket=self.bucket_name)
                encryption = True
            except ClientError:
                encryption = False

            # Resultado estructurado para el panel de información del bucket
            self.permissions_ready.emit(
                self.bucket_name,
                {
                    'region': region,
                    'permissions': permissions,
                    'encryption': encryption,
                },
            )

            def mark(ok):
                return '✅' if ok else '❌'

            def status(ok):
                return 'OK' if ok else 'Error'

            # "Resultados de verificación" lo usa operation_completed de la UI
            details = [
                "📊 Resultados de verificación:",
                f"🌎 Región: {region}",
                "\n🔐 Permisos:",
                f"{mark(permissions['read'])} Lectura: {status(permissions['read'])}",
                f"{mark(permissions['write'])} Escritura: {status(permissions['write'])}",
                f"{mark(permissions['delete'])} Eliminación: {status(permissions['delete'])}",
                f"{mark(permissions['list'])} Listado: {status(permissions['list'])}",
                "\n🔒 Encriptación: Habilitada"
                if encryption
                else "\n⚠️ Encriptación: No configurada",
            ]
            self.operation_completed.emit(True, "\n".join(details))

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
        self.region_combo.addItems(AWS_REGIONS)
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
        """Lanza la verificación de permisos en el worker. El panel se
        rellena en show_permissions() cuando llega el resultado."""
        bucket_name = getattr(self.parent, 'selected_bucket', None)
        if not bucket_name:
            return
        if self.parent.worker.isRunning():
            self.parent.log_tab.add_log(
                "Operación en curso, espera a que termine", "warning"
            )
            return

        self.permissions_btn.setEnabled(False)
        self.permissions_btn.setText("🔄 Verificando...")
        self.parent.start_operation('check_permissions', bucket_name=bucket_name)

    def reset_permissions_button(self):
        """Restaura el botón tras terminar la verificación (éxito o error)."""
        if self.permissions_btn.text().startswith("🔄"):
            self.permissions_btn.setText("🔍 Verificar Permisos")
            self.permissions_btn.setEnabled(
                bool(getattr(self.parent, 'selected_bucket', None))
            )

    def show_permissions(self, bucket_name, info):
        """Muestra en el panel el resultado que envía el worker."""
        # Si el usuario cambió de bucket mientras se verificaba, no pisar
        if bucket_name != getattr(self.parent, 'selected_bucket', None):
            return
        bucket = next(
            (b for b in self.buckets if b['Name'] == bucket_name), None
        )
        if bucket is None:
            return

        permissions = info['permissions']

        def line(key, label):
            ok = permissions[key]
            return f"{'✅' if ok else '❌'} {label}: {'OK' if ok else 'Error'}"

        info_text = f"""
📦 INFORMACIÓN DEL BUCKET

Nombre: {bucket['Name']}
Fecha de creación: {bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')}
Región: {info['region']}

🔐 PERMISOS:
{line('read', 'Lectura')}
{line('write', 'Escritura')}
{line('delete', 'Eliminación')}
{line('list', 'Listado')}
"""
        if info['encryption']:
            info_text += "\n🔒 Encriptación: Habilitada"
        else:
            info_text += "\n⚠️ Encriptación: No configurada"

        self.bucket_info.setText(info_text.strip())

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

        # Si hay contraseña maestra activa, pedirla antes de tocar
        # cualquier credencial.
        self.ensure_unlocked()

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

        # Barra de herramientas: selector de perfil AWS activo
        self.create_profile_toolbar()

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

        # Añadir opción de gestión de perfiles AWS
        config_action = QAction('⚙️ Gestionar Perfiles AWS...', self)
        config_action.triggered.connect(self.show_profiles_dialog)
        file_menu.addAction(config_action)

        master_password_action = QAction('🔒 Contraseña Maestra...', self)
        master_password_action.triggered.connect(self.manage_master_password)
        file_menu.addAction(master_password_action)

        file_menu.addSeparator()

        quit_action = QAction('Salir', self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Menú Ayuda
        help_menu = menubar.addMenu('Ayuda')

        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_profile_toolbar(self):
        """Crea la barra con el selector de perfil AWS activo."""
        toolbar = self.addToolBar("Perfil AWS")
        toolbar.setMovable(False)
        toolbar.addWidget(QLabel(" Perfil AWS activo: "))

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(160)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        toolbar.addWidget(self.profile_combo)

        manage_profiles_action = QAction("⚙️ Gestionar...", self)
        manage_profiles_action.triggered.connect(self.show_profiles_dialog)
        toolbar.addAction(manage_profiles_action)

    def refresh_profile_combo(self):
        """Sincroniza el desplegable de perfiles con lo guardado en disco."""
        profiles = AWSCredentialsManager.list_profiles()
        active = AWSCredentialsManager.get_active_profile()

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(profiles)
        if active in profiles:
            self.profile_combo.setCurrentText(active)
        self.profile_combo.blockSignals(False)

    def on_profile_changed(self, profile_name):
        """El usuario ha elegido otro perfil en el desplegable: lo activa."""
        if not profile_name:
            return
        success, error_message = AWSCredentialsManager.activate_profile(profile_name)
        if success:
            self.log_tab.add_log(f"Perfil AWS activo: {profile_name}", "success")
            self.status_bar.showMessage(f"✅ Perfil activo: {profile_name}")
            self.selected_bucket = None
            self.bucket_tab.refresh_buckets()
        else:
            self.log_tab.add_log(f"Error activando el perfil '{profile_name}': {error_message}", "error")
            self.status_bar.showMessage("❌ Error de perfil AWS")
    
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
        self.worker.permissions_ready.connect(self.bucket_tab.show_permissions)

    def switch_to_files_tab(self):
        """Cambia a la pestaña de archivos y carga su contenido."""
        if self.selected_bucket:
            self.tab_widget.setCurrentIndex(1)  # 1 es el índice de la pestaña de archivos
            self.files_tab.load_bucket_files(self.selected_bucket)
    
    def load_saved_credentials(self):
        """Carga y activa las credenciales del perfil AWS activo al inicio"""
        try:
            self.refresh_profile_combo()
            active_profile = AWSCredentialsManager.get_active_profile()
            if AWSCredentialsManager.has_credentials(active_profile):
                AWSCredentialsManager.activate_profile(active_profile)
                self.log_tab.add_log(
                    f"Credenciales AWS cargadas (perfil: {active_profile})", "success"
                )
                self.status_bar.showMessage(f"✅ Credenciales cargadas ({active_profile})")
            elif AWSCredentialsManager.is_master_password_enabled() and not AWSCredentialsManager.is_unlocked():
                self.log_tab.add_log(
                    "Credenciales bloqueadas por la contraseña maestra", "warning"
                )
                self.status_bar.showMessage("🔒 Bloqueado")
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
        self.bucket_tab.reset_permissions_button()

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
    
    def closeEvent(self, event):
        """Espera a que termine la operación S3 en curso antes de cerrar,
        para no destruir el QThread mientras sigue ejecutándose."""
        if self.worker.isRunning():
            self.status_bar.showMessage(
                "Esperando a que termine la operación en curso..."
            )
            self.worker.wait()
        event.accept()

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
            self.show_profiles_dialog()

    def show_profiles_dialog(self):
        """Muestra el diálogo de gestión de perfiles AWS"""
        self.ensure_unlocked()
        if AWSCredentialsManager.is_master_password_enabled() and not AWSCredentialsManager.is_unlocked():
            return  # el usuario canceló el desbloqueo

        dialog = AWSProfilesDialog(self)
        dialog.exec()
        # Se refresca siempre: el usuario puede haber creado, editado o
        # eliminado perfiles aunque el perfil activo no haya cambiado.
        self.refresh_profile_combo()
        self.check_credentials()
        self.refresh_all()

    def ensure_unlocked(self):
        """Si hay contraseña maestra activa, la pide hasta que se
        introduce correctamente o el usuario cancela."""
        if not AWSCredentialsManager.is_master_password_enabled():
            return
        while not AWSCredentialsManager.is_unlocked():
            password, ok = QInputDialog.getText(
                self, "Contraseña Maestra",
                "S3Manager está protegido con contraseña maestra.\n"
                "Introdúcela para desbloquear las credenciales AWS:",
                QLineEdit.EchoMode.Password
            )
            if not ok:
                self.log_tab.add_log(
                    "S3Manager sigue bloqueado. Desbloquéalo desde "
                    "Archivo → Contraseña Maestra...", "warning"
                )
                self.status_bar.showMessage("🔒 Bloqueado")
                return
            success, error_message = AWSCredentialsManager.unlock(password)
            if not success:
                QMessageBox.critical(self, "Contraseña Incorrecta", error_message)

    def manage_master_password(self):
        """Activa, desactiva o desbloquea la protección con contraseña maestra."""
        if AWSCredentialsManager.is_master_password_enabled():
            if not AWSCredentialsManager.is_unlocked():
                self.ensure_unlocked()
                if not AWSCredentialsManager.is_unlocked():
                    return

            reply = QMessageBox.question(
                self, "Contraseña Maestra Activa",
                "La protección con contraseña maestra ya está activada.\n\n"
                "¿Quieres desactivarla? Las credenciales seguirán protegidas "
                "por el keyring del sistema, pero sin esta capa adicional.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            password, ok = QInputDialog.getText(
                self, "Confirmar Contraseña Maestra",
                "Introduce la contraseña maestra actual para desactivarla:",
                QLineEdit.EchoMode.Password
            )
            if not ok or not password:
                return

            success, error_message = AWSCredentialsManager.disable_master_password(password)
            if success:
                self.log_tab.add_log("Contraseña maestra desactivada", "success")
                QMessageBox.information(self, "Desactivada", "La contraseña maestra se ha desactivado.")
            else:
                QMessageBox.critical(self, "Error", error_message)
        else:
            QMessageBox.information(
                self, "Activar Contraseña Maestra",
                "Vas a añadir una capa extra de cifrado a las claves secretas "
                "guardadas.\n\nSe te pedirá esta contraseña cada vez que abras "
                "S3Manager. Si la olvidas, no hay forma de recuperarla: tendrás "
                "que volver a introducir tus credenciales AWS manualmente."
            )
            password, ok = QInputDialog.getText(
                self, "Nueva Contraseña Maestra", "Elige una contraseña maestra:",
                QLineEdit.EchoMode.Password
            )
            if not ok or not password:
                return
            confirm, ok = QInputDialog.getText(
                self, "Confirmar Contraseña Maestra", "Repite la contraseña maestra:",
                QLineEdit.EchoMode.Password
            )
            if not ok or confirm != password:
                QMessageBox.warning(self, "Contraseñas no Coinciden", "No se ha activado la protección.")
                return

            success, error_message = AWSCredentialsManager.setup_master_password(password)
            if success:
                self.log_tab.add_log("Contraseña maestra activada", "success")
                QMessageBox.information(
                    self, "Activada",
                    "La contraseña maestra se ha activado y las credenciales "
                    "guardadas ya están protegidas."
                )
            else:
                QMessageBox.critical(self, "Error", error_message)

    def show_about(self):
        """Muestra información sobre la aplicación"""
        QMessageBox.about(
            self,
            "Acerca de S3 Manager",
            f"""
            <h3>S3 Manager</h3>
            <p>Aplicación de gestión de buckets AWS S3</p>
            <p><b>Versión:</b> {__version__}</p>
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
                <li>✅ Perfiles AWS múltiples y contraseña maestra</li>
            </ul>
            """
        )

class AWSProfilesDialog(QDialog):
    """Diálogo para gestionar (crear/editar/eliminar) perfiles de
    credenciales AWS. Cada perfil tiene su propia access key, secret key
    y región por defecto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Perfiles AWS")
        self.setMinimumSize(580, 380)
        self.current_profile = None
        self.init_ui()
        self.refresh_profile_list(select=AWSCredentialsManager.get_active_profile())

    def init_ui(self):
        """Inicializa la interfaz del diálogo"""
        layout = QHBoxLayout()

        # --- Columna izquierda: lista de perfiles ---
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Perfiles guardados:"))

        self.profiles_list = QListWidget()
        self.profiles_list.itemClicked.connect(self.on_profile_item_clicked)
        left_layout.addWidget(self.profiles_list)

        list_buttons_layout = QHBoxLayout()
        new_btn = QPushButton("➕ Nuevo")
        new_btn.clicked.connect(self.start_new_profile)
        list_buttons_layout.addWidget(new_btn)

        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.clicked.connect(self.delete_selected_profile)
        list_buttons_layout.addWidget(delete_btn)
        left_layout.addLayout(list_buttons_layout)

        io_buttons_layout = QHBoxLayout()
        export_btn = QPushButton("📤 Exportar...")
        export_btn.clicked.connect(self.export_profiles)
        io_buttons_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 Importar...")
        import_btn.clicked.connect(self.import_profiles)
        io_buttons_layout.addWidget(import_btn)
        left_layout.addLayout(io_buttons_layout)

        layout.addLayout(left_layout, 1)

        # --- Columna derecha: formulario del perfil seleccionado ---
        right_layout = QVBoxLayout()

        title_label = QLabel("CONFIGURACIÓN DEL PERFIL")
        title_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        right_layout.addWidget(title_label)

        right_layout.addWidget(QLabel("Nombre del perfil:"))
        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText("ej: default, trabajo, personal...")
        right_layout.addWidget(self.profile_name_input)

        right_layout.addWidget(QLabel("AWS_ACCESS_KEY_ID:"))
        self.access_key_input = QLineEdit()
        right_layout.addWidget(self.access_key_input)

        right_layout.addWidget(QLabel("AWS_SECRET_ACCESS_KEY:"))
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        right_layout.addWidget(self.secret_key_input)

        right_layout.addWidget(QLabel("Región por defecto:"))
        self.region_combo = QComboBox()
        self.region_combo.setEditable(True)
        self.region_combo.addItems(AWS_REGIONS)
        right_layout.addWidget(self.region_combo)

        right_layout.addStretch()

        button_layout = QHBoxLayout()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        save_btn = QPushButton("💾 Guardar Perfil")
        save_btn.clicked.connect(self.save_profile)
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

        right_layout.addLayout(button_layout)

        layout.addLayout(right_layout, 2)
        self.setLayout(layout)

    def refresh_profile_list(self, select=None):
        """Reconstruye la lista de perfiles, marcando el activo con ⭐."""
        self.profiles_list.clear()
        active = AWSCredentialsManager.get_active_profile()
        target = select if select is not None else self.current_profile

        for name in AWSCredentialsManager.list_profiles():
            label = f"⭐ {name}" if name == active else name
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.profiles_list.addItem(item)
            if name == target:
                self.profiles_list.setCurrentItem(item)

        if target:
            self.load_profile_into_form(target)
        elif not AWSCredentialsManager.list_profiles():
            self.start_new_profile()

    def on_profile_item_clicked(self, item):
        self.load_profile_into_form(item.data(Qt.ItemDataRole.UserRole))

    def load_profile_into_form(self, name):
        """Rellena el formulario con los datos de `name`. Si el perfil
        todavía no tiene credenciales guardadas, se trata como uno nuevo
        (nombre editable)."""
        access_key, secret_key, region = AWSCredentialsManager.load_credentials(name)
        exists = bool(access_key and secret_key)
        self.current_profile = name if exists else None

        self.profile_name_input.setText(name)
        self.profile_name_input.setEnabled(not exists)
        self.access_key_input.setText(access_key or '')
        self.secret_key_input.setText(secret_key or '')
        self.region_combo.setCurrentText(region or AWS_REGIONS[0])

    def start_new_profile(self):
        """Limpia el formulario para dar de alta un perfil nuevo."""
        self.current_profile = None
        self.profiles_list.clearSelection()
        self.profile_name_input.clear()
        self.profile_name_input.setEnabled(True)
        self.access_key_input.clear()
        self.secret_key_input.clear()
        self.region_combo.setCurrentIndex(0)
        self.profile_name_input.setFocus()

    def save_profile(self):
        """Guarda el perfil que hay actualmente en el formulario."""
        name = self.profile_name_input.text().strip()
        access_key = self.access_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()
        region = self.region_combo.currentText().strip()

        if not name or not access_key or not secret_key:
            QMessageBox.warning(
                self,
                "Campos Requeridos",
                "Indica un nombre de perfil y ambas credenciales AWS."
            )
            return

        success, error_message = AWSCredentialsManager.save_credentials(
            access_key, secret_key, region, profile=name
        )
        if success:
            self.refresh_profile_list(select=name)
            QMessageBox.information(
                self,
                "Perfil Guardado",
                f"El perfil '{name}' se ha guardado correctamente."
            )
        else:
            QMessageBox.critical(
                self,
                "Error al Guardar",
                f"No se pudo guardar el perfil.\n\nRazón: {error_message}"
            )

    def delete_selected_profile(self):
        """Elimina el perfil actualmente cargado en el formulario."""
        if not self.current_profile:
            QMessageBox.warning(
                self,
                "Selecciona un Perfil",
                "Elige un perfil de la lista para eliminarlo."
            )
            return

        reply = QMessageBox.question(
            self,
            "Eliminar Perfil",
            f"¿Seguro que quieres eliminar el perfil '{self.current_profile}'?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            AWSCredentialsManager.delete_profile(self.current_profile)
            self.current_profile = None
            self.refresh_profile_list()

    def export_profiles(self):
        """Exporta todos los perfiles guardados a un archivo cifrado."""
        if not AWSCredentialsManager.list_profiles():
            QMessageBox.warning(self, "Nada que Exportar", "No hay perfiles guardados todavía.")
            return

        password, ok = QInputDialog.getText(
            self, "Contraseña de Exportación",
            "Elige una contraseña para cifrar el archivo exportado.\n"
            "La necesitarás para importarlo de nuevo:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not password:
            return

        confirm, ok = QInputDialog.getText(
            self, "Confirmar Contraseña", "Repite la contraseña:",
            QLineEdit.EchoMode.Password
        )
        if not ok or confirm != password:
            QMessageBox.warning(self, "Contraseñas no Coinciden", "La exportación se ha cancelado.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Perfiles AWS", "s3manager_perfiles.s3mcfg",
            "Configuración S3Manager (*.s3mcfg)"
        )
        if not file_path:
            return

        try:
            blob = AWSCredentialsManager.export_profiles(password)
            with open(file_path, 'wb') as f:
                f.write(blob)
            QMessageBox.information(
                self, "Exportación Completada",
                f"Perfiles exportados y cifrados en:\n{file_path}\n\n"
                "Guarda la contraseña en un lugar seguro: sin ella no podrás "
                "recuperar este archivo."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", str(e))

    def import_profiles(self):
        """Importa perfiles desde un archivo previamente exportado."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Perfiles AWS", "",
            "Configuración S3Manager (*.s3mcfg);;Todos los archivos (*)"
        )
        if not file_path:
            return

        password, ok = QInputDialog.getText(
            self, "Contraseña de Importación",
            "Introduce la contraseña usada al exportar este archivo:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not password:
            return

        existing = set(AWSCredentialsManager.list_profiles())
        overwrite = True
        if existing:
            reply = QMessageBox.question(
                self, "Perfiles Existentes",
                "Si el archivo importado contiene perfiles con el mismo nombre "
                "que perfiles ya guardados, ¿quieres sobrescribirlos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            overwrite = reply == QMessageBox.StandardButton.Yes

        try:
            with open(file_path, 'rb') as f:
                blob = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error al Leer el Archivo", str(e))
            return

        success, message = AWSCredentialsManager.import_profiles(blob, password, overwrite)
        if success:
            self.refresh_profile_list()
            QMessageBox.information(self, "Importación Completada", message)
        else:
            QMessageBox.critical(self, "Error al Importar", message)

def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar aplicación
    app.setApplicationName("S3 Manager")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Sistema de Catálogo de Tablas")
    
    # Crear y mostrar ventana principal
    window = S3ManagerApp()
    window.show()
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
