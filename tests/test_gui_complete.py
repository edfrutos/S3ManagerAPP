#!/usr/bin/env python3
"""
Pruebas exhaustivas de la interfaz gráfica de S3 Manager
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import sys
import os
import time
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer

from s3_manager_app import S3ManagerApp

class S3ManagerGUITester:
    """Clase para pruebas exhaustivas de la GUI"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = S3ManagerApp()
        self.results = []
        
    def run_all_tests(self):
        """Ejecuta todas las pruebas de GUI"""
        print("🧪 INICIANDO PRUEBAS EXHAUSTIVAS DE GUI")
        print("=" * 60)
        
        # Mostrar ventana
        self.window.show()
        
        # Programar pruebas secuencialmente
        QTimer.singleShot(1000, self.test_initial_state)
        QTimer.singleShot(2000, self.test_bucket_tab)
        QTimer.singleShot(3000, self.test_files_tab)
        QTimer.singleShot(4000, self.test_logs_tab)
        QTimer.singleShot(5000, self.test_menu_actions)
        QTimer.singleShot(6000, self.test_error_handling)
        QTimer.singleShot(7000, self.test_file_operations)
        QTimer.singleShot(8000, self.finish_tests)
        
        # Ejecutar loop de eventos
        return self.app.exec()
    
    def test_initial_state(self):
        """Prueba el estado inicial de la aplicación"""
        print("\n1️⃣ Probando estado inicial...")
        
        try:
            # Verificar elementos principales
            assert self.window.tab_widget is not None
            assert self.window.bucket_tab is not None
            assert self.window.files_tab is not None
            assert self.window.log_tab is not None
            
            # Verificar pestañas
            assert self.window.tab_widget.count() == 3
            assert self.window.tab_widget.tabText(0) == "📦 Buckets"
            assert self.window.tab_widget.tabText(1) == "📁 Archivos"
            assert self.window.tab_widget.tabText(2) == "📋 Logs"
            
            print("✅ Estado inicial correcto")
            self.results.append(("Estado inicial", True))
            
        except AssertionError as e:
            print(f"❌ Error en estado inicial: {e}")
            self.results.append(("Estado inicial", False))
    
    def test_bucket_tab(self):
        """Prueba la pestaña de buckets"""
        print("\n2️⃣ Probando pestaña de buckets...")
        
        try:
            # Cambiar a pestaña de buckets
            self.window.tab_widget.setCurrentIndex(0)
            
            # Verificar elementos
            bucket_tab = self.window.bucket_tab
            assert bucket_tab.bucket_list is not None
            assert bucket_tab.bucket_info is not None
            assert bucket_tab.permissions_btn is not None
            assert bucket_tab.files_btn is not None
            
            # Verificar estado inicial de botones
            assert not bucket_tab.permissions_btn.isEnabled()
            assert not bucket_tab.files_btn.isEnabled()
            
            print("✅ Pestaña de buckets correcta")
            self.results.append(("Pestaña buckets", True))
            
        except AssertionError as e:
            print(f"❌ Error en pestaña buckets: {e}")
            self.results.append(("Pestaña buckets", False))
    
    def test_files_tab(self):
        """Prueba la pestaña de archivos"""
        print("\n3️⃣ Probando pestaña de archivos...")
        
        try:
            # Cambiar a pestaña de archivos
            self.window.tab_widget.setCurrentIndex(1)
            
            # Verificar elementos
            files_tab = self.window.files_tab
            assert files_tab.files_table is not None
            assert files_tab.select_all_btn is not None
            assert files_tab.select_none_btn is not None
            assert files_tab.download_btn is not None
            assert files_tab.delete_btn is not None
            
            # Verificar tabla
            assert files_tab.files_table.columnCount() == 4
            headers = [files_tab.files_table.horizontalHeaderItem(i).text() 
                      for i in range(4)]
            assert headers == ["Seleccionar", "Nombre", "Tamaño (MB)", "Fecha"]
            
            print("✅ Pestaña de archivos correcta")
            self.results.append(("Pestaña archivos", True))
            
        except AssertionError as e:
            print(f"❌ Error en pestaña archivos: {e}")
            self.results.append(("Pestaña archivos", False))
    
    def test_logs_tab(self):
        """Prueba la pestaña de logs"""
        print("\n4️⃣ Probando pestaña de logs...")
        
        try:
            # Cambiar a pestaña de logs
            self.window.tab_widget.setCurrentIndex(2)
            
            # Verificar elementos
            log_tab = self.window.log_tab
            assert log_tab.log_text is not None
            
            # Probar funciones de log
            log_tab.add_log("Prueba de log info", "info")
            log_tab.add_log("Prueba de log error", "error")
            log_tab.add_log("Prueba de log warning", "warning")
            
            # Verificar contenido
            log_content = log_tab.log_text.toPlainText()
            assert "Prueba de log info" in log_content
            assert "Prueba de log error" in log_content
            assert "Prueba de log warning" in log_content
            
            print("✅ Pestaña de logs correcta")
            self.results.append(("Pestaña logs", True))
            
        except AssertionError as e:
            print(f"❌ Error en pestaña logs: {e}")
            self.results.append(("Pestaña logs", False))
    
    def test_menu_actions(self):
        """Prueba las acciones del menú"""
        print("\n5️⃣ Probando menú y acciones...")
        
        try:
            # Verificar menú
            menubar = self.window.menuBar()
            assert menubar is not None
            
            # Verificar menús principales
            menus = [menu.text() for menu in menubar.actions()]
            assert "Archivo" in menus
            assert "Ayuda" in menus
            
            # Probar acción "Acerca de"
            about_action = None
            for menu in menubar.actions():
                if menu.text() == "Ayuda":
                    about_action = menu.menu().actions()[0]
                    break
            
            assert about_action is not None
            assert about_action.text() == "Acerca de"
            
            print("✅ Menú y acciones correctos")
            self.results.append(("Menú y acciones", True))
            
        except AssertionError as e:
            print(f"❌ Error en menú y acciones: {e}")
            self.results.append(("Menú y acciones", False))
    
    def test_error_handling(self):
        """Prueba el manejo de errores en la GUI"""
        print("\n6️⃣ Probando manejo de errores...")
        
        try:
            # Simular error de credenciales
            self.window.worker.operation_completed.emit(False, "Error de credenciales")
            
            # Simular error de conexión
            self.window.worker.operation_completed.emit(False, "Error de conexión S3")
            
            # Verificar logs de error
            log_content = self.window.log_tab.log_text.toPlainText()
            assert "Error de credenciales" in log_content
            assert "Error de conexión S3" in log_content
            
            print("✅ Manejo de errores correcto")
            self.results.append(("Manejo de errores", True))
            
        except AssertionError as e:
            print(f"❌ Error en manejo de errores: {e}")
            self.results.append(("Manejo de errores", False))
    
    def test_file_operations(self):
        """Prueba operaciones con archivos"""
        print("\n7️⃣ Probando operaciones con archivos...")
        
        try:
            # Cambiar a pestaña de archivos
            self.window.tab_widget.setCurrentIndex(1)
            files_tab = self.window.files_tab
            
            # Verificar estado inicial (sin archivos cargados)
            assert not files_tab.download_btn.isEnabled()
            assert not files_tab.delete_btn.isEnabled()
            
            # Verificar que los botones de selección existen
            assert files_tab.select_all_btn is not None
            assert files_tab.select_none_btn is not None
            
            # Verificar que la tabla está vacía inicialmente
            assert files_tab.files_table.rowCount() == 0
            
            print("✅ Operaciones con archivos correctas")
            self.results.append(("Operaciones archivos", True))
            
        except AssertionError as e:
            print(f"❌ Error en operaciones con archivos: {e}")
            self.results.append(("Operaciones archivos", False))
    
    def finish_tests(self):
        """Finaliza las pruebas y muestra resultados"""
        print("\n📊 RESUMEN DE PRUEBAS GUI")
        print("=" * 60)
        
        passed = 0
        total = len(self.results)
        
        for test_name, result in self.results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"\n🎯 Tasa de éxito: {success_rate:.1f}% ({passed}/{total})")
        
        if success_rate == 100:
            print("\n🎉 ¡TODAS LAS PRUEBAS GUI PASARON!")
            print("✨ La interfaz gráfica está lista para uso")
        else:
            print("\n⚠️  Algunas pruebas fallaron")
            print("🔧 Revisa los errores antes de usar")
        
        # Cerrar aplicación
        self.window.close()
        self.app.quit()

def main():
    """Función principal"""
    tester = S3ManagerGUITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
