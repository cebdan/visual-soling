# Visual Solving MVP - UI с иерархической адресацией переменных
# PyQt6 implementation with hierarchical variable addressing

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTableWidget, 
                            QTableWidgetItem, QSplitter, QMenuBar, QFileDialog, 
                            QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, 
                            QComboBox, QPushButton, QLabel, QTextEdit, QCheckBox,
                            QListWidget, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QColor
import json
import traceback

# Импорт нашей системы с иерархической адресацией
try:
    from visual_solving_hierarchical import (
        Solution, BoxSolution, EdgeBandingSolution, VsolFormat, Part3DSpace, 
        HierarchicalVariable, VariableType, solution_number_manager
    )
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"Ошибка импорта ядра: {e}")
    CORE_AVAILABLE = False

class HierarchicalSolutionTreeWidget(QTreeWidget):
    solution_selected = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.setHeaderLabel("Solutions (Hierarchical)")
        self.itemClicked.connect(self._on_item_clicked)
        
        # Store solution references
        self._item_solution_map = {}
    
    def add_solution(self, solution: Solution, parent_item=None):
        try:
            if parent_item is None:
                item = QTreeWidgetItem(self)
            else:
                item = QTreeWidgetItem(parent_item)
            
            # Показываем номер Solution и тип
            solution_text = f"#{solution.solution_number}: {solution.name} ({type(solution).__name__})"
            item.setText(0, solution_text)
            self._item_solution_map[item] = solution
            
            # Add child solutions
            for child in solution.parent_solutions:
                self.add_solution(child, item)
            
            item.setExpanded(True)
            return item
        except Exception as e:
            print(f"Ошибка добавления solution в дерево: {e}")
            traceback.print_exc()
    
    def _on_item_clicked(self, item, column):
        try:
            solution = self._item_solution_map.get(item)
            if solution:
                self.solution_selected.emit(solution)
        except Exception as e:
            print(f"Ошибка выбора solution: {e}")
    
    def clear_solutions(self):
        self.clear()
        self._item_solution_map.clear()

class HierarchicalVariableTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Full ID", "Named ID", "Name", "Value", "Type", "Aliases"
        ])
        
        # Настройка ширины колонок
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Full ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Named ID
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Value
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Aliases
    
    def update_variables(self, solution: Solution):
        try:
            variables = solution.variables.get_all_variables()
            self.setRowCount(len(variables))
            
            for row, var in enumerate(variables):
                # Full ID: #1.2
                full_id_item = QTableWidgetItem(var.full_id)
                full_id_item.setForeground(QColor("#0066cc"))  # Синий цвет
                self.setItem(row, 0, full_id_item)
                
                # Named ID: #1.length
                named_id_item = QTableWidgetItem(var.named_id)
                named_id_item.setForeground(QColor("#009900"))  # Зеленый цвет
                self.setItem(row, 1, named_id_item)
                
                # Variable name
                self.setItem(row, 2, QTableWidgetItem(var.name))
                
                # Variable value
                value_str = str(var.value)
                if isinstance(var.value, float):
                    value_str = f"{var.value:.3f}"
                elif isinstance(var.value, list):
                    value_str = ", ".join(str(v) for v in var.value)
                self.setItem(row, 3, QTableWidgetItem(value_str))
                
                # Variable type
                type_item = QTableWidgetItem(var.variable_type.value)
                if var.variable_type == VariableType.CONTROLLABLE:
                    type_item.setForeground(QColor("#cc6600"))  # Оранжевый
                elif var.variable_type == VariableType.DERIVED:
                    type_item.setForeground(QColor("#666666"))  # Серый
                self.setItem(row, 4, type_item)
                
                # Aliases с полными ссылками
                alias_references = []
                for alias in var.aliases:
                    alias_references.append(f"#{var.solution_number}.{alias}")
                    alias_references.append(alias)  # Локальная ссылка
                
                aliases_str = ", ".join(alias_references)
                self.setItem(row, 5, QTableWidgetItem(aliases_str))
        except Exception as e:
            print(f"Ошибка обновления переменных: {e}")
            traceback.print_exc()
    
    def clear_variables(self):
        self.setRowCount(0)

class Enhanced3DViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #2a2a2a; border: 1px solid #555;")
        
        layout = QVBoxLayout()
        
        # Заголовок с номером Solution
        self.solution_header = QLabel("3D Viewer - Hierarchical Variables")
        self.solution_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.solution_header.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(self.solution_header)
        
        # Placeholder for 3D visualization
        placeholder_label = QLabel("3D Viewer\n(Placeholder)")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(placeholder_label)
        
        # Информационная панель
        self.solution_info = QTextEdit()
        self.solution_info.setMaximumHeight(150)
        self.solution_info.setStyleSheet("background-color: #3a3a3a; color: white; font-family: monospace;")
        layout.addWidget(self.solution_info)
        
        self.setLayout(layout)
    
    def update_solution(self, solution: Solution):
        try:
            # Обновляем заголовок
            self.solution_header.setText(f"Solution #{solution.solution_number}: {solution.name}")
            
            # Создаем детальную информацию
            info = f"Solution #{solution.solution_number}: {solution.name}\n"
            info += f"Type: {type(solution).__name__}\n"
            info += f"Variables: {len(solution.variables.get_all_variables())}\n"
            info += f"UUID: {solution.solution_id[:8]}...\n"
            info += "-" * 40 + "\n"
            
            # Показываем переменные с иерархической адресацией
            info += "HIERARCHICAL VARIABLES:\n"
            for var in solution.variables.get_all_variables():
                info += f"  {var.full_id} | {var.named_id} = {var.value}\n"
                
                # Показываем алиасы
                if var.aliases:
                    for alias in var.aliases:
                        info += f"    └─ #{var.solution_number}.{alias} = {var.value}\n"
            
            info += "\n"
            
            # Специфичная информация для типов решений
            if isinstance(solution, BoxSolution):
                info += "BOX DIMENSIONS:\n"
                info += f"  Length: {solution.length:.1f} mm\n"
                info += f"  Width: {solution.width:.1f} mm\n"
                info += f"  Height: {solution.height:.1f} mm\n"
                
                # Получаем объем через иерархическую ссылку
                volume_var = solution.variables.get_variable_by_reference("volume")
                if volume_var:
                    info += f"  Volume: {volume_var.value:.2f} mm³\n"
            
            if solution.parent_solutions:
                info += f"\nCOMPOSED FROM:\n"
                for parent in solution.parent_solutions:
                    info += f"  └─ #{parent.solution_number}: {parent.name}\n"
            
            self.solution_info.setText(info)
        except Exception as e:
            print(f"Ошибка обновления 3D viewer: {e}")
            self.solution_info.setText(f"Error: {str(e)}")

class CreateBoxDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Box Solution")
        self.setFixedSize(350, 250)
        
        try:
            layout = QFormLayout()
            
            # Показываем какой номер получит Solution
            next_number = solution_number_manager._next_number
            self.info_label = QLabel(f"Will be assigned Solution #{next_number}")
            self.info_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addRow("Solution Number:", self.info_label)
            
            self.name_edit = QLineEdit("New Box")
            
            self.length_spin = QDoubleSpinBox()
            self.length_spin.setRange(1, 10000)
            self.length_spin.setValue(600)
            self.length_spin.setSuffix(" mm")
            
            self.width_spin = QDoubleSpinBox()
            self.width_spin.setRange(1, 10000)
            self.width_spin.setValue(400)
            self.width_spin.setSuffix(" mm")
            
            self.height_spin = QDoubleSpinBox()
            self.height_spin.setRange(1, 1000)
            self.height_spin.setValue(18)
            self.height_spin.setSuffix(" mm")
            
            layout.addRow("Name:", self.name_edit)
            layout.addRow("Length (will be #X.1):", self.length_spin)
            layout.addRow("Width (will be #X.2):", self.width_spin)
            layout.addRow("Height (will be #X.3):", self.height_spin)
            
            # Информация о переменных
            info_text = QLabel("Variables will be:\n• #X.1, #X.length, #X.L\n• #X.2, #X.width, #X.W\n• #X.3, #X.height, #X.H\n• #X.4, #X.volume, #X.vol")
            info_text.setStyleSheet("color: #666; font-size: 10px;")
            layout.addRow("", info_text)
            
            # Buttons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("Create")
            cancel_button = QPushButton("Cancel")
            
            ok_button.clicked.connect(self.accept)
            cancel_button.clicked.connect(self.reject)
            
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            
            layout.addRow(button_layout)
            self.setLayout(layout)
            
        except Exception as e:
            print(f"Ошибка создания диалога CreateBox: {e}")
            traceback.print_exc()
    
    def get_solution(self):
        try:
            name = self.name_edit.text() or "Box"
            length = self.length_spin.value()
            width = self.width_spin.value()
            height = self.height_spin.value()
            
            print(f"Создаем BoxSolution: {name}, {length}, {width}, {height}")
            
            solution = BoxSolution(name, length, width, height)
            print(f"BoxSolution создан: #{solution.solution_number}: {solution.name}")
            return solution
            
        except Exception as e:
            print(f"Ошибка в get_solution: {e}")
            traceback.print_exc()
            return None

class VariableReferenceDialog(QDialog):
    """Диалог для тестирования ссылок на переменные"""
    
    def __init__(self, solution: Solution, parent=None):
        super().__init__(parent)
        self.solution = solution
        self.setWindowTitle(f"Test Variable References - Solution #{solution.solution_number}")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Инструкция
        instruction = QLabel("Enter variable reference to test:")
        layout.addWidget(instruction)
        
        # Поле ввода
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("e.g., #1.length, #1.1, length, L")
        layout.addWidget(self.reference_input)
        
        # Кнопка тестирования
        test_button = QPushButton("Test Reference")
        test_button.clicked.connect(self.test_reference)
        layout.addWidget(test_button)
        
        # Результат
        self.result_text = QTextEdit()
        self.result_text.setStyleSheet("background-color: #f5f5f5; font-family: monospace;")
        layout.addWidget(self.result_text)
        
        # Справка
        help_text = QLabel("Available reference formats:\n"
                          f"• Full ID: #{solution.solution_number}.1, #{solution.solution_number}.2, ...\n"
                          f"• Named ID: #{solution.solution_number}.length, #{solution.solution_number}.width, ...\n"
                          f"• Aliases: #{solution.solution_number}.L, #{solution.solution_number}.W, ...\n"
                          "• Local: length, width, L, W, ...")
        help_text.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(help_text)
        
        # Показать все доступные ссылки
        self.show_all_references()
        
        self.setLayout(layout)
    
    def show_all_references(self):
        """Показать все доступные ссылки"""
        text = f"SOLUTION #{self.solution.solution_number}: {self.solution.name}\n"
        text += "=" * 50 + "\n\n"
        text += "ALL AVAILABLE REFERENCES:\n"
        text += "-" * 30 + "\n"
        
        for var in self.solution.variables.get_all_variables():
            text += f"\nVariable: {var.name} = {var.value}\n"
            text += f"  {var.full_id}      ← Full ID\n"
            text += f"  {var.named_id}    ← Named ID\n"
            text += f"  {var.name}        ← Local name\n"
            
            for alias in var.aliases:
                text += f"  #{var.solution_number}.{alias}       ← Alias (full)\n"
                text += f"  {alias}           ← Alias (local)\n"
        
        self.result_text.setText(text)
    
    def test_reference(self):
        reference = self.reference_input.text().strip()
        if not reference:
            return
        
        try:
            var = self.solution.variables.get_variable_by_reference(reference)
            
            if var:
                result = f"✅ REFERENCE FOUND: '{reference}'\n"
                result += f"   → {var.full_id} ({var.named_id})\n"
                result += f"   → {var.name} = {var.value}\n"
                result += f"   → Type: {var.variable_type.value}\n"
                
                if var.aliases:
                    result += f"   → Aliases: {', '.join(var.aliases)}\n"
            else:
                result = f"❌ REFERENCE NOT FOUND: '{reference}'\n"
                result += f"   Available references for Solution #{self.solution.solution_number}:\n"
                
                for var in self.solution.variables.get_all_variables():
                    result += f"     • {var.full_id}, {var.named_id}, {var.name}\n"
                    for alias in var.aliases:
                        result += f"     • #{var.solution_number}.{alias}, {alias}\n"
            
            # Добавляем к существующему тексту
            current_text = self.result_text.toPlainText()
            self.result_text.setText(current_text + "\n" + "=" * 50 + "\n" + result)
            
        except Exception as e:
            error_text = f"❌ ERROR: {str(e)}\n"
            current_text = self.result_text.toPlainText()
            self.result_text.setText(current_text + "\n" + error_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Solving MVP - Hierarchical Variables")
        self.setGeometry(100, 100, 1400, 900)
        
        # Current workspace
        if CORE_AVAILABLE:
            self.workspace = Part3DSpace("Main Workspace")
            # Сброс нумерации для чистого начала
            solution_number_manager.reset()
        else:
            self.workspace = None
        self.current_solution = None
        
        self._setup_ui()
        self._setup_menu()
        
        # Show welcome message
        self._show_welcome()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left panel - Solution tree and variables
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Solution tree
        self.solution_tree = HierarchicalSolutionTreeWidget()
        self.solution_tree.solution_selected.connect(self._on_solution_selected)
        left_splitter.addWidget(self.solution_tree)
        
        # Variable table
        self.variable_table = HierarchicalVariableTableWidget()
        left_splitter.addWidget(self.variable_table)
        
        left_splitter.setSizes([400, 400])
        
        # Right panel - 3D viewer
        self.viewer_3d = Enhanced3DViewer()
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self.viewer_3d)
        main_splitter.setSizes([600, 700])
        
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)
    
    def _setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Workspace", self)
        new_action.triggered.connect(self._new_workspace)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save Solution", self)
        save_action.triggered.connect(self._save_solution)
        file_menu.addAction(save_action)
        
        load_action = QAction("Load Solution", self)
        load_action.triggered.connect(self._load_solution)
        file_menu.addAction(load_action)
        
        # Create menu
        create_menu = menubar.addMenu("Create")
        
        create_box_action = QAction("Box Solution", self)
        create_box_action.triggered.connect(self._create_box_solution)
        create_menu.addAction(create_box_action)
        
        create_edge_action = QAction("Edge Banding Solution", self)
        create_edge_action.triggered.connect(self._create_edge_banding)
        create_menu.addAction(create_edge_action)
        
        # Variables menu
        variables_menu = menubar.addMenu("Variables")
        
        test_references_action = QAction("Test Variable References", self)
        test_references_action.triggered.connect(self._test_variable_references)
        variables_menu.addAction(test_references_action)
        
        show_global_registry_action = QAction("Show Global Solution Registry", self)
        show_global_registry_action.triggered.connect(self._show_global_registry)
        variables_menu.addAction(show_global_registry_action)
        
        # Integration menu
        integration_menu = menubar.addMenu("Integration")
        
        apply_action = QAction("Apply Selected to Target", self)
        apply_action.triggered.connect(self._apply_solution)
        integration_menu.addAction(apply_action)
    
    def _show_welcome(self):
        welcome_text = """
Visual Solving MVP - Hierarchical Variables!

🎯 NEW ADDRESSING SYSTEM:
• Each Solution gets unique number: #1, #2, #3...
• Variables are hierarchical: #1.1, #1.2, #1.3...
• Named references: #1.length, #1.width, #1.height
• Aliases work: #1.L, #1.W, #1.H
• Local access: 'length', 'L' (within Solution)

🚀 Try:
1. Create → Box Solution (becomes Solution #1)
2. Create → Edge Banding Solution (becomes Solution #2)  
3. Variables → Test Variable References
4. Integration → Apply Selected to Target

📋 Variable Reference Examples:
• #1.1 or #1.length (full reference)
• length or L (local reference)
• Variables → Test Variable References (interactive testing)
        """
        self.viewer_3d.solution_info.setText(welcome_text)
    
    def _new_workspace(self):
        try:
            if CORE_AVAILABLE:
                self.workspace = Part3DSpace("Main Workspace")
                solution_number_manager.reset()  # Сброс нумерации
            self.solution_tree.clear_solutions()
            self.variable_table.clear_variables()
            self.current_solution = None
            self._show_welcome()
        except Exception as e:
            print(f"Ошибка создания workspace: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create workspace: {str(e)}")
    
    def _create_box_solution(self):
        try:
            if not CORE_AVAILABLE:
                QMessageBox.warning(self, "Warning", "Core system not available")
                return
            
            dialog = CreateBoxDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                solution = dialog.get_solution()
                
                if solution:
                    solution.place_in_space(self.workspace)
                    self.solution_tree.add_solution(solution)
                    self._on_solution_selected(solution)
                    
                    # Показываем созданные переменные
                    solution.debug_variables()
                else:
                    QMessageBox.warning(self, "Warning", "Failed to create solution")
                
        except Exception as e:
            print(f"Критическая ошибка в _create_box_solution: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Critical error: {str(e)}")
    
    def _create_edge_banding(self):
        try:
            if not CORE_AVAILABLE:
                QMessageBox.warning(self, "Warning", "Core system not available")
                return
            
            # Простой диалог для демонстрации
            from visual_solving_ui_fixed import CreateEdgeBandingDialog
            dialog = CreateEdgeBandingDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                solution = dialog.get_solution()
                if solution:
                    solution.place_in_space(self.workspace)
                    self.solution_tree.add_solution(solution)
                    self._on_solution_selected(solution)
                    
                    # Показываем созданные переменные
                    solution.debug_variables()
        except Exception as e:
            print(f"Ошибка в _create_edge_banding: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to create edge banding: {str(e)}")
    
    def _test_variable_references(self):
        """Открыть диалог тестирования ссылок на переменные"""
        if not self.current_solution:
            QMessageBox.warning(self, "Warning", "Please select a solution first")
            return
        
        dialog = VariableReferenceDialog(self.current_solution, self)
        dialog.exec()
    
    def _show_global_registry(self):
        """Показать глобальный реестр Solution"""
        registry_info = "GLOBAL SOLUTION REGISTRY\n"
        registry_info += "=" * 40 + "\n"
        registry_info += f"Next number: #{solution_number_manager._next_number}\n\n"
        
        for number, solution in solution_number_manager._solution_registry.items():
            registry_info += f"#{number}: {solution.name} ({type(solution).__name__})\n"
            registry_info += f"   UUID: {solution.solution_id}\n"
            registry_info += f"   Variables: {len(solution.variables.get_all_variables())}\n\n"
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Global Solution Registry")
        msg.setText(registry_info)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        msg.exec()
    
    def _apply_solution(self):
        try:
            if not self.current_solution:
                QMessageBox.warning(self, "Warning", "Please select a solution first")
                return
            
            # Найти цель для применения
            target_box = None
            for solution in self.workspace.solutions:
                if isinstance(solution, BoxSolution) and solution != self.current_solution:
                    target_box = solution
                    break
            
            if not target_box:
                QMessageBox.warning(self, "Warning", "No target box solution found")
                return
            
            # Применить решение
            result = self.current_solution.apply_to(target_box)
            result.place_in_space(self.workspace)
            
            self.solution_tree.add_solution(result)
            self._on_solution_selected(result)
            
            # Показываем информацию о результате
            info = f"Applied #{self.current_solution.solution_number} to #{target_box.solution_number}\n"
            info += f"Result: #{result.solution_number}: {result.name}"
            QMessageBox.information(self, "Success", info)
            
        except Exception as e:
            print(f"Ошибка в _apply_solution: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to apply solution: {str(e)}")
    
    def _save_solution(self):
        try:
            if not self.current_solution:
                QMessageBox.warning(self, "Warning", "Please select a solution to save")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Solution", f"{self.current_solution.name}.vsol", 
                "Visual Solving Files (*.vsol)"
            )
            
            if filename:
                VsolFormat.save_solution(self.current_solution, filename)
                QMessageBox.information(self, "Success", f"Solution #{self.current_solution.solution_number} saved to {filename}")
                
        except Exception as e:
            print(f"Ошибка в _save_solution: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
    
    def _load_solution(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Load Solution", "", "Visual Solving Files (*.vsol)"
            )
            
            if filename:
                solution = VsolFormat.load_solution(filename)
                solution.place_in_space(self.workspace)
                self.solution_tree.add_solution(solution)
                self._on_solution_selected(solution)
                
                QMessageBox.information(self, "Success", f"Solution #{solution.solution_number} loaded from {filename}")
                
        except Exception as e:
            print(f"Ошибка в _load_solution: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")
    
    def _on_solution_selected(self, solution: Solution):
        try:
            print(f"Solution выбран: #{solution.solution_number}: {solution.name}")
            self.current_solution = solution
            self.variable_table.update_variables(solution)
            self.viewer_3d.update_solution(solution)
        except Exception as e:
            print(f"Ошибка в _on_solution_selected: {e}")
            traceback.print_exc()

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        if not CORE_AVAILABLE:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Core Error")
            msg.setText("Hierarchical core system not found")
            msg.setInformativeText("visual_solving_hierarchical.py not found or has errors")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Критическая ошибка запуска: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
