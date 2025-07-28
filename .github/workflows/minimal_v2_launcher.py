# Minimal Visual Solving V2 Launcher
# Минимальный запускатель для тестирования системы V2

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

def test_v2_imports():
    """Тестирование импортов V2 системы"""
    try:
        from variable_system_v2 import ExpressionParser, V2Solution, demo_new_syntax
        print("✅ variable_system_v2 импортирован успешно")
        return True, "variable_system_v2"
    except ImportError as e:
        print(f"❌ Ошибка импорта variable_system_v2: {e}")
        return False, str(e)

def test_advanced_v2_imports():
    """Тестирование импортов advanced V2"""
    try:
        from visual_solving_advanced_v2 import HybridBoxSolution, v2_solution_manager
        print("✅ visual_solving_advanced_v2 импортирован успешно")
        return True, "visual_solving_advanced_v2"
    except ImportError as e:
        print(f"❌ Ошибка импорта visual_solving_advanced_v2: {e}")
        return False, str(e)

class MinimalV2Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Solving V2 - Minimal Launcher")
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_ui()
        self.test_system()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QTextEdit()
        title.setHtml("""
        <h1 style='color: #2c3e50;'>🚀 Visual Solving V2 - System Test</h1>
        <p style='color: #7f8c8d;'>Минимальный запускатель для проверки системы V2</p>
        """)
        title.setMaximumHeight(100)
        title.setReadOnly(True)
        layout.addWidget(title)
        
        # Информационная панель
        self.info_panel = QTextEdit()
        self.info_panel.setFont(QFont("Courier", 10))
        layout.addWidget(self.info_panel)
        
        # Кнопки тестирования
        btn_test_core = QPushButton("🔧 Test Core V2 System")
        btn_test_core.clicked.connect(self.test_core_system)
        layout.addWidget(btn_test_core)
        
        btn_test_demo = QPushButton("🎯 Run V2 Demo")
        btn_test_demo.clicked.connect(self.run_v2_demo)
        layout.addWidget(btn_test_demo)
        
        btn_test_ui = QPushButton("🖥️ Test V2 UI")
        btn_test_ui.clicked.connect(self.test_v2_ui)
        layout.addWidget(btn_test_ui)
        
        central_widget.setLayout(layout)
    
    def test_system(self):
        """Начальное тестирование системы"""
        info = "=== ТЕСТИРОВАНИЕ СИСТЕМЫ V2 ===\n\n"
        
        # Тест импортов
        info += "1. Тестирование импортов:\n"
        
        success1, msg1 = test_v2_imports()
        info += f"   variable_system_v2: {'✅' if success1 else '❌'} {msg1}\n"
        
        success2, msg2 = test_advanced_v2_imports()
        info += f"   visual_solving_advanced_v2: {'✅' if success2 else '❌'} {msg2}\n"
        
        # Тест PyQt6
        info += f"\n2. PyQt6 система: ✅ Работает корректно\n"
        
        # Файлы в директории
        info += f"\n3. Файлы в директории:\n"
        files = [
            "variable_system_v2.py",
            "visual_solving_advanced_v2.py", 
            "visual_solving_ui_advanced_v2.py",
            "run_advanced_demo_v2.py"
        ]
        
        for file in files:
            exists = os.path.exists(file)
            info += f"   {file}: {'✅' if exists else '❌'}\n"
        
        info += f"\n4. Статус системы: {'🟢 ГОТОВА К РАБОТЕ' if success1 and success2 else '🔴 ТРЕБУЕТ НАСТРОЙКИ'}\n"
        
        self.info_panel.setText(info)
    
    def test_core_system(self):
        """Тестирование ядра V2 системы"""
        try:
            from variable_system_v2 import demo_new_syntax
            
            # Перехватываем вывод
            import io
            from contextlib import redirect_stdout
            
            captured_output = io.StringIO()
            with redirect_stdout(captured_output):
                demo_new_syntax()
            
            output = captured_output.getvalue()
            
            result_text = "=== ТЕСТ ЯДРА V2 СИСТЕМЫ ===\n\n"
            result_text += "✅ Ядро работает корректно!\n\n"
            result_text += "Результат демонстрации:\n"
            result_text += "-" * 40 + "\n"
            result_text += output
            
            self.info_panel.setText(result_text)
            
        except Exception as e:
            error_text = f"❌ Ошибка тестирования ядра:\n{str(e)}"
            self.info_panel.setText(error_text)
            QMessageBox.critical(self, "Ошибка", f"Ошибка тестирования ядра V2:\n{str(e)}")
    
    def run_v2_demo(self):
        """Запуск демонстрации V2"""
        try:
            from visual_solving_advanced_v2 import demo_hybrid_system
            
            # Перехватываем вывод
            import io
            from contextlib import redirect_stdout
            
            captured_output = io.StringIO()
            with redirect_stdout(captured_output):
                demo_hybrid_system()
            
            output = captured_output.getvalue()
            
            result_text = "=== ДЕМОНСТРАЦИЯ ГИБРИДНОЙ СИСТЕМЫ V2 ===\n\n"
            result_text += "✅ Демонстрация выполнена успешно!\n\n"
            result_text += "Результат:\n"
            result_text += "-" * 40 + "\n"
            result_text += output
            
            self.info_panel.setText(result_text)
            
        except Exception as e:
            error_text = f"❌ Ошибка запуска демонстрации:\n{str(e)}"
            self.info_panel.setText(error_text)
            QMessageBox.critical(self, "Ошибка", f"Ошибка демонстрации V2:\n{str(e)}")
    
    def test_v2_ui(self):
        """Тестирование UI V2"""
        try:
            from visual_solving_ui_advanced_v2 import V2AdvancedMainWindow
            
            self.ui_window = V2AdvancedMainWindow()
            self.ui_window.show()
            
            QMessageBox.information(self, "Успех", "✅ UI V2 запущен успешно!\nОкно интерфейса должно появиться.")
            
        except Exception as e:
            error_text = f"❌ Ошибка запуска UI V2:\n{str(e)}"
            self.info_panel.setText(error_text)
            QMessageBox.critical(self, "Ошибка", f"Ошибка UI V2:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MinimalV2Window()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    print("🚀 Запуск минимального тестера Visual Solving V2...")
    main()
