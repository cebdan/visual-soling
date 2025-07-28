# Visual Solving - Advanced UI
# Современный интерфейс с поддержкой революционного синтаксиса переменных
# variable@solution и variable.solution

import sys
import re
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QTextEdit, QLabel, QPushButton, QDialog, QFormLayout, QLineEdit,
    QComboBox, QMessageBox, QCompleter, QFileDialog, QFrame, QGridLayout,
    QListWidget, QListWidgetItem, QTabWidget, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QStringListModel, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QPixmap, QIcon

from visual_solving_advanced import (
    HybridBoxSolution, solution_manager, HybridSolution
)
from variable_system import ExpressionParser

class FormulaHighlighter(QSyntaxHighlighter):
    """
    Подсветка синтаксиса для формул с новым синтаксисом
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Форматы для подсветки
        self.formats = {}
        
        # @ символы (оранжевый)
        self.formats['assignment'] = QTextCharFormat()
        self.formats['assignment'].setForeground(QColor("#e67e22"))  # Оранжевый
        self.formats['assignment'].setFontWeight(QFont.Weight.Bold)
        
        # . символы (синий)
        self.formats['reference'] = QTextCharFormat()
        self.formats['reference'].setForeground(QColor("#3498db"))  # Синий
        self.formats['reference'].setFontWeight(QFont.Weight.Bold)
        
        # Числа (зеленый)
        self.formats['number'] = QTextCharFormat()
        self.formats['number'].setForeground(QColor("#27ae60"))  # Зеленый
        
        # Функции (фиолетовый)
        self.formats['function'] = QTextCharFormat()
        self.formats['function'].setForeground(QColor("#9b59b6"))  # Фиолетовый
        self.formats['function'].setFontWeight(QFont.Weight.Bold)
        
        # Legacy синтаксис (серый)
        self.formats['legacy'] = QTextCharFormat()
        self.formats['legacy'].setForeground(QColor("#95a5a6"))  # Серый
        
    def highlightBlock(self, text: str):
        """Подсветка блока текста"""
        
        # @ символы для assignment
        for match in re.finditer(r'\w+@\w+', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['assignment'])
        
        # . символы для reference  
        for match in re.finditer(r'\w+\.\w+', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['reference'])
        
        # Legacy синтаксис #1.variable
        for match in re.finditer(r'#\d+\.\w+', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['legacy'])
        
        # Числа
        for match in re.finditer(r'\b\d+\.?\d*\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])
        
        # Математические функции
        functions = ['sqrt', 'sin', 'cos', 'tan', 'max', 'min', 'abs', 'pow', 'exp', 'log']
        for func in functions:
            pattern = f'\\b{func}\\b'
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['function'])

class VariableCompleter(QCompleter):
    """
    Автодополнение для переменных в новом синтаксисе
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.update_completions()
    
    def update_completions(self):
        """Обновление списка автодополнений"""
        completions = []
        
        # Добавляем переменные из всех решений
        for solution in solution_manager.get_all_solutions():
            for var_info in solution.get_all_variables_info():
                # Новый синтаксис
                completions.append(var_info['read_id'])  # variable.solution
                completions.append(var_info['write_id'])  # variable@solution
                
                # Legacy синтаксис
                if var_info.get('legacy_id'):
                    completions.append(var_info['legacy_id'])
                
                # Алиасы
                for alias in var_info['aliases']:
                    completions.append(alias)
        
        # Математические функции
        math_functions = [
            'sqrt(', 'sin(', 'cos(', 'tan(', 'max(', 'min(', 'abs(',
            'pow(', 'exp(', 'log(', 'log10(', 'ceil(', 'floor(', 'round('
        ]
        completions.extend(math_functions)
        
        # Обновляем модель
        model = QStringListModel(completions)
        self.setModel(model)

class GlobalVariableRegistryWindow(QDialog):
    """
    Окно глобального реестра переменных
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Variable Registry - All Variables")
        self.setGeometry(200, 200, 1000, 600)
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        header = QLabel("🌐 Global Variable Registry")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # Таблица переменных
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(8)
        self.variables_table.setHorizontalHeaderLabels([
            "Solution", "Variable", "Value", "Write ID", "Read ID", 
            "Legacy ID", "Type", "Formula/Dependencies"
        ])
        layout.addWidget(self.variables_table)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_data)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("✖️ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def refresh_data(self):
        """Обновление данных в таблице"""
        global_info = solution_manager.get_global_registry_info()
        
        self.variables_table.setRowCount(len(global_info))
        
        for row, var_info in enumerate(global_info):
            # Solution
            self.variables_table.setItem(row, 0, QTableWidgetItem(var_info['solution_name']))
            
            # Variable
            self.variables_table.setItem(row, 1, QTableWidgetItem(var_info['name']))
            
            # Value
            value_str = f"{var_info['value']:.2f}" if var_info['value'] is not None else "N/A"
            self.variables_table.setItem(row, 2, QTableWidgetItem(value_str))
            
            # Write ID
            self.variables_table.setItem(row, 3, QTableWidgetItem(var_info['write_id']))
            
            # Read ID
            self.variables_table.setItem(row, 4, QTableWidgetItem(var_info['read_id']))
            
            # Legacy ID
            legacy_id = var_info.get('legacy_id', 'N/A')
            self.variables_table.setItem(row, 5, QTableWidgetItem(str(legacy_id)))
            
            # Type
            self.variables_table.setItem(row, 6, QTableWidgetItem(var_info['type']))
            
            # Formula/Dependencies
            if var_info['is_formula']:
                formula_info = f"Formula: {var_info['raw_value']}"
                if var_info['dependencies']:
                    formula_info += f" | Deps: {', '.join(var_info['dependencies'])}"
            else:
                formula_info = "Direct value"
            
            self.variables_table.setItem(row, 7, QTableWidgetItem(formula_info))
        
        # Автоподстройка колонок
        self.variables_table.resizeColumnsToContents()
    
    def export_data(self):
        """Экспорт данных в файл"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Global Registry", "", 
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                global_info = solution_manager.get_global_registry_info()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    # Заголовок
                    f.write("Solution,Variable,Value,Write_ID,Read_ID,Legacy_ID,Type,Formula\n")
                    
                    # Данные
                    for var_info in global_info:
                        value_str = f"{var_info['value']:.2f}" if var_info['value'] is not None else "N/A"
                        legacy_id = var_info.get('legacy_id', 'N/A')
                        formula = var_info['raw_value'] if var_info['is_formula'] else "direct"
                        
                        f.write(f"{var_info['solution_name']},{var_info['name']},{value_str},"
                               f"{var_info['write_id']},{var_info['read_id']},{legacy_id},"
                               f"{var_info['type']},{formula}\n")
                
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

class VariableEditDialog(QDialog):
    """
    Диалог редактирования переменной
    """
    
    def __init__(self, solution: HybridSolution, var_name: str = None, parent=None):
        super().__init__(parent)
        self.solution = solution
        self.var_name = var_name
        self.is_edit = var_name is not None
        
        self.setWindowTitle("Edit Variable" if self.is_edit else "Create Variable")
        self.setGeometry(300, 300, 500, 300)
        self.setup_ui()
        
        if self.is_edit:
            self.load_variable_data()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title = "✏️ Edit Variable" if self.is_edit else "➕ Create Variable"
        header = QLabel(title)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # Форма
        form_layout = QFormLayout()
        
        # Имя переменной
        self.name_edit = QLineEdit()
        self.name_edit.setEnabled(not self.is_edit)  # Нельзя менять имя при редактировании
        form_layout.addRow("Variable Name:", self.name_edit)
        
        # Значение/формула
        self.value_edit = QTextEdit()
        self.value_edit.setMaximumHeight(100)
        
        # Подсветка синтаксиса
        self.highlighter = FormulaHighlighter(self.value_edit.document())
        
        # Автодополнение
        self.completer = VariableCompleter()
        self.value_edit.textChanged.connect(self._on_text_changed)
        
        form_layout.addRow("Value/Formula:", self.value_edit)
        
        # Тип переменной
        self.type_combo = QComboBox()
        self.type_combo.addItems(["controllable", "calculated", "alias"])
        form_layout.addRow("Type:", self.type_combo)
        
        # Алиасы
        self.alias_edit = QLineEdit()
        form_layout.addRow("Aliases (comma-separated):", self.alias_edit)
        
        layout.addLayout(form_layout)
        
        # Предварительный просмотр
        preview_group = QFrame()
        preview_group.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px;")
        preview_layout = QVBoxLayout()
        
        preview_label = QLabel("📋 Preview:")
        preview_label.setStyleSheet("font-weight: bold; color: #34495e;")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(80)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("background-color: #f8f9fa; color: #2c3e50;")
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("✅ OK")
        self.ok_button.clicked.connect(self.accept_changes)
        button_layout.addWidget(self.ok_button)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Обновление предварительного просмотра
        self.value_edit.textChanged.connect(self.update_preview)
        self.name_edit.textChanged.connect(self.update_preview)
    
    def _on_text_changed(self):
        """Обработка изменения текста для автодополнения"""
        # Простая реализация автодополнения
        cursor = self.value_edit.textCursor()
        cursor.select(cursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        
        if len(word) > 1:
            self.completer.setCompletionPrefix(word)
            if self.completer.completionCount() > 0:
                # Показываем автодополнение
                pass
    
    def load_variable_data(self):
        """Загрузка данных переменной для редактирования"""
        if self.var_name and self.var_name in self.solution.variables:
            var = self.solution.variables[self.var_name]
            
            self.name_edit.setText(self.var_name)
            self.value_edit.setText(str(var.value))
            
            # Тип
            type_index = self.type_combo.findText(var.variable_type.value)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
            
            # Алиасы
            aliases = [alias for alias, var_name in self.solution.aliases.items() 
                      if var_name == self.var_name]
            self.alias_edit.setText(", ".join(aliases))
    
    def update_preview(self):
        """Обновление предварительного просмотра"""
        name = self.name_edit.text().strip()
        value = self.value_edit.toPlainText().strip()
        
        if name and value:
            preview = f"Write: {name}@{self.solution.name} = {value}\n"
            preview += f"Read: {name}.{self.solution.name}\n"
            
            # Пытаемся вычислить значение
            try:
                if value.replace('.', '').replace('-', '').replace('+', '').replace('*', '').replace('/', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():
                    preview += f"Evaluated: {float(value):.2f}"
                else:
                    preview += f"Formula: {value}"
            except:
                preview += f"Formula: {value}"
            
            self.preview_text.setText(preview)
        else:
            self.preview_text.setText("Enter name and value to see preview")
    
    def accept_changes(self):
        """Применение изменений"""
        name = self.name_edit.text().strip()
        value = self.value_edit.toPlainText().strip()
        
        if not name or not value:
            QMessageBox.warning(self, "Warning", "Name and value are required")
            return
        
        # Валидация имени
        parser = ExpressionParser()
        if not parser.validate_name(name):
            QMessageBox.warning(self, "Warning", 
                              "Invalid name. Must start with letter/digit and contain only letters, digits, and underscore. Cannot contain @ or .")
            return
        
        try:
            # Установка переменной
            success = self.solution.set_variable(name, value)
            
            if success:
                # Установка алиасов
                aliases = [alias.strip() for alias in self.alias_edit.text().split(',') if alias.strip()]
                for alias in aliases:
                    if parser.validate_name(alias):
                        self.solution.set_alias(alias, name)
                
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to set variable")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting variable: {str(e)}")

class CreateBoxDialog(QDialog):
    """
    Диалог создания нового Box Solution
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Box Solution")
        self.setGeometry(300, 300, 400, 250)
        self.result_solution = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        header = QLabel("📦 Create New Box Solution")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(header)
        
        # Форма
        form_layout = QFormLayout()
        
        # Имя решения
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., panel, door, shelf")
        form_layout.addRow("Solution Name:", self.name_edit)
        
        # Размеры
        self.length_edit = QLineEdit()
        self.length_edit.setPlaceholderText("e.g., 600 or length.panel")
        form_layout.addRow("Length:", self.length_edit)
        
        self.width_edit = QLineEdit()
        self.width_edit.setPlaceholderText("e.g., 400 or width.panel - 20")
        form_layout.addRow("Width:", self.width_edit)
        
        self.height_edit = QLineEdit()
        self.height_edit.setPlaceholderText("e.g., 18 or height.panel")
        form_layout.addRow("Height:", self.height_edit)
        
        layout.addLayout(form_layout)
        
        # Примеры синтаксиса
        examples_group = QFrame()
        examples_group.setStyleSheet("border: 1px solid #3498db; border-radius: 5px; padding: 10px; background-color: #ecf0f1;")
        examples_layout = QVBoxLayout()
        
        examples_label = QLabel("💡 Syntax Examples:")
        examples_label.setStyleSheet("font-weight: bold; color: #2980b9;")
        examples_layout.addWidget(examples_label)
        
        examples_text = QLabel("""
• Direct values: 600, 400, 18
• Read from other solutions: length.panel, width.door
• Formulas: width.panel - 20, height.door + 5
• Math functions: max(length.panel, 800), sqrt(width.panel^2 + height.panel^2)
        """)
        examples_text.setStyleSheet("color: #34495e; font-size: 11px;")
        examples_layout.addWidget(examples_text)
        
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        create_button = QPushButton("✅ Create")
        create_button.clicked.connect(self.create_solution)
        button_layout.addWidget(create_button)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_solution(self):
        """Создание решения"""
        name = self.name_edit.text().strip()
        length = self.length_edit.text().strip()
        width = self.width_edit.text().strip()
        height = self.height_edit.text().strip()
        
        if not all([name, length, width, height]):
            QMessageBox.warning(self, "Warning", "All fields are required")
            return
        
        # Валидация имени
        parser = ExpressionParser()
        if not parser.validate_name(name):
            QMessageBox.warning(self, "Warning", 
                              "Invalid solution name. Must start with letter/digit and contain only letters, digits, and underscore.")
            return
        
        # Проверка уникальности имени
        if solution_manager.get_solution(name):
            QMessageBox.warning(self, "Warning", f"Solution '{name}' already exists")
            return
        
        try:
            # Создание решения
            self.result_solution = solution_manager.create_box_solution(name, length, width, height)
            QMessageBox.information(self, "Success", f"Solution '{name}' created successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create solution: {str(e)}")

class AdvancedMainWindow(QMainWindow):
    """
    Главное окно с поддержкой революционного синтаксиса
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Visual Solving - Revolutionary CAD System")
        self.setGeometry(100, 100, 1400, 800)
        
        # Таймер для автообновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_ui)
        self.update_timer.start(1000)  # Обновление каждую секунду
        
        self.setup_ui()
        self.setup_menu()
        
        # Создание демо данных
        self.create_demo_data()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout с разделителем
        main_layout = QHBoxLayout()
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - решения и переменные
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Правая панель - 3D viewer и свойства
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Пропорции
        main_splitter.setSizes([600, 800])
        
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)
        
        # Статусная строка
        self.statusBar().showMessage("🚀 Visual Solving ready - New syntax active")
    
    def create_left_panel(self) -> QWidget:
        """Создание левой панели"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Заголовок
        header = QLabel("📊 Solutions & Variables")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 5px;")
        left_layout.addWidget(header)
        
        # Вертикальный разделитель
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Дерево решений
        solutions_group = QWidget()
        solutions_layout = QVBoxLayout()
        
        solutions_label = QLabel("🗂️ Solutions")
        solutions_label.setStyleSheet("font-weight: bold; color: #34495e;")
        solutions_layout.addWidget(solutions_label)
        
        self.solution_tree = QTreeWidget()
        self.solution_tree.setHeaderLabel("Solutions (@solution syntax)")
        self.solution_tree.itemClicked.connect(self._on_solution_selected)
        solutions_layout.addWidget(self.solution_tree)
        
        solutions_group.setLayout(solutions_layout)
        left_splitter.addWidget(solutions_group)
        
        # Таблица переменных
        variables_group = QWidget()
        variables_layout = QVBoxLayout()
        
        variables_label = QLabel("📋 Variables")
        variables_label.setStyleSheet("font-weight: bold; color: #34495e;")
        variables_layout.addWidget(variables_label)
        
        self.variable_table = QTableWidget()
        self.variable_table.setColumnCount(6)
        self.variable_table.setHorizontalHeaderLabels([
            "Write ID", "Read ID", "Legacy ID", "Value", "Type", "Aliases"
        ])
        self.variable_table.doubleClicked.connect(self._on_variable_edit)
        variables_layout.addWidget(self.variable_table)
        
        variables_group.setLayout(variables_layout)
        left_splitter.addWidget(variables_group)
        
        left_splitter.setSizes([300, 400])
        left_layout.addWidget(left_splitter)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        add_solution_btn = QPushButton("➕ New Solution")
        add_solution_btn.clicked.connect(self.create_new_solution)
        buttons_layout.addWidget(add_solution_btn)
        
        add_variable_btn = QPushButton("➕ New Variable")
        add_variable_btn.clicked.connect(self.create_new_variable)
        buttons_layout.addWidget(add_variable_btn)
        
        left_layout.addLayout(buttons_layout)
        
        left_widget.setLayout(left_layout)
        return left_widget
    
    def create_right_panel(self) -> QWidget:
        """Создание правой панели"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Заголовок
        self.solution_header = QLabel("🎯 Visual Solving - Revolutionary Syntax")
        self.solution_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.solution_header.setStyleSheet("color: #2c3e50; font-size: 18px; font-weight: bold; padding: 10px;")
        right_layout.addWidget(self.solution_header)
        
        # Табы
        tabs = QTabWidget()
        
        # Таб 1: 3D Viewer
        viewer_tab = QWidget()
        viewer_layout = QVBoxLayout()
        
        # Placeholder для 3D
        self.viewer_3d = QWidget()
        self.viewer_3d.setMinimumSize(400, 300)
        self.viewer_3d.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555; border-radius: 5px;")
        
        viewer_placeholder_layout = QVBoxLayout()
        placeholder_label = QLabel("🎮 3D Viewer\n(Enhanced for new syntax)\n\nSelected solutions will be\nvisualized here")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #888; font-size: 14px;")
        viewer_placeholder_layout.addWidget(placeholder_label)
        self.viewer_3d.setLayout(viewer_placeholder_layout)
        
        viewer_layout.addWidget(self.viewer_3d)
        viewer_tab.setLayout(viewer_layout)
        tabs.addTab(viewer_tab, "🎮 3D Viewer")
        
        # Таб 2: Properties
        props_tab = QWidget()
        props_layout = QVBoxLayout()
        
        self.solution_info = QTextEdit()
        self.solution_info.setStyleSheet("background-color: #f8f9fa; color: #2c3e50; font-family: monospace; font-size: 11px;")
        self.solution_info.setReadOnly(True)
        props_layout.addWidget(self.solution_info)
        
        props_tab.setLayout(props_layout)
        tabs.addTab(props_tab, "📋 Properties")
        
        # Таб 3: Global Registry
        global_tab = QWidget()
        global_layout = QVBoxLayout()
        
        global_btn = QPushButton("🌐 Open Global Variable Registry")
        global_btn.clicked.connect(self.open_global_registry)
        global_layout.addWidget(global_btn)
        
        # Краткая сводка
        self.global_summary = QTextEdit()
        self.global_summary.setMaximumHeight(200)
        self.global_summary.setStyleSheet("background-color: #f8f9fa; color: #2c3e50; font-family: monospace; font-size: 10px;")
        self.global_summary.setReadOnly(True)
        global_layout.addWidget(self.global_summary)
        
        global_tab.setLayout(global_layout)
        tabs.addTab(global_tab, "🌐 Global")
        
        right_layout.addWidget(tabs)
        right_widget.setLayout(right_layout)
        
      