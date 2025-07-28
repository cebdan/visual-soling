# Visual Solving V2 - Complete Startup System
# Стартовые диалоги: New/Open Solution + Global Variables
# Сохраните этот файл как: complete_startup_system_v2.py

import sys
import re
from typing import Dict, List, Optional, Set
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFrame, QGridLayout, QWidget,
                            QFileDialog, QMessageBox, QSpacerItem, QSizePolicy,
                            QLineEdit, QComboBox, QTextEdit, QFormLayout,
                            QGroupBox, QListWidget, QListWidgetItem, QCheckBox,
                            QDoubleSpinBox, QSpinBox, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QStringListModel
from PyQt6.QtGui import QFont, QPixmap, QPalette, QIcon, QColor

# =============================================================================
# Глобальные переменные системы
# =============================================================================

class GlobalVariable:
    """Глобальная переменная системы"""
    
    def __init__(self, name: str, value: any, var_type: str, description: str = ""):
        self.name = name
        self.value = value
        self.var_type = var_type  # "number", "text", "boolean"
        self.description = description
        self.created_time = None
    
    @property
    def display_name(self) -> str:
        """Отображаемое имя для UI"""
        return f"{self.name} ({self.var_type})"

class GlobalVariableRegistry:
    """Реестр глобальных переменных"""
    
    def __init__(self):
        self.variables: Dict[str, GlobalVariable] = {}
        self._load_default_variables()
    
    def _load_default_variables(self):
        """Загрузить стандартные глобальные переменные"""
        defaults = [
            ("panel_thickness", 18.0, "number", "Standard panel thickness in mm"),
            ("edge_thickness", 2.0, "number", "Standard edge banding thickness in mm"),
            ("default_material", "chipboard", "text", "Default panel material"),
            ("use_metric", True, "boolean", "Use metric units"),
        ]
        
        for name, value, var_type, desc in defaults:
            self.variables[name] = GlobalVariable(name, value, var_type, desc)
    
    def add_variable(self, name: str, value: any, var_type: str, description: str = "") -> bool:
        """Добавить глобальную переменную"""
        if self.is_name_taken(name):
            return False
        
        if not self.validate_variable_name(name):
            return False
        
        self.variables[name] = GlobalVariable(name, value, var_type, description)
        return True
    
    def is_name_taken(self, name: str) -> bool:
        """Проверить, занято ли имя"""
        return name.lower() in [v.name.lower() for v in self.variables.values()]
    
    def validate_variable_name(self, name: str) -> bool:
        """Валидация имени переменной"""
        if not name or name.startswith(' ') or name.endswith(' '):
            return False
        
        # Должно начинаться с буквы или цифры
        if not re.match(r'^[a-zA-Z0-9]', name):
            return False
        
        # Может содержать буквы, цифры, подчеркивания
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return False
        
        return True
    
    def get_all_variables(self) -> List[GlobalVariable]:
        """Получить все глобальные переменные"""
        return list(self.variables.values())
    
    def get_variable(self, name: str) -> Optional[GlobalVariable]:
        """Получить переменную по имени"""
        return self.variables.get(name)

# Глобальный реестр переменных
global_variable_registry = GlobalVariableRegistry()

# =============================================================================
# Утилиты валидации
# =============================================================================

class ValidationUtils:
    """Утилиты для валидации названий"""
    
    @staticmethod
    def validate_solution_name(name: str) -> tuple[bool, str]:
        """Валидация имени решения"""
        if not name or not name.strip():
            return False, "Name cannot be empty"
        
        name = name.strip()
        
        if name.startswith(' '):
            return False, "Name cannot start with space"
        
        if not re.match(r'^[a-zA-Z0-9]', name):
            return False, "Name must start with letter or digit"
        
        # Проверяем недопустимые символы для V2 системы
        if '@' in name or '.' in name:
            return False, "Name cannot contain @ or . symbols (reserved for V2 syntax)"
        
        return True, ""
    
    @staticmethod
    def validate_variable_name(name: str) -> tuple[bool, str]:
        """Валидация имени переменной"""
        if not name or not name.strip():
            return False, "Variable name cannot be empty"
        
        name = name.strip()
        
        if name.startswith(' '):
            return False, "Variable name cannot start with space"
        
        if not re.match(r'^[a-zA-Z0-9]', name):
            return False, "Variable name must start with letter or digit"
        
        if '@' in name or '.' in name:
            return False, "Variable name cannot contain @ or . symbols"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return False, "Variable name can only contain letters, digits and underscores"
        
        return True, ""

# =============================================================================
# Стартовый диалог
# =============================================================================

class StartupDialog(QDialog):
    """Стартовый диалог выбора действия"""
    
    # Сигналы для результатов
    new_solution_requested = pyqtSignal()
    open_solution_requested = pyqtSignal(str)
    global_variables_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visual Solving V2 - Welcome")
        self.setFixedSize(700, 500)
        self.setModal(True)
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        
        self._setup_ui()
        self._setup_styles()
        
        self.selected_action = None
        self.selected_file = None
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок
        self._create_header(main_layout)
        
        # Основные кнопки действий
        self._create_action_buttons(main_layout)
        
        # Кнопка глобальных переменных
        self._create_global_variables_section(main_layout)
        
        # Последние файлы
        self._create_recent_files(main_layout)
        
        # Нижние кнопки
        self._create_bottom_buttons(main_layout)
        
        self.setLayout(main_layout)
    
    def _create_header(self, layout):
        """Создать заголовок"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout()
        
        title_label = QLabel("Visual Solving V2")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Revolutionary Variable System")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        version_label = QLabel("Version 2.0 - New Syntax: variable@solution")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addWidget(version_label)
        header_frame.setLayout(header_layout)
        
        layout.addWidget(header_frame)
    
    def _create_action_buttons(self, layout):
        """Создать основные кнопки действий"""
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_layout = QGridLayout()
        actions_layout.setSpacing(15)
        
        # Кнопка New Solution
        new_btn = self._create_action_button(
            "🆕 New Solution",
            "Create new furniture solution\nwith V2 variable system",
            self._on_new_solution
        )
        new_btn.setObjectName("newSolutionBtn")
        
        # Кнопка Open Solution
        open_btn = self._create_action_button(
            "📂 Open Solution", 
            "Open existing .vsol file\nor import from STEP/DXF",
            self._on_open_solution
        )
        open_btn.setObjectName("openSolutionBtn")
        
        actions_layout.addWidget(new_btn, 0, 0)
        actions_layout.addWidget(open_btn, 0, 1)
        
        actions_frame.setLayout(actions_layout)
        layout.addWidget(actions_frame)
    
    def _create_global_variables_section(self, layout):
        """Создать секцию глобальных переменных"""
        global_frame = QFrame()
        global_frame.setObjectName("globalFrame")
        global_layout = QHBoxLayout()
        
        # Информация о глобальных переменных
        info_layout = QVBoxLayout()
        
        global_label = QLabel("🌐 Global Variables")
        global_label.setObjectName("globalLabel")
        
        count_label = QLabel(f"Current: {len(global_variable_registry.get_all_variables())} variables")
        count_label.setObjectName("countLabel")
        
        info_layout.addWidget(global_label)
        info_layout.addWidget(count_label)
        
        # Кнопка управления
        global_btn = QPushButton("Manage Global Variables")
        global_btn.setObjectName("globalBtn")
        global_btn.clicked.connect(self._on_global_variables)
        global_btn.setMinimumHeight(50)
        
        global_layout.addLayout(info_layout)
        global_layout.addStretch()
        global_layout.addWidget(global_btn)
        
        global_frame.setLayout(global_layout)
        layout.addWidget(global_frame)
    
    def _create_action_button(self, title: str, description: str, callback):
        """Создать кнопку действия"""
        btn = QPushButton()
        btn.clicked.connect(callback)
        btn.setMinimumHeight(100)
        btn.setMinimumWidth(250)
        
        btn_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setObjectName("actionButtonTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc_label = QLabel(description)
        desc_label.setObjectName("actionButtonDesc")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        
        btn_layout.addWidget(title_label)
        btn_layout.addWidget(desc_label)
        
        btn.setLayout(btn_layout)
        return btn
    
    def _create_recent_files(self, layout):
        """Создать секцию последних файлов"""
        recent_frame = QFrame()
        recent_frame.setObjectName("recentFrame")
        recent_layout = QVBoxLayout()
        
        recent_label = QLabel("📁 Recent Solutions")
        recent_label.setObjectName("recentLabel")
        recent_layout.addWidget(recent_label)
        
        # Список последних файлов (заглушка)
        recent_list = QListWidget()
        recent_list.setMaximumHeight(80)
        recent_list.addItem("No recent files")
        recent_layout.addWidget(recent_list)
        
        recent_frame.setLayout(recent_layout)
        layout.addWidget(recent_frame)
    
    def _create_bottom_buttons(self, layout):
        """Создать нижние кнопки"""
        button_layout = QHBoxLayout()
        
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self._on_help)
        
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(help_btn)
        button_layout.addStretch()
        button_layout.addWidget(exit_btn)
        
        layout.addLayout(button_layout)
    
    def _setup_styles(self):
        """Настройка стилей"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            
            #titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px;
            }
            
            #subtitleLabel {
                font-size: 14px;
                color: #7f8c8d;
                margin: 5px;
            }
            
            #versionLabel {
                font-size: 11px;
                color: #95a5a6;
                margin: 5px;
            }
            
            #newSolutionBtn, #openSolutionBtn {
                background-color: #3498db;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }
            
            #newSolutionBtn:hover, #openSolutionBtn:hover {
                background-color: #2980b9;
            }
            
            #globalBtn {
                background-color: #e74c3c;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            
            #globalBtn:hover {
                background-color: #c0392b;
            }
            
            #globalLabel {
                font-size: 14px;
                font-weight: bold;
                color: #e74c3c;
            }
            
            #recentLabel {
                font-size: 12px;
                font-weight: bold;
                color: #7f8c8d;
            }
            
            #actionButtonTitle {
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            
            #actionButtonDesc {
                font-size: 11px;
                color: #ecf0f1;
            }
            
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                padding: 10px;
            }
        """)
    
    def _on_new_solution(self):
        """Обработка New Solution"""
        self.selected_action = "new"
        self.accept()
        self.new_solution_requested.emit()
    
    def _on_open_solution(self):
        """Обработка Open Solution"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Solution", "", 
            "Visual Solving Files (*.vsol);;STEP Files (*.step *.stp);;DXF Files (*.dxf);;All Files (*)"
        )
        
        if filename:
            self.selected_action = "open"
            self.selected_file = filename
            self.accept()
            self.open_solution_requested.emit(filename)
    
    def _on_global_variables(self):
        """Обработка Global Variables"""
        self.selected_action = "global_vars"
        self.accept()
        self.global_variables_requested.emit()
    
    def _on_help(self):
        """Показать справку"""
        help_text = """Visual Solving V2 - Help

NEW SOLUTION:
Create new furniture solution with revolutionary V2 variable system.

OPEN SOLUTION:
Open existing .vsol files or import from STEP/DXF formats.

GLOBAL VARIABLES:
Manage system-wide variables that can be accessed from any solution:
• variable@SolutionName (write access)
• variable.SolutionName (read access)

V2 SYNTAX FEATURES:
• Intuitive addressing: length@panel=600
• Natural reading: width.panel
• Safe aliases: L, W, H (isolated per solution)
• Readable formulas: width.panel - 2*thickness.edge

NAMING RULES:
• Must start with letter or digit
• Cannot start with space
• Cannot contain @ or . symbols
• Global variables must be unique
"""
        
        QMessageBox.information(self, "Help", help_text)

# =============================================================================
# Диалог создания нового решения
# =============================================================================

class NewSolutionDialog(QDialog):
    """Диалог создания нового решения"""
    
    global_variables_requested = pyqtSignal()  # Сигнал для глобальных переменных
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties of the new solution")
        self.setFixedSize(500, 450)
        self.setModal(True)
        
        self._setup_ui()
        self._setup_validation()
        
        self.solution_data = None
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Create New Solution")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Форма
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name of solution (обязательное)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter solution name (required)")
        self.name_edit.textChanged.connect(self._validate_form)
        
        name_label = QLabel("Name of solution *")
        name_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(name_label, self.name_edit)
        
        # Solution type (обязательное)
        self.type_combo = QComboBox()
        self.type_combo.addItem("Model Solution")
        # Можно добавить другие типы позже
        self.type_combo.currentTextChanged.connect(self._validate_form)
        
        type_label = QLabel("Solution type *")
        type_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(type_label, self.type_combo)
        
        # Description (необязательное)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter solution description (optional)")
        form_layout.addRow("Description:", self.description_edit)
        
        # Comment (необязательное)
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText("Enter additional comments (optional)")
        form_layout.addRow("Comment:", self.comment_edit)
        
        layout.addLayout(form_layout)
        
        # Информация о валидации
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: red; font-size: 11px;")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)
        
        # Информация о глобальных переменных
        global_info_frame = QFrame()
        global_info_frame.setStyleSheet("background-color: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; padding: 8px;")
        global_info_layout = QHBoxLayout()
        
        global_count = len(global_variable_registry.get_all_variables())
        global_info_label = QLabel(f"🌐 Global Variables Available: {global_count}")
        global_info_label.setStyleSheet("color: #2c3e50; font-size: 11px; font-weight: bold;")
        
        global_info_layout.addWidget(global_info_label)
        global_info_layout.addStretch()
        global_info_frame.setLayout(global_info_layout)
        layout.addWidget(global_info_frame)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        # Кнопка Global Variables (слева)
        global_vars_button = QPushButton("🌐 Global Variables")
        global_vars_button.clicked.connect(self._on_global_variables)
        global_vars_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # Основные кнопки (справа)
        self.ok_button = QPushButton("Create Solution")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self._on_create)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        button_layout.addWidget(global_vars_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _setup_validation(self):
        """Настройка валидации"""
        # Начальная валидация
        self._validate_form()
    
    def _validate_form(self):
        """Валидация формы"""
        name = self.name_edit.text().strip()
        solution_type = self.type_combo.currentText()
        
        # Проверка имени
        is_name_valid, name_error = ValidationUtils.validate_solution_name(name)
        
        # Проверка типа решения
        is_type_valid = bool(solution_type)
        
        # Общая валидность
        is_valid = is_name_valid and is_type_valid
        
        # Обновляем UI
        if not is_name_valid and name:
            self.validation_label.setText(f"Name error: {name_error}")
        elif not name:
            self.validation_label.setText("Name is required")
        else:
            self.validation_label.setText("")
        
        self.ok_button.setEnabled(is_valid)
        
        # Подсветка полей с ошибками
        if name and not is_name_valid:
            self.name_edit.setStyleSheet("border: 2px solid red;")
        else:
            self.name_edit.setStyleSheet("")
    
    def _on_create(self):
        """Создание решения"""
        self.solution_data = {
            'name': self.name_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'description': self.description_edit.toPlainText().strip(),
            'comment': self.comment_edit.toPlainText().strip()
        }
        
        self.accept()
    
    def _on_global_variables(self):
        """Открыть диалог глобальных переменных"""
        self.global_variables_requested.emit()

# =============================================================================
# Диалог управления глобальными переменными
# =============================================================================

class GlobalVariablesDialog(QDialog):
    """Диалог управления глобальными переменными"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Variables Manager")
        self.setFixedSize(700, 500)
        self.setModal(True)
        
        self._setup_ui()
        self._refresh_variables_list()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Global Variables Manager")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Информация
        info_label = QLabel("Global variables can be accessed from any solution using V2 syntax:\n• variable@SolutionName (write) • variable.SolutionName (read)")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-bottom: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Основной контент
        content_layout = QHBoxLayout()
        
        # Левая панель - список переменных
        left_panel = self._create_variables_list()
        content_layout.addWidget(left_panel, 2)
        
        # Правая панель - создание/редактирование
        right_panel = self._create_edit_panel()
        content_layout.addWidget(right_panel, 1)
        
        layout.addLayout(content_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _create_variables_list(self):
        """Создать панель списка переменных"""
        group = QGroupBox("Existing Global Variables")
        layout = QVBoxLayout()
        
        self.variables_list = QListWidget()
        self.variables_list.itemSelectionChanged.connect(self._on_variable_selected)
        layout.addWidget(self.variables_list)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected_variable)
        delete_btn.setStyleSheet("background-color: #e74c3c; color: white; border: none; padding: 5px; border-radius: 3px;")
        
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_edit_panel(self):
        """Создать панель редактирования"""
        group = QGroupBox("Add New Global Variable")
        layout = QVBoxLayout()
        
        # Форма создания
        form_layout = QFormLayout()
        
        # Имя переменной
        self.var_name_edit = QLineEdit()
        self.var_name_edit.setPlaceholderText("variable_name")
        self.var_name_edit.textChanged.connect(self._validate_new_variable)
        form_layout.addRow("Name *:", self.var_name_edit)
        
        # Тип переменной
        self.var_type_combo = QComboBox()
        self.var_type_combo.addItems(["number", "text", "boolean"])
        self.var_type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("Type *:", self.var_type_combo)
        
        # Значение переменной
        self.var_value_widget = QLineEdit()  # Будет заменяться в зависимости от типа
        self.var_value_widget.setPlaceholderText("Enter value")
        form_layout.addRow("Value *:", self.var_value_widget)
        
        # Описание
        self.var_desc_edit = QLineEdit()
        self.var_desc_edit.setPlaceholderText("Optional description")
        form_layout.addRow("Description:", self.var_desc_edit)
        
        layout.addLayout(form_layout)
        
        # Валидация
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: red; font-size: 10px;")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)
        
        # Кнопка добавления
        self.add_button = QPushButton("Add Variable")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self._add_variable)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        layout.addWidget(self.add_button)
        
        group.setLayout(layout)
        return group
    
    def _refresh_variables_list(self):
        """Обновить список переменных"""
        self.variables_list.clear()
        
        for var in global_variable_registry.get_all_variables():
            item_text = f"{var.name} ({var.var_type}) = {var.value}"
            if var.description:
                item_text += f"\n    {var.description}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, var.name)
            self.variables_list.addItem(item)
    
    def _on_variable_selected(self):
        """Обработка выбора переменной"""
        # Можно добавить логику для редактирования выбранной переменной
        pass
    
    def _on_type_changed(self):
        """Обработка изменения типа переменной"""
        var_type = self.var_type_combo.currentText()
        
        # Удаляем старый виджет
        if hasattr(self, 'var_value_widget') and self.var_value_widget:
            self.var_value_widget.deleteLater()
        
        # Создаём новый виджет в зависимости от типа
        if var_type == "number":
            self.var_value_widget = QDoubleSpinBox()
            self.var_value_widget.setRange(-999999, 999999)
            self.var_value_widget.setDecimals(3)
            self.var_value_widget.setValue(0.0)
        elif var_type == "boolean":
            self.var_value_widget = QCheckBox("True/False")
        else:  # text
            self.var_value_widget = QLineEdit()
            self.var_value_widget.setPlaceholderText("Enter text value")
        
        # Добавляем в форму (заменяем в layout)
        form_layout = self.findChild(QFormLayout)
        if form_layout:
            form_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.var_value_widget)
        
        self._validate_new_variable()
    
    def _validate_new_variable(self):
        """Валидация новой переменной"""
        name = self.var_name_edit.text().strip()
        
        # Проверка имени
        is_valid, error = ValidationUtils.validate_variable_name(name)
        
        # Проверка уникальности
        if is_valid and global_variable_registry.is_name_taken(name):
            is_valid = False
            error = "Variable name already exists"
        
        # Проверка значения
        has_value = True
        if isinstance(self.var_value_widget, QLineEdit):
            has_value = bool(self.var_value_widget.text().strip())
        
        is_valid = is_valid and has_value
        
        # Обновляем UI
        if not is_valid and name:
            self.validation_label.setText(error)
        elif not name:
            self.validation_label.setText("Variable name is required")
        elif not has_value:
            self.validation_label.setText("Value is required")
        else:
            self.validation_label.setText("")
        
        self.add_button.setEnabled(is_valid)
        
        # Подсветка ошибок
        if name and not ValidationUtils.validate_variable_name(name)[0]:
            self.var_name_edit.setStyleSheet("border: 2px solid red;")
        elif name and global_variable_registry.is_name_taken(name):
            self.var_name_edit.setStyleSheet("border: 2px solid orange;")
        else:
            self.var_name_edit.setStyleSheet("")
    
    def _add_variable(self):
        """Добавить новую переменную"""
        name = self.var_name_edit.text().strip()
        var_type = self.var_type_combo.currentText()
        description = self.var_desc_edit.text().strip()
        
        # Получаем значение в зависимости от типа
        if var_type == "number":
            value = self.var_value_widget.value()
        elif var_type == "boolean":
            value = self.var_value_widget.isChecked()
        else:  # text
            value = self.var_value_widget.text().strip()
        
        # Добавляем переменную
        success = global_variable_registry.add_variable(name, value, var_type, description)
        
        if success:
            # Очищаем форму
            self.var_name_edit.clear()
            self.var_desc_edit.clear()
            self._on_type_changed()  # Сбрасываем значение
            
            # Обновляем список
            self._refresh_variables_list()
            
            QMessageBox.information(self, "Success", f"Global variable '{name}' created successfully!")
        else:
            QMessageBox.warning(self, "Error", "Failed to create variable")
    
    def _delete_selected_variable(self):
        """Удалить выбранную переменную"""
        current_item = self.variables_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a variable to delete")
            return
        
        var_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete global variable '{var_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if var_name in global_variable_registry.variables:
                del global_variable_registry.variables[var_name]
                self._refresh_variables_list()
                QMessageBox.information(self, "Success", f"Variable '{var_name}' deleted")

# =============================================================================
# Диспетчер стартовой системы
# =============================================================================

class StartupManager:
    """Менеджер стартовой системы"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.main_window = None
    
    def show_startup_dialog(self):
        """Показать стартовый диалог"""
        dialog = StartupDialog(self.parent)
        
        # Подключаем сигналы
        dialog.new_solution_requested.connect(self._handle_new_solution)
        dialog.open_solution_requested.connect(self._handle_open_solution)
        dialog.global_variables_requested.connect(self._handle_global_variables)
        
        return dialog.exec()
    
    def _handle_new_solution(self):
        """Обработка создания нового решения"""
        dialog = NewSolutionDialog(self.parent)
        
        # Подключаем сигнал для глобальных переменных
        dialog.global_variables_requested.connect(
            lambda: self._handle_global_variables_from_properties(dialog)
        )
        
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            solution_data = dialog.solution_data
            print(f"Creating new solution: {solution_data}")
            
            # Здесь должен открываться главный интерфейс
            # self._open_main_window(solution_data)
            
            return solution_data
        else:
            # Пользователь отменил создание решения
            return None
    
    def _handle_open_solution(self, filename: str):
        """Обработка открытия решения"""
        print(f"Opening solution from: {filename}")
        
        # Здесь должна быть логика загрузки файла
        # self._open_main_window(loaded_solution)
        
        return filename
    
    def _handle_global_variables(self):
        """Обработка управления глобальными переменными"""
        dialog = GlobalVariablesDialog(self.parent)
        dialog.exec()
        
        # После закрытия диалога возвращаемся к стартовому экрану
        self.show_startup_dialog()
    
    def _handle_global_variables_from_properties(self, properties_dialog):
        """Обработка глобальных переменных из Properties dialog"""
        # Скрываем Properties dialog
        properties_dialog.hide()
        
        # Показываем Global Variables dialog
        global_vars_dialog = GlobalVariablesDialog(self.parent)
        global_vars_dialog.exec()
        
        # Обновляем информацию о глобальных переменных в Properties dialog
        self._update_global_variables_info(properties_dialog)
        
        # Возвращаем Properties dialog
        properties_dialog.show()
    
    def _update_global_variables_info(self, properties_dialog):
        """Обновить информацию о глобальных переменных в Properties dialog"""
        # Находим и обновляем label с информацией о глобальных переменных
        for child in properties_dialog.findChildren(QLabel):
            if "Global Variables Available:" in child.text():
                global_count = len(global_variable_registry.get_all_variables())
                child.setText(f"🌐 Global Variables Available: {global_count}")
                break

# =============================================================================
# Демонстрация и интеграция
# =============================================================================

def demo_startup_system():
    """Демонстрация стартовой системы"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    manager = StartupManager()
    result = manager.show_startup_dialog()
    
    print(f"Startup result: {result}")
    
    sys.exit(app.exec())

def integrate_with_main_window():
    """Пример интеграции с главным окном программы"""
    
    def main():
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Показываем стартовую систему
        startup_manager = StartupManager()
        startup_result = startup_manager.show_startup_dialog()
        
        if startup_result == QDialog.DialogCode.Accepted:
            # Здесь должно быть создание и показ главного окна программы
            print("Opening main application window...")
            
            # Пример интеграции:
            # try:
            #     from visual_solving_ui_advanced_v2 import V2AdvancedMainWindow
            #     main_window = V2AdvancedMainWindow()
            #     main_window.show()
            #     app.exec()
            # except ImportError:
            #     print("Main window module not found")
        else:
            print("Application startup cancelled")
        
        sys.exit(0)
    
    return main

if __name__ == "__main__":
    # Запуск с интеграцией в главное окно
    main_function = integrate_with_main_window()
    main_function()
    
    # Или для демонстрации только стартовой системы:
    # demo_startup_system()
