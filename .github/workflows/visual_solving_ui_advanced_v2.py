# Visual Solving UI Advanced V2 - UI с поддержкой новой системы переменных
# PyQt6 implementation with variable@solution and variable.solution support
# ИСПРАВЛЕННЫЕ ИМПОРТЫ PyQt6

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTableWidget, 
                            QTableWidgetItem, QSplitter, QMenuBar, QFileDialog, 
                            QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, 
                            QComboBox, QPushButton, QLabel, QTextEdit, QCheckBox,
                            QListWidget, QMessageBox, QHeaderView, QTabWidget,
                            QGroupBox, QGridLayout, QScrollArea, QSpinBox, QPlainTextEdit,
                            QCompleter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QStringListModel  # ← ИСПРАВЛЕНО: QStringListModel из QtCore
from PyQt6.QtGui import QAction, QFont, QColor, QTextCharFormat, QTextCursor, QSyntaxHighlighter
import json
import traceback
import re

# Импорт новой системы V2
try:
    from variable_system_v2 import (
        ExpressionParser, V2FormulaEvaluator, V2Variable, V2Solution,
        ExpressionType
    )
    from visual_solving_advanced_v2 import (
        HybridSolution, HybridBoxSolution as BoxSolution, HybridEdgeBandingSolution as EdgeBandingSolution, 
        Part3DSpace, HybridVariable, VariableType, v2_solution_manager,
        V2GlobalVariableRegistry, v2_dependency_tracker
    )
    CORE_V2_AVAILABLE = True
except ImportError as e:
    print(f"Ошибка импорта V2 ядра: {e}")
    CORE_V2_AVAILABLE = False

# =============================================================================
# Подсветка синтаксиса для новой системы V2
# =============================================================================

class V2FormulaHighlighter(QSyntaxHighlighter):
    """Подсветка синтаксиса для формул V2 (variable@solution и variable.solution)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Форматы для разных элементов
        self.formats = {}
        
        # Запись переменных (variable@solution)
        self.formats['variable_write'] = QTextCharFormat()
        self.formats['variable_write'].setForeground(QColor("#cc6600"))
        self.formats['variable_write'].setFontWeight(QFont.Weight.Bold)
        
        # Чтение переменных (variable.solution)
        self.formats['variable_read'] = QTextCharFormat()
        self.formats['variable_read'].setForeground(QColor("#0066cc"))
        self.formats['variable_read'].setFontWeight(QFont.Weight.Bold)
        
        # Числа
        self.formats['number'] = QTextCharFormat()
        self.formats['number'].setForeground(QColor("#009900"))
        
        # Операторы
        self.formats['operator'] = QTextCharFormat()
        self.formats['operator'].setForeground(QColor("#cc0066"))
        self.formats['operator'].setFontWeight(QFont.Weight.Bold)
        
        # Функции
        self.formats['function'] = QTextCharFormat()
        self.formats['function'].setForeground(QColor("#9900cc"))
        self.formats['function'].setFontWeight(QFont.Weight.Bold)
        
        # @ символ
        self.formats['at_symbol'] = QTextCharFormat()
        self.formats['at_symbol'].setForeground(QColor("#ff6600"))
        self.formats['at_symbol'].setFontWeight(QFont.Weight.Bold)
        
        # Символ точки для чтения
        self.formats['dot_symbol'] = QTextCharFormat()
        self.formats['dot_symbol'].setForeground(QColor("#0099cc"))
        self.formats['dot_symbol'].setFontWeight(QFont.Weight.Bold)
    
    def highlightBlock(self, text):
        # Запись переменных: variable@solution
        write_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)(@)([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(write_pattern, text):
            # Переменная
            self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['variable_write'])
            # @ символ
            self.setFormat(match.start(2), match.end(2) - match.start(2), self.formats['at_symbol'])
            # Solution
            self.setFormat(match.start(3), match.end(3) - match.start(3), self.formats['variable_write'])
        
        # Чтение переменных: variable.solution
        read_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)(\.)([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.finditer(read_pattern, text):
            # Переменная
            self.setFormat(match.start(1), match.end(1) - match.start(1), self.formats['variable_read'])
            # . символ
            self.setFormat(match.start(2), match.end(2) - match.start(2), self.formats['dot_symbol'])
            # Solution
            self.setFormat(match.start(3), match.end(3) - match.start(3), self.formats['variable_read'])
        
        # Числа
        number_pattern = r'\b\d+(\.\d+)?\b'
        for match in re.finditer(number_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])
        
        # Операторы
        operator_pattern = r'[+\-*/^()=]'
        for match in re.finditer(operator_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['operator'])
        
        # Функции
        function_pattern = r'\b(sin|cos|tan|sqrt|abs|min|max|round)\b'
        for match in re.finditer(function_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['function'])

# =============================================================================
# Автодополнение для новой системы V2
# =============================================================================

class V2VariableCompleter(QCompleter):
    """Автодополнение для переменных V2"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.update_completions()
    
    def update_completions(self):
        """Обновить список автодополнения"""
        if not CORE_V2_AVAILABLE:
            return
        
        completions = []
        
        # Получаем все solutions
        all_solutions = v2_solution_manager.get_all_solutions()
        
        for solution_name, solution in all_solutions.items():
            for var_name in solution.variables.keys():
                # Добавляем варианты для записи
                completions.append(f"{var_name}@{solution_name}")
                
                # Добавляем варианты для чтения
                completions.append(f"{var_name}.{solution_name}")
        
        # Добавляем функции
        functions = ['sin', 'cos', 'tan', 'sqrt', 'abs', 'min', 'max', 'round']
        completions.extend(functions)
        
        # Устанавливаем модель
        model = QStringListModel(completions)
        self.setModel(model)

# =============================================================================
# Окно глобального реестра переменных V2
# =============================================================================

class V2GlobalVariableRegistryWindow(QMainWindow):
    """Окно глобального реестра всех переменных V2"""
    
    variable_updated = pyqtSignal(str)  # Сигнал об обновлении переменной
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Variable Registry V2 - New Syntax")
        self.setGeometry(200, 200, 1400, 900)
        
        self._setup_ui()
        self._refresh_data()
        
        # Таймер для автообновления
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(2000)  # Обновление каждые 2 секунды
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Панель поиска
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search V2:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by variable@solution, variable.solution, aliases...")
        self.search_input.textChanged.connect(self._filter_variables)
        search_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_data)
        search_layout.addWidget(refresh_btn)
        
        layout.addLayout(search_layout)
        
        # Информация о синтаксисе
        syntax_info = QLabel("💡 New V2 Syntax: variable@solution=value (write), variable.solution (read), L=600 (alias)")
        syntax_info.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(syntax_info)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка 1: Все переменные V2
        self._setup_variables_v2_tab()
        
        # Вкладка 2: Граф зависимостей V2
        self._setup_dependencies_v2_tab()
        
        # Вкладка 3: Статистика V2
        self._setup_statistics_v2_tab()
        
        # Вкладка 4: Тестирование выражений V2
        self._setup_expression_test_tab()
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
        # Меню
        self._setup_menu()
    
    def _setup_variables_v2_tab(self):
        """Настройка вкладки с переменными V2"""
        variables_widget = QWidget()
        layout = QVBoxLayout()
        
        # Таблица переменных
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(10)
        self.variables_table.setHorizontalHeaderLabels([
            "Solution", "Write ID (V2)", "Read ID (V2)", "Legacy ID", "Name", 
            "Value/Formula", "Type", "Aliases", "Dependencies", "Dependents"
        ])
        
        # Настройка размеров колонок
        header = self.variables_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Solution
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Write ID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Read ID
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Legacy ID
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Value/Formula
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Aliases
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Dependencies
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Dependents
        
        # Двойной клик для редактирования
        self.variables_table.cellDoubleClicked.connect(self._edit_variable_v2)
        
        layout.addWidget(self.variables_table)
        variables_widget.setLayout(layout)
        
        self.tab_widget.addTab(variables_widget, "All Variables V2")
    
    def _setup_dependencies_v2_tab(self):
        """Настройка вкладки с зависимостями V2"""
        dependencies_widget = QWidget()
        layout = QVBoxLayout()
        
        # Информация
        info_label = QLabel("Dependency Graph V2 - Variables with formulas using new syntax")
        info_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(info_label)
        
        # Текстовое представление графа
        self.dependencies_text = QTextEdit()
        self.dependencies_text.setFont(QFont("Courier", 10))
        self.dependencies_text.setReadOnly(True)
        layout.addWidget(self.dependencies_text)
        
        dependencies_widget.setLayout(layout)
        self.tab_widget.addTab(dependencies_widget, "Dependencies V2")
    
    def _setup_statistics_v2_tab(self):
        """Настройка вкладки со статистикой V2"""
        stats_widget = QWidget()
        layout = QVBoxLayout()
        
        # Статистика
        self.stats_text = QTextEdit()
        self.stats_text.setFont(QFont("Courier", 10))
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        stats_widget.setLayout(layout)
        self.tab_widget.addTab(stats_widget, "Statistics V2")
    
    def _setup_expression_test_tab(self):
        """Настройка вкладки тестирования выражений V2"""
        test_widget = QWidget()
        layout = QVBoxLayout()
        
        # Информация
        info_label = QLabel("Test V2 Expressions - variable@solution=value, variable.solution, L=600")
        info_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        layout.addWidget(info_label)
        
        # Поле ввода с автодополнением
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Expression:"))
        
        self.expression_input = QLineEdit()
        self.expression_input.setPlaceholderText("length@box=600, width@result=width.panel-2*thickness.edge, L=400")
        
        # Автодополнение
        self.completer = V2VariableCompleter()
        self.expression_input.setCompleter(self.completer)
        
        input_layout.addWidget(self.expression_input)
        
        test_btn = QPushButton("Test Expression")
        test_btn.clicked.connect(self._test_expression_v2)
        input_layout.addWidget(test_btn)
        
        layout.addLayout(input_layout)
        
        # Подсветка синтаксиса
        self.highlighter = V2FormulaHighlighter(self.expression_input.document())
        
        # Результат
        self.test_result = QTextEdit()
        self.test_result.setMaximumHeight(200)
        self.test_result.setFont(QFont("Courier", 10))
        layout.addWidget(self.test_result)
        
        # Примеры
        examples_group = QGroupBox("Examples")
        examples_layout = QVBoxLayout()
        
        examples = [
            ("Assignment", "length@box=600"),
            ("Formula", "width@result=width.panel - 2*thickness.edge"),
            ("Math", "diagonal@panel=sqrt(length.panel^2 + width.panel^2)"),
            ("Alias", "L=600"),
            ("Read", "a=volume.box")
        ]
        
        for name, example in examples:
            btn = QPushButton(f"{name}: {example}")
            btn.clicked.connect(lambda checked, ex=example: self._load_example(ex))
            examples_layout.addWidget(btn)
        
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        test_widget.setLayout(layout)
        self.tab_widget.addTab(test_widget, "Expression Test V2")
    
    def _setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_action = QAction("Export Variables V2 to JSON", self)
        export_action.triggered.connect(self._export_variables_v2)
        file_menu.addAction(export_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        validate_action = QAction("Validate All V2 Expressions", self)
        validate_action.triggered.connect(self._validate_all_expressions_v2)
        tools_menu.addAction(validate_action)
        
        migrate_action = QAction("Help: Legacy to V2 Migration", self)
        migrate_action.triggered.connect(self._show_migration_help)
        tools_menu.addAction(migrate_action)
    
    def _refresh_data(self):
        """Обновить данные во всех вкладках"""
        if not CORE_V2_AVAILABLE:
            return
        
        try:
            # Обновляем таблицу переменных
            self._update_variables_table_v2()
            
            # Обновляем граф зависимостей
            self._update_dependencies_view_v2()
            
            # Обновляем статистику
            self._update_statistics_v2()
            
            # Обновляем автодополнение
            self.completer.update_completions()
            
        except Exception as e:
            print(f"Ошибка обновления данных V2: {e}")
    
    def _update_variables_table_v2(self):
        """Обновить таблицу переменных V2"""
        variables_info = V2GlobalVariableRegistry.get_all_variables_info()
        
        # Применяем фильтр поиска
        search_term = self.search_input.text().lower()
        if search_term:
            variables_info = [var for var in variables_info if self._matches_search_v2(var, search_term)]
        
        self.variables_table.setRowCount(len(variables_info))
        
        for row, var_info in enumerate(variables_info):
            # Solution
            solution_name = var_info.get('solution_name', 'Unknown')
            self.variables_table.setItem(row, 0, QTableWidgetItem(solution_name))
            
            # Write ID (V2)
            write_id = var_info.get('new_write_id', '')
            write_id_item = QTableWidgetItem(write_id)
            write_id_item.setForeground(QColor("#cc6600"))
            self.variables_table.setItem(row, 1, write_id_item)
            
            # Read ID (V2)
            read_id = var_info.get('new_read_id', '')
            read_id_item = QTableWidgetItem(read_id)
            read_id_item.setForeground(QColor("#0066cc"))
            self.variables_table.setItem(row, 2, read_id_item)
            
            # Legacy ID
            legacy_id = var_info.get('legacy_full_id', '')
            legacy_id_item = QTableWidgetItem(legacy_id)
            legacy_id_item.setForeground(QColor("#999999"))
            self.variables_table.setItem(row, 3, legacy_id_item)
            
            # Name
            self.variables_table.setItem(row, 4, QTableWidgetItem(var_info.get('name', '')))
            
            # Value/Formula
            if var_info.get('is_formula', False):
                formula = var_info.get('formula', '')
                computed = var_info.get('computed_value', 0)
                value_text = f"= {formula} → {computed}"
                value_item = QTableWidgetItem(value_text)
                value_item.setForeground(QColor("#cc6600"))
            else:
                value_text = str(var_info.get('value', ''))
                value_item = QTableWidgetItem(value_text)
            
            self.variables_table.setItem(row, 5, value_item)
            
            # Type
            var_type = var_info.get('type', 'unknown')
            type_item = QTableWidgetItem(var_type)
            if var_type == 'formula':
                type_item.setForeground(QColor("#cc6600"))
            elif var_type == 'controllable':
                type_item.setForeground(QColor("#009900"))
            self.variables_table.setItem(row, 6, type_item)
            
            # Aliases
            aliases = var_info.get('aliases', [])
            aliases_text = ", ".join(aliases) if aliases else ""
            self.variables_table.setItem(row, 7, QTableWidgetItem(aliases_text))
            
            # Dependencies
            dependencies = var_info.get('dependencies', [])
            deps_text = ", ".join(dependencies) if dependencies else ""
            self.variables_table.setItem(row, 8, QTableWidgetItem(deps_text))
            
            # Dependents
            dependents = var_info.get('dependents', [])
            dependents_text = ", ".join(dependents) if dependents else ""
            self.variables_table.setItem(row, 9, QTableWidgetItem(dependents_text))
    
    def _update_dependencies_view_v2(self):
        """Обновить представление зависимостей V2"""
        text = "DEPENDENCY GRAPH V2 - New Syntax\n"
        text += "=" * 60 + "\n\n"
        
        # Получаем все переменные с формулами
        all_solutions = v2_solution_manager.get_all_solutions()
        formula_vars = []
        
        for solution_name, solution in all_solutions.items():
            for var_name, var in solution.variables.items():
                if var.is_formula:
                    formula_vars.append((solution_name, var_name, var))
        
        if not formula_vars:
            text += "No formula variables found.\n"
        else:
            for solution_name, var_name, var in formula_vars:
                text += f"{var.read_id}: {var.name}\n"
                text += f"  Write: {var.full_id}\n"
                text += f"  Formula: {var.formula}\n"
                
                if var.dependencies:
                    text += f"  Depends on: {', '.join(var.dependencies)}\n"
                else:
                    text += f"  Depends on: none\n"
                
                # Получаем зависимые переменные
                dependents = v2_dependency_tracker.get_dependent_variables(var.read_id)
                if dependents:
                    text += f"  Used by: {', '.join(dependents)}\n"
                else:
                    text += f"  Used by: none\n"
                
                text += "\n"
        
        self.dependencies_text.setText(text)
    
    def _update_statistics_v2(self):
        """Обновить статистику V2"""
        all_solutions = v2_solution_manager.get_all_solutions()
        
        total_solutions = len(all_solutions)
        total_variables = 0
        formula_count = 0
        alias_count = 0
        
        for solution in all_solutions.values():
            total_variables += len(solution.variables)
            alias_count += len(solution.aliases)
            
            for var in solution.variables.values():
                if var.is_formula:
                    formula_count += 1
        
        # Создаем текст статистики
        stats_text = "GLOBAL REGISTRY STATISTICS V2\n"
        stats_text += "=" * 40 + "\n\n"
        
        stats_text += f"Solutions: {total_solutions}\n"
        stats_text += f"Variables: {total_variables}\n"
        stats_text += f"Formula Variables: {formula_count}\n"
        stats_text += f"Aliases: {alias_count}\n\n"
        
        if total_variables > 0:
            formula_percentage = (formula_count / total_variables * 100)
            stats_text += f"Formula Percentage: {formula_percentage:.1f}%\n"
        
        stats_text += f"\nV2 Syntax Usage:\n"
        stats_text += f"  • Write syntax: variable@solution=value\n"
        stats_text += f"  • Read syntax: variable.solution\n"
        stats_text += f"  • Local aliases: L, W, H (isolated per solution)\n"
        
        # Топ Solution по количеству переменных
        if all_solutions:
            stats_text += f"\nVariables per Solution:\n"
            for solution_name, solution in all_solutions.items():
                var_count = len(solution.variables)
                formula_count_sol = sum(1 for var in solution.variables.values() if var.is_formula)
                stats_text += f"  {solution_name}: {var_count} variables ({formula_count_sol} formulas)\n"
        
        self.stats_text.setText(stats_text)
    
    def _matches_search_v2(self, var_info: dict, search_term: str) -> bool:
        """Проверить, соответствует ли переменная поисковому запросу V2"""
        searchable_fields = [
            var_info.get('name', ''),
            var_info.get('new_write_id', ''),
            var_info.get('new_read_id', ''),
            var_info.get('legacy_full_id', ''),
            var_info.get('solution_name', ''),
        ]
        
        # Поиск в алиасах
        aliases = var_info.get('aliases', [])
        searchable_fields.extend(aliases)
        
        # Поиск в формуле
        if var_info.get('is_formula') and var_info.get('formula'):
            searchable_fields.append(var_info['formula'])
        
        return any(search_term in field.lower() for field in searchable_fields)
    
    def _filter_variables(self):
        """Применить фильтр поиска"""
        self._update_variables_table_v2()
    
    def _edit_variable_v2(self, row: int, column: int):
        """Редактировать переменную V2"""
        if column != 5:  # Только колонка Value/Formula
            return
        
        # Получаем информацию о переменной
        write_id_item = self.variables_table.item(row, 1)
        if not write_id_item:
            return
        
        write_id = write_id_item.text()
        # Парсим write_id для получения solution и variable
        if '@' in write_id:
            var_name, solution_name = write_id.split('@')
            solution = v2_solution_manager.get_solution(solution_name)
            if solution and var_name in solution.variables:
                variable = solution.variables[var_name]
                
                # Открываем диалог редактирования
                dialog = V2VariableEditDialog(variable, solution_name, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.variable_updated.emit(write_id)
                    self._refresh_data()
    
    def _test_expression_v2(self):
        """Тестировать выражение V2"""
        expression = self.expression_input.text().strip()
        if not expression:
            return
        
        try:
            # Парсим выражение
            parsed = ExpressionParser.parse_expression(expression)
            
            result_text = f"Expression: {expression}\n"
            result_text += f"Type: {parsed['type'].value}\n"
            result_text += "-" * 40 + "\n"
            
            for key, value in parsed.items():
                if key != 'type':
                    result_text += f"{key}: {value}\n"
            
            # Если это формула, пытаемся вычислить
            if parsed['type'] == ExpressionType.FORMULA:
                try:
                    formula = parsed['formula']
                    solution_registry = v2_solution_manager.get_all_solutions()
                    result = V2FormulaEvaluator.evaluate_formula(formula, solution_registry)
                    result_text += f"\nComputed Result: {result}\n"
                except Exception as e:
                    result_text += f"\nComputation Error: {e}\n"
            
            result_text += "\n✅ Expression is valid!\n"
            
        except Exception as e:
            result_text = f"Expression: {expression}\n"
            result_text += f"❌ Parse Error: {e}\n"
        
        self.test_result.setText(result_text)
    
    def _load_example(self, example: str):
        """Загрузить пример выражения"""
        self.expression_input.setText(example)
        self._test_expression_v2()
    
    def _export_variables_v2(self):
        """Экспорт переменных V2 в JSON"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Variables V2", "variables_v2.json", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                variables_info = V2GlobalVariableRegistry.get_all_variables_info()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(variables_info, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Success", f"Variables V2 exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def _validate_all_expressions_v2(self):
        """Проверить все выражения V2"""
        all_solutions = v2_solution_manager.get_all_solutions()
        
        valid_count = 0
        error_count = 0
        errors = []
        
        for solution in all_solutions.values():
            for var in solution.variables.values():
                if var.is_formula:
                    try:
                        var.get_computed_value(all_solutions)
                        if var.computation_error:
                            error_count += 1
                            errors.append(f"{var.read_id}: {var.computation_error}")
                        else:
                            valid_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"{var.read_id}: {str(e)}")
        
        # Показываем результат
        result_text = f"V2 Expression Validation Results:\n\n"
        result_text += f"Valid expressions: {valid_count}\n"
        result_text += f"Expressions with errors: {error_count}\n\n"
        
        if errors:
            result_text += "Errors:\n"
            for error in errors[:20]:  # Показываем первые 20 ошибок
                result_text += f"  • {error}\n"
            
            if len(errors) > 20:
                result_text += f"  ... and {len(errors) - 20} more errors"
        
        msg = QMessageBox(self)
        msg.setWindowTitle("V2 Expression Validation")
        msg.setText(result_text)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.exec()
    
    def _show_migration_help(self):
        """Показать справку по миграции с Legacy на V2"""
        help_text = """MIGRATION FROM LEGACY TO V2 SYNTAX

Old Syntax (#1.length) → New Syntax (variable@solution)

WRITING VALUES:
Legacy: panel.variables.get_variable_by_reference("#1").value = 600
V2:     length@panel=600

READING VALUES:
Legacy: panel.variables.get_variable_by_reference("#1").value
V2:     length.panel

FORMULAS:
Legacy: "#1.width - 2 * #2.thickness"
V2:     "width.panel - 2*thickness.edge"

ALIASES:
Legacy: #1.L (global reference)
V2:     L (local to solution only)

BENEFITS OF V2:
✅ More intuitive: length@panel vs #1.length
✅ Readable formulas: width.panel - 2*thickness.edge
✅ Safe aliases: isolated per solution
✅ Clear semantics: @ for write, . for read
✅ Backward compatible: #1.length still works

MIGRATION STRATEGY:
1. Start using V2 syntax for new variables
2. Gradually convert existing formulas
3. Test expressions in Expression Test V2 tab
4. Use HybridSolution for compatibility
"""
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Legacy to V2 Migration Help")
        msg.setText(help_text)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.exec()

class V2VariableEditDialog(QDialog):
    """Диалог редактирования переменной V2"""
    
    def __init__(self, variable: V2Variable, solution_name: str, parent=None):
        super().__init__(parent)
        self.variable = variable
        self.solution_name = solution_name
        self.setWindowTitle(f"Edit Variable V2 - {variable.read_id}")
        self.setFixedSize(600, 500)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Информация о переменной
        info_group = QGroupBox("Variable Information V2")
        info_layout = QFormLayout()
        
        info_layout.addRow("Write ID:", QLabel(self.variable.full_id))
        info_layout.addRow("Read ID:", QLabel(self.variable.read_id))
        info_layout.addRow("Name:", QLabel(self.variable.name))
        info_layout.addRow("Solution:", QLabel(self.variable.solution_name))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Редактирование значения/формулы
        edit_group = QGroupBox("Value / Expression V2")
        edit_layout = QVBoxLayout()
        
        if self.variable.is_formula:
            edit_layout.addWidget(QLabel("Expression (V2 Syntax):"))
            self.expression_edit = QPlainTextEdit()
            self.expression_edit.setPlainText(f"{self.variable.name}@{self.solution_name}={self.variable.formula}")
            self.expression_edit.setMaximumHeight(100)
            
            # Подсветка синтаксиса V2
            highlighter = V2FormulaHighlighter(self.expression_edit.document())
            
            edit_layout.addWidget(self.expression_edit)
            
            # Кнопка тестирования выражения
            test_btn = QPushButton("Test V2 Expression")
            test_btn.clicked.connect(self._test_expression)
            edit_layout.addWidget(test_btn)
            
            # Результат
            self.result_label = QLabel()
            self.result_label.setWordWrap(True)
            edit_layout.addWidget(self.result_label)
            
            self._test_expression()  # Показываем текущий результат
            
        else:
            edit_layout.addWidget(QLabel("Value:"))
            self.value_edit = QLineEdit()
            self.value_edit.setText(str(self.variable._value))
            edit_layout.addWidget(self.value_edit)
            
            # Кнопка для превращения в выражение V2
            expression_btn = QPushButton("Convert to V2 Expression")
            expression_btn.clicked.connect(self._convert_to_expression)
            edit_layout.addWidget(expression_btn)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # Зависимости V2
        if self.variable.is_formula:
            deps_group = QGroupBox("Dependencies V2")
            deps_layout = QVBoxLayout()
            
            if self.variable.dependencies:
                deps_text = "Depends on: " + ", ".join(self.variable.dependencies)
            else:
                deps_text = "No dependencies"
            deps_layout.addWidget(QLabel(deps_text))
            
            dependents = v2_dependency_tracker.get_dependent_variables(self.variable.read_id)
            if dependents:
                dependents_text = "Used by: " + ", ".join(dependents)
            else:
                dependents_text = "Not used by any variables"
            deps_layout.addWidget(QLabel(dependents_text))
            
            deps_group.setLayout(deps_layout)
            layout.addWidget(deps_group)
        
        # Примеры V2 синтаксиса
        examples_group = QGroupBox("V2 Syntax Examples")
        examples_layout = QVBoxLayout()
        
        examples_text = """Examples:
• length@panel=600                    (set value)
• width@result=width.panel-2*thickness.edge    (formula)
• diagonal@panel=sqrt(length.panel^2+width.panel^2)  (math)
• L=600                              (local alias)"""
        
        examples_layout.addWidget(QLabel(examples_text))
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _test_expression(self):
        """Тестировать выражение V2"""
        if not hasattr(self, 'expression_edit'):
            return
        
        expression = self.expression_edit.toPlainText().strip()
        
        try:
            parsed = ExpressionParser.parse_expression(expression)
            
            if parsed['type'] == ExpressionType.FORMULA:
                # Тестируем формулу
                formula = parsed['formula']
                solution_registry = v2_solution_manager.get_all_solutions()
                result = V2FormulaEvaluator.evaluate_formula(formula, solution_registry)
                
                self.result_label.setText(f"✅ Result: {result}")
                self.result_label.setStyleSheet("color: green;")
            else:
                self.result_label.setText(f"✅ Valid {parsed['type'].value} expression")
                self.result_label.setStyleSheet("color: green;")
                
        except Exception as e:
            self.result_label.setText(f"❌ Error: {str(e)}")
            self.result_label.setStyleSheet("color: red;")
    
    def _convert_to_expression(self):
        """Превратить значение в выражение V2"""
        current_value = self.value_edit.text()
        
        # Создаем выражение V2
        if '.' in current_value or '@' in current_value:
            QMessageBox.information(self, "Info", "Value already looks like a V2 expression")
        else:
            new_expression = f"{self.variable.name}@{self.solution_name}={current_value}"
            self.value_edit.setText(new_expression)
    
    def accept(self):
        """Применить изменения"""
        try:
            solution_registry = v2_solution_manager.get_all_solutions()
            solution = solution_registry.get(self.solution_name)
            
            if not solution:
                QMessageBox.critical(self, "Error", f"Solution '{self.solution_name}' not found")
                return
            
            if self.variable.is_formula and hasattr(self, 'expression_edit'):
                # Обновляем выражение
                expression = self.expression_edit.toPlainText().strip()
                solution.execute_expression(expression, solution_registry)
                
            elif hasattr(self, 'value_edit'):
                # Обновляем значение
                new_value = self.value_edit.text().strip()
                if '.' in new_value or '@' in new_value:
                    # Это выражение V2
                    solution.execute_expression(new_value, solution_registry)
                else:
                    # Обычное значение
                    expression = f"{self.variable.name}@{self.solution_name}={new_value}"
                    solution.execute_expression(expression, solution_registry)
            
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update variable: {str(e)}")

# =============================================================================
# Диалог создания с поддержкой V2
# =============================================================================

class V2CreateBoxDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Box Solution V2 - New Syntax")
        self.setFixedSize(500, 400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QFormLayout()
        
        # Информация о новом синтаксисе
        info_label = QLabel("Using new V2 syntax: variable@solution and variable.solution")
        info_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        layout.addRow("", info_label)
        
        self.name_edit = QLineEdit("panel")
        layout.addRow("Solution Name:", self.name_edit)
        
        # Поля с поддержкой V2 синтаксиса
        length_group = QGroupBox("Length (V2 Syntax)")
        length_layout = QVBoxLayout()
        self.length_edit = QLineEdit("600")
        self.length_edit.setPlaceholderText("600 or length.otherpanel or width.panel-20...")
        
        # Автодополнение
        self.length_completer = V2VariableCompleter()
        self.length_edit.setCompleter(self.length_completer)
        
        length_layout.addWidget(self.length_edit)
        length_group.setLayout(length_layout)
        layout.addRow(length_group)
        
        width_group = QGroupBox("Width (V2 Syntax)")
        width_layout = QVBoxLayout()
        self.width_edit = QLineEdit("400")
        self.width_edit.setPlaceholderText("400 or width.panel - 2*thickness.edge...")
        
        self.width_completer = V2VariableCompleter()
        self.width_edit.setCompleter(self.width_completer)
        
        width_layout.addWidget(self.width_edit)
        width_group.setLayout(width_layout)
        layout.addRow(width_group)
        
        height_group = QGroupBox("Height (V2 Syntax)")
        height_layout = QVBoxLayout()
        self.height_edit = QLineEdit("18")
        self.height_edit.setPlaceholderText("18 or max(height.panel, 16)...")
        
        self.height_completer = V2VariableCompleter()
        self.height_edit.setCompleter(self.height_completer)
        
        height_layout.addWidget(self.height_edit)
        height_group.setLayout(height_layout)
        layout.addRow(height_group)
        
        # Подсветка синтаксиса для всех полей
        V2FormulaHighlighter(self.length_edit.document())
        V2FormulaHighlighter(self.width_edit.document())
        V2FormulaHighlighter(self.height_edit.document())
        
        # Информация о синтаксисе
        info_text = QLabel(
            "V2 Syntax Examples:\n"
            "• Numbers: 600, 18.5\n"
            "• References: length.panel, width.othersolution\n"
            "• Formulas: width.panel - 2*thickness.edge\n"
            "• Functions: sqrt, max, min, sin, cos...\n"
            "• Write: variable@solution=value\n"
            "• Read: variable.solution"
        )
        info_text.setStyleSheet("color: #666; font-size: 10px;")
        layout.addRow("", info_text)
        
        # Кнопки
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Create V2")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
    
    def get_solution(self):
        try:
            name = self.name_edit.text() or "panel"
            length = self.length_edit.text() or "600"
            width = self.width_edit.text() or "400" 
            height = self.height_edit.text() or "18"
            
            solution = BoxSolution(name, length, width, height)
            return solution
            
        except Exception as e:
            print(f"Ошибка создания решения V2: {e}")
            traceback.print_exc()
            return None

# =============================================================================
# Основное окно с поддержкой V2
# =============================================================================

class V2AdvancedMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Solving Advanced V2 - New Variable System (@solution & .solution)")
        self.setGeometry(100, 100, 1500, 1000)
        
        if CORE_V2_AVAILABLE:
            self.workspace = Part3DSpace("Main Workspace")
            v2_solution_manager.reset()
        else:
            self.workspace = None
        
        self.current_solution = None
        self.registry_window = None
        
        self._setup_ui()
        self._setup_menu()
        self._show_welcome()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout()
        
        # Левая панель
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Дерево решений (адаптируем для V2)
        self.solution_tree = QTreeWidget()
        self.solution_tree.setHeaderLabel("Solutions V2 (@solution syntax)")
        self.solution_tree.itemClicked.connect(self._on_solution_selected)
        left_splitter.addWidget(self.solution_tree)
        
        # Таблица переменных V2
        self.variable_table = QTableWidget()
        self.variable_table.setColumnCount(6)
        self.variable_table.setHorizontalHeaderLabels([
            "Write ID (V2)", "Read ID (V2)", "Legacy ID", "Value", "Type", "Aliases"
        ])
        left_splitter.addWidget(self.variable_table)
        
        left_splitter.setSizes([400, 400])
        
        # Правая панель - 3D viewer с информацией V2
        self.viewer_3d = QWidget()
        self.viewer_3d.setMinimumSize(400, 300)
        self.viewer_3d.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")
        
        viewer_layout = QVBoxLayout()
        
        # Заголовок
        self.solution_header = QLabel("Visual Solving V2 - New Syntax")
        self.solution_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.solution_header.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 5px;")
        viewer_layout.addWidget(self.solution_header)
        
        # Placeholder for 3D
        placeholder_label = QLabel("3D Viewer V2\n(Enhanced for new syntax)")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #888; font-size: 14px;")
        viewer_layout.addWidget(placeholder_label)
        
        # Информационная панель
        self.solution_info = QTextEdit()
        self.solution_info.setMaximumHeight(200)
        self.solution_info.setStyleSheet("background-color: #3a3a3a; color: white; font-family: monospace;")
        viewer_layout.addWidget(self.solution_info)
        
        self.viewer_3d.setLayout(viewer_layout)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self.viewer_3d)
        main_splitter.setSizes([700, 800])
        
        layout.addWidget(main_splitter)
        central_widget.setLayout(layout)
    
    def _setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Workspace V2", self)
        new_action.triggered.connect(self._new_workspace)
        file_menu.addAction(new_action)
        
        # Create menu
        create_menu = menubar.addMenu("Create")
        
        create_box_action = QAction("Box Solution V2 (New Syntax)", self)
        create_box_action.triggered.connect(self._create_box_v2)
        create_menu.addAction(create_box_action)
        
        create_demo_action = QAction("Demo Solutions V2", self)
        create_demo_action.triggered.connect(self._create_demo_solutions_v2)
        create_menu.addAction(create_demo_action)
        
        # Variables menu  
        variables_menu = menubar.addMenu("Variables")
        
        registry_action = QAction("Global Variable Registry V2", self)
        registry_action.triggered.connect(self._show_variable_registry_v2)
        variables_menu.addAction(registry_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        syntax_help_action = QAction("V2 Syntax Help", self)
        syntax_help_action.triggered.connect(self._show_syntax_help)
        help_menu.addAction(syntax_help_action)
    
    def _show_welcome(self):
        welcome_text = """
Visual Solving Advanced V2 - Revolutionary Variable System!

🚀 NEW V2 SYNTAX:
• Write variables: length@panel=600
• Read variables: width.panel, volume.box
• Local aliases: L=600 (only visible within solution)
• Formulas: width@result=width.panel - 2*thickness.edge

🎯 Try:
1. Create → Box Solution V2 (New Syntax)
2. Use V2 expressions: length@box=600
3. Variables → Global Variable Registry V2
4. Help → V2 Syntax Help

📋 V2 Examples:
• length@box=600                           # Set value
• width@result=width.panel - 2*thickness.edge  # Formula
• diagonal@panel=sqrt(length.panel^2 + width.panel^2)  # Math
• a=volume.box                             # Read value
• L=600                                    # Local alias

✅ ADVANTAGES:
• More intuitive than #1.length
• Readable formulas
• Safe aliases (isolated per solution)
• Clear semantics (@ for write, . for read)
• Backward compatible (#1.length still works)
        """
        self.solution_info.setText(welcome_text)
    
    def _new_workspace(self):
        if CORE_V2_AVAILABLE:
            self.workspace = Part3DSpace("Main Workspace")
            v2_solution_manager.reset()
        
        self.solution_tree.clear()
        self.variable_table.setRowCount(0)
        self.current_solution = None
        self._show_welcome()
    
    def _create_box_v2(self):
        if not CORE_V2_AVAILABLE:
            QMessageBox.warning(self, "Warning", "V2 Core system not available")
            return
        
        dialog = V2CreateBoxDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            solution = dialog.get_solution()
            
            if solution:
                solution.place_in_space(self.workspace)
                self._add_solution_to_tree(solution)
                self._on_solution_selected_direct(solution)
                
                # Показываем отладочную информацию V2
                solution.debug_variables()
    
    def _create_demo_solutions_v2(self):
        """Создать демонстрационные решения V2"""
        if not CORE_V2_AVAILABLE:
            return
        
        try:
            v2_solution_manager.reset()
            
            # Solution "panel" - базовая панель
            panel = BoxSolution("panel", 600, 400, 18)
            panel.place_in_space(self.workspace)
            self._add_solution_to_tree(panel)
            
            # Solution "edge" - кромка
            edge = EdgeBandingSolution("edge", "white", 2.0, ["top", "bottom"])
            edge.place_in_space(self.workspace)
            self._add_solution_to_tree(edge)
            
            # Solution "result" - панель с учетом кромки (V2 синтаксис!)
            result = BoxSolution(
                "result", 
                "length.panel",                    # V2 синтаксис!
                "width.panel - 2*thickness.edge", # V2 синтаксис!
                "height.panel"                     # V2 синтаксис!
            )
            result.place_in_space(self.workspace)
            self._add_solution_to_tree(result)
            
            # Solution "math" - математические операции
            math_panel = BoxSolution(
                "math",
                "sqrt(length.panel^2 + width.panel^2)",  # Диагональ
                "max(width.panel, width.result, 350)",   # Максимум
                "height.panel * 2"                       # Удвоенная высота
            )
            math_panel.place_in_space(self.workspace)
            self._add_solution_to_tree(math_panel)
            
            QMessageBox.information(self, "Demo V2 Created", 
                "Demo solutions V2 created!\n\n"
                "• panel: Base panel (600x400x18)\n"
                "• edge: PVC Edge (thickness=2)\n" 
                "• result: Panel with edge (width = width.panel - 2*thickness.edge)\n"
                "• math: Math Panel (length = diagonal of panel)\n\n"
                "Open Variables → Global Variable Registry V2 to see all V2 syntax!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create demo V2: {str(e)}")
    
    def _show_variable_registry_v2(self):
        """Показать окно глобального реестра переменных V2"""
        if self.registry_window is None:
            self.registry_window = V2GlobalVariableRegistryWindow(self)
            self.registry_window.variable_updated.connect(self._on_variable_updated)
        
        self.registry_window.show()
        self.registry_window.raise_()
        self.registry_window.activateWindow()
    
    def _show_syntax_help(self):
        """Показать справку по синтаксису V2"""
        help_text = """V2 SYNTAX HELP

WRITING VARIABLES:
variable@solution=value
• length@panel=600
• width@result=width.panel - 2*thickness.edge
• diagonal@math=sqrt(length.panel^2 + width.panel^2)

READING VARIABLES:
variable.solution
• a=volume.panel
• diagonal=length.panel
• maxsize=max(length.panel, width.panel)

LOCAL ALIASES:
alias=value (only within solution)
• L=600          # Local alias for length
• W=400          # Local alias for width
• H=18           # Local alias for height

RULES:
✅ @ symbol: for writing and setting values
✅ . symbol: for reading values only
✅ Aliases: cannot contain @ or . symbols
✅ Scope: aliases are isolated per solution
✅ Backward compatibility: #1.length still works

EXAMPLES:
Assignment:    length@box=600
Formula:       width@result=width.panel - 2*thickness.edge
Math:          diagonal@panel=sqrt(length.panel^2 + width.panel^2)
Read:          a=volume.box
Alias:         L=600

FUNCTIONS AVAILABLE:
sin, cos, tan, sqrt, abs, min, max, round

BENEFITS:
• More intuitive than #1.length
• Readable formulas
• Safe aliases (isolated per solution)
• Clear semantics (@ write, . read)
• Natural syntax
"""
        
        msg = QMessageBox(self)
        msg.setWindowTitle("V2 Syntax Help")
        msg.setText(help_text)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.exec()
    
    def _add_solution_to_tree(self, solution):
        """Добавить решение в дерево"""
        item = QTreeWidgetItem(self.solution_tree)
        item.setText(0, f"{solution.name} (V2)")
        item.setData(0, Qt.ItemDataRole.UserRole, solution)
        return item
    
    def _on_solution_selected(self, item, column):
        """Обработка выбора решения"""
        solution = item.data(0, Qt.ItemDataRole.UserRole)
        if solution:
            self._on_solution_selected_direct(solution)
    
    def _on_solution_selected_direct(self, solution):
        """Прямая обработка выбора решения"""
        self.current_solution = solution
        self._update_variable_table(solution)
        self._update_solution_info(solution)
    
    def _update_variable_table(self, solution):
        """Обновить таблицу переменных V2"""
        variables = solution.get_all_variables()
        self.variable_table.setRowCount(len(variables))
        
        for row, var in enumerate(variables):
            # Write ID (V2)
            write_id_item = QTableWidgetItem(var.new_write_id)
            write_id_item.setForeground(QColor("#cc6600"))
            self.variable_table.setItem(row, 0, write_id_item)
            
            # Read ID (V2)
            read_id_item = QTableWidgetItem(var.new_read_id)
            read_id_item.setForeground(QColor("#0066cc"))
            self.variable_table.setItem(row, 1, read_id_item)
            
            # Legacy ID
            legacy_id_item = QTableWidgetItem(var.legacy_full_id)
            legacy_id_item.setForeground(QColor("#999999"))
            self.variable_table.setItem(row, 2, legacy_id_item)
            
            # Value
            value_str = str(var.value)
            if isinstance(var.value, float):
                value_str = f"{var.value:.3f}"
            self.variable_table.setItem(row, 3, QTableWidgetItem(value_str))
            
            # Type
            var_type = "formula" if var.v2_variable.is_formula else "value"
            type_item = QTableWidgetItem(var_type)
            if var_type == "formula":
                type_item.setForeground(QColor("#cc6600"))
            self.variable_table.setItem(row, 4, type_item)
            
            # Aliases
            aliases_str = ", ".join(var.aliases)
            self.variable_table.setItem(row, 5, QTableWidgetItem(aliases_str))
    
    def _update_solution_info(self, solution):
        """Обновить информацию о решении"""
        info = f"Solution V2: {solution.name}\n"
        info += f"Type: {type(solution).__name__}\n"
        info += f"Variables: {len(solution.variables)}\n"
        info += "-" * 40 + "\n"
        
        info += "V2 VARIABLE SYSTEM:\n"
        for var in solution.get_all_variables():
            info += f"  Write: {var.new_write_id} = {var.value}\n"
            info += f"  Read:  {var.new_read_id}\n"
            if var.legacy_full_id:
                info += f"  Legacy: {var.legacy_full_id}\n"
            
            if var.v2_variable.is_formula:
                info += f"  Formula: {var.v2_variable.formula}\n"
            
            if var.aliases:
                info += f"  Aliases: {', '.join(var.aliases)}\n"
            info += "\n"
        
        # Специфичная информация для типов решений
        if isinstance(solution, BoxSolution):
            info += "BOX DIMENSIONS V2:\n"
            info += f"  Length: {solution.length:.1f} mm\n"
            info += f"  Width: {solution.width:.1f} mm\n"
            info += f"  Height: {solution.height:.1f} mm\n"
        
        self.solution_info.setText(info)
    
    def _on_variable_updated(self, variable_id: str):
        """Обработка обновления переменной"""
        if self.current_solution:
            self._update_variable_table(self.current_solution)
            self._update_solution_info(self.current_solution)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    if not CORE_V2_AVAILABLE:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("V2 Core Error")
        msg.setText("Advanced V2 core system not found")
        msg.setInformativeText("variable_system_v2.py or visual_solving_advanced_v2.py not found or has errors")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        return
    
    window = V2AdvancedMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
