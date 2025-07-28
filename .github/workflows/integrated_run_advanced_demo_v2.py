#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visual Solving Advanced Demo V2 - Интегрированный запуск с новой стартовой системой
Полная интеграция стартовых диалогов с основной программой
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Проверка зависимостей"""
    missing = []
    
    try:
        import PyQt6
        print("✅ PyQt6 найден")
    except ImportError:
        missing.append("PyQt6")
        print("❌ PyQt6 не найден")
    
    try:
        import numpy
        print("✅ NumPy найден")
    except ImportError:
        missing.append("numpy") 
        print("❌ NumPy не найден")
    
    try:
        from variable_system_v2 import ExpressionParser, V2FormulaEvaluator
        print("✅ Variable System V2 найден")
        v2_available = True
    except ImportError as e:
        print(f"❌ Variable System V2 не найден: {e}")
        v2_available = False
    
    try:
        from visual_solving_advanced_v2 import (
            HybridBoxSolution, v2_solution_manager, 
            demo_hybrid_system, demo_expression_parsing
        )
        print("✅ Advanced V2 ядро найдено")
        advanced_v2_available = True
    except ImportError as e:
        print(f"❌ Advanced V2 ядро не найдено: {e}")
        advanced_v2_available = False
    
    try:
        from complete_startup_system_v2 import (
            StartupManager, NewSolutionDialog, GlobalVariablesDialog,
            global_variable_registry
        )
        print("✅ Startup System V2 найден")
        startup_available = True
    except ImportError as e:
        print(f"❌ Startup System V2 не найден: {e}")
        startup_available = False
    
    try:
        from visual_solving_ui_advanced_v2 import V2AdvancedMainWindow
        print("✅ UI Advanced V2 найден")
        ui_available = True
    except ImportError as e:
        print(f"❌ UI Advanced V2 не найден: {e}")
        ui_available = False
    
    return missing, v2_available and advanced_v2_available and startup_available and ui_available

def run_console_demo():
    """Консольная демонстрация новой системы V2 (без GUI)"""
    try:
        from visual_solving_advanced_v2 import (
            HybridBoxSolution, HybridEdgeBandingSolution, Part3DSpace,
            v2_solution_manager, V2GlobalVariableRegistry,
            demo_hybrid_system, demo_expression_parsing,
            ExpressionParser
        )
        from variable_system_v2 import demo_new_syntax
    except ImportError as e:
        print(f"❌ Ошибка импорта V2 ядра: {e}")
        print("Убедитесь, что файлы variable_system_v2.py и visual_solving_advanced_v2.py находятся в каталоге")
        return False
    
    print("=" * 80)
    print("VISUAL SOLVING ADVANCED V2 - КОНСОЛЬНАЯ ДЕМОНСТРАЦИЯ")
    print("=" * 80)
    
    print("🚀 РЕВОЛЮЦИОННЫЕ ВОЗМОЖНОСТИ:")
    print("   • Новая адресация: variable@solution=value")
    print("   • Чтение через точку: a=variable.solution")
    print("   • Локальные алиасы: L, W, H (без @ и точки)")
    print("   • Читаемые формулы: width.panel - 2*thickness.edge")
    print("   • Обратная совместимость: #1.length по-прежнему работает")
    print("   • Безопасность: алиасы изолированы в Solution")
    print()
    
    print("1. НОВАЯ СИСТЕМА ПЕРЕМЕННЫХ V2")
    print("-" * 35)
    demo_new_syntax()
    print()
    
    print("2. ГИБРИДНАЯ СИСТЕМА (V2 + Legacy)")
    print("-" * 40)
    demo_hybrid_system()
    print()
    
    print("3. ПАРСИНГ НОВЫХ ВЫРАЖЕНИЙ")
    print("-" * 30)
    demo_expression_parsing()
    print()
    
    print("4. ГЛОБАЛЬНЫЙ РЕЕСТР V2")
    print("-" * 25)
    demo_global_registry_v2()
    print()
    
    print("5. ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ V2")
    print("-" * 38)
    demo_interactive_testing_v2()
    
    print("\n" + "=" * 80)
    print("КОНСОЛЬНАЯ ДЕМОНСТРАЦИЯ V2 ЗАВЕРШЕНА")
    print("=" * 80)
    
    print("\n🎯 КЛЮЧЕВЫЕ ДОСТИЖЕНИЯ V2:")
    print("   ✅ Интуитивная адресация: variable@solution")
    print("   ✅ Естественное чтение: variable.solution")
    print("   ✅ Безопасные алиасы: изолированы в Solution")
    print("   ✅ Читаемые формулы: width.panel - 2*thickness.edge")
    print("   ✅ Обратная совместимость: #1.length работает")
    print("   ✅ Валидация: @ и точка запрещены в алиасах")
    
    print("\n📋 ПРИМЕРЫ НОВОГО СИНТАКСИСА:")
    print("   length@box=600                           # Установка значения")
    print("   width@result=width.panel - 2*thickness.edge  # Формула")
    print("   a=volume.box                             # Чтение значения")
    print("   L=600                                    # Локальный алиас")
    
    return True

def demo_global_registry_v2():
    """Демонстрация глобального реестра V2"""
    from visual_solving_advanced_v2 import V2GlobalVariableRegistry
    
    print("Все переменные в системе V2:")
    variables_info = V2GlobalVariableRegistry.get_all_variables_info()
    
    for var_info in variables_info:
        solution_name = var_info.get('solution_name', 'Unknown')
        print(f"  {var_info.get('new_write_id', '')}: {var_info.get('name', '')}")
        
        if var_info.get('is_formula', False):
            formula = var_info.get('formula', '')
            computed = var_info.get('computed_value', 0)
            print(f"    Formula: {formula} → {computed}")
        else:
            value = var_info.get('value', '')
            print(f"    Value: {value}")
        
        # Показываем все способы обращения
        legacy_id = var_info.get('legacy_full_id', '')
        read_id = var_info.get('new_read_id', '')
        if legacy_id:
            print(f"    Legacy: {legacy_id}")
        if read_id:
            print(f"    Read: {read_id}")
    
    print(f"\nВсего переменных: {len(variables_info)}")

def demo_interactive_testing_v2():
    """Интерактивное тестирование новых выражений"""
    try:
        from visual_solving_advanced_v2 import (
            HybridBoxSolution, HybridEdgeBandingSolution,
            v2_solution_manager, ExpressionParser
        )
        
        print("🧪 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ V2")
        print("=" * 35)
        
        # Создаем тестовые решения
        v2_solution_manager.reset()
        panel = HybridBoxSolution("panel", 600, 400, 18)
        edge = HybridEdgeBandingSolution("edge", "white", 2.0, ["top"])
        
        print("Созданы тестовые решения:")
        print(f"  panel: length@panel={panel.length}")
        print(f"  edge: thickness@edge={edge.get_variable_by_reference('thickness').value}")
        
        print("\nДоступные переменные:")
        for var in panel.get_all_variables():
            print(f"  {var.new_write_id}: {var.value}")
        
        print("\nПримеры выражений для тестирования:")
        print("  length@panel=800")
        print("  width@result=width.panel - 2*thickness.edge")  
        print("  diagonal@panel=sqrt(length.panel^2 + width.panel^2)")
        print("  L=600  # локальный алиас")
        
        # Тестируем несколько выражений
        test_expressions = [
            "length@panel=800",
            "width@result=width.panel - 2*thickness.edge",
            "diagonal@panel=sqrt(length.panel^2 + width.panel^2)"
        ]
        
        print("\nТестирование выражений:")
        for expr in test_expressions:
            try:
                parsed = ExpressionParser.parse_expression(expr)
                print(f"  ✅ {expr} → {parsed['type'].value}")
            except Exception as e:
                print(f"  ❌ {expr} → {e}")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")

def run_interactive_formula_test_v2():
    """Интерактивное тестирование формул V2"""
    try:
        from visual_solving_advanced_v2 import (
            HybridBoxSolution, HybridEdgeBandingSolution, v2_solution_manager,
            ExpressionParser
        )
        from variable_system_v2 import V2FormulaEvaluator
        
        print("🧪 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ ФОРМУЛ V2")
        print("=" * 45)
        
        # Создаем тестовые решения
        v2_solution_manager.reset()
        panel = HybridBoxSolution("panel", 600, 400, 18)
        edge = HybridEdgeBandingSolution("edge", "white", 2.0, ["top"])
        
        print("Созданы тестовые решения:")
        print(f"  panel: {panel.length}x{panel.width}x{panel.height}")
        print(f"  edge: thickness={edge.get_variable_by_reference('thickness').value}")
        
        print("\nДоступные переменные для формул:")
        print("  length.panel, width.panel, height.panel")
        print("  thickness.edge, material.edge")
        
        print("\nПримеры формул:")
        print("  width.panel - 2*thickness.edge")
        print("  sqrt(length.panel^2 + width.panel^2)")
        print("  max(length.panel, width.panel, height.panel)")
        print("Введите 'quit' для выхода")
        
        solution_registry = v2_solution_manager.get_all_solutions()
        
        while True:
            try:
                formula = input("\nFormula V2> ").strip()
                
                if formula.lower() in ['quit', 'q', 'exit']:
                    break
                
                if not formula:
                    continue
                
                # Проверяем, это выражение или формула
                if '=' in formula:
                    # Это выражение - парсим его
                    parsed = ExpressionParser.parse_expression(formula)
                    print(f"✅ Выражение: {parsed['type'].value}")
                    for key, value in parsed.items():
                        if key != 'type':
                            print(f"   {key}: {value}")
                else:
                    # Это формула - вычисляем её
                    result = V2FormulaEvaluator.evaluate_formula(formula, solution_registry)
                    print(f"✅ Результат: {result}")
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            except KeyboardInterrupt:
                break
        
        print("\nТестирование завершено!")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")

# =============================================================================
# Главная функция с интегрированной стартовой системой
# =============================================================================

def run_main_application():
    """Запуск основного приложения с интегрированной стартовой системой"""
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import QDialog
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    try:
        # Импортируем стартовую систему
        from complete_startup_system_v2 import StartupManager, global_variable_registry
        from visual_solving_ui_advanced_v2 import V2AdvancedMainWindow
        from visual_solving_advanced_v2 import v2_solution_manager, HybridBoxSolution
        
        print("🚀 Запуск Visual Solving Advanced V2...")
        print("=" * 50)
        
        # Создаем менеджер стартовой системы
        startup_manager = StartupManager()
        
        # Показываем стартовое окно
        result = startup_manager.show_startup_dialog()
        
        if result == QDialog.DialogCode.Accepted:
            print("✅ Стартовая система успешно завершена")
            
            # Инициализируем глобальные переменные в систему V2
            _initialize_global_variables()
            
            # Создаем и показываем главное окно
            print("🔧 Создание главного окна...")
            main_window = V2AdvancedMainWindow()
            
            # Если было создано новое решение, добавляем демо-данные
            _setup_demo_data_if_needed(main_window)
            
            main_window.show()
            print("✅ Главное окно запущено")
            
            # Показываем приветственную информацию
            _show_welcome_info(main_window)
            
            # Запускаем приложение
            sys.exit(app.exec())
            
        else:
            print("❌ Запуск приложения отменён пользователем")
            sys.exit(0)
            
    except ImportError as e:
        print(f"❌ Ошибка импорта компонентов: {e}")
        
        # Показываем диалог ошибки
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Startup Error")
        msg.setText("Failed to load Visual Solving V2 components")
        msg.setDetailedText(f"Import error: {str(e)}\n\nPlease ensure all required files are present:\n- variable_system_v2.py\n- visual_solving_advanced_v2.py\n- complete_startup_system_v2.py\n- visual_solving_ui_advanced_v2.py")
        msg.exec()
        
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Критическая ошибка запуска: {e}")
        traceback.print_exc()
        
        # Показываем диалог критической ошибки
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Critical Error")
        msg.setText("Critical startup error occurred")
        msg.setDetailedText(f"Error: {str(e)}\n\nStacktrace:\n{traceback.format_exc()}")
        msg.exec()
        
        sys.exit(1)

def _initialize_global_variables():
    """Инициализация глобальных переменных в V2 системе"""
    from complete_startup_system_v2 import global_variable_registry
    
    global_vars = global_variable_registry.get_all_variables()
    print(f"🌐 Инициализация {len(global_vars)} глобальных переменных...")
    
    for var in global_vars:
        print(f"   {var.name} ({var.var_type}) = {var.value}")

def _setup_demo_data_if_needed(main_window):
    """Настройка демо-данных при необходимости"""
    from visual_solving_advanced_v2 import v2_solution_manager, HybridBoxSolution, HybridEdgeBandingSolution, Part3DSpace
    
    # Проверяем, есть ли уже решения в системе
    existing_solutions = v2_solution_manager.get_all_solutions()
    
    if not existing_solutions:
        print("🎯 Создание демонстрационных данных...")
        
        try:
            # Создаем рабочее пространство
            workspace = Part3DSpace("Demo Workspace")
            
            # Создаем демо-решения
            panel = HybridBoxSolution("demo_panel", 600, 400, 18)
            panel.place_in_space(workspace)
            
            edge = HybridEdgeBandingSolution("demo_edge", "white", 2.0, ["top", "bottom"])
            edge.place_in_space(workspace)
            
            # Результирующая панель с V2 формулами
            result = HybridBoxSolution(
                "demo_result",
                "length.demo_panel",
                "width.demo_panel - 2*thickness.demo_edge",
                "height.demo_panel"
            )
            result.place_in_space(workspace)
            
            # Устанавливаем workspace в главное окно
            main_window.workspace = workspace
            
            # Обновляем UI
            main_window._add_solution_to_tree(panel)
            main_window._add_solution_to_tree(edge)
            main_window._add_solution_to_tree(result)
            
            print("✅ Демонстрационные данные созданы")
            
        except Exception as e:
            print(f"⚠️ Ошибка создания демо-данных: {e}")

def _show_welcome_info(main_window):
    """Показать приветственную информацию"""
    from PyQt6.QtWidgets import QMessageBox
    
    welcome_text = """🎉 Добро пожаловать в Visual Solving V2!

🚀 НОВЫЕ ВОЗМОЖНОСТИ V2:
• Революционная адресация: variable@solution=value
• Естественное чтение: variable.solution  
• Безопасные алиасы: L, W, H (изолированы в Solution)
• Читаемые формулы: width.panel - 2*thickness.edge
• Глобальные переменные: доступны из любого решения

📋 БЫСТРЫЙ СТАРТ:
1. Создайте новые решения через меню "Create"
2. Используйте V2 синтаксис в формулах
3. Управляйте глобальными переменными
4. Исследуйте Global Variable Registry V2

💡 ПРИМЕРЫ V2 СИНТАКСИСА:
• length@panel=600
• width@result=width.panel - 2*thickness.edge
• diagonal=sqrt(length.panel^2 + width.panel^2)

Приятной работы! 🛠️"""
    
    QMessageBox.information(main_window, "Welcome to Visual Solving V2", welcome_text)

def run_gui_v2():
    """Запуск графического интерфейса V2 (устаревший метод)"""
    print("⚠️  Внимание: Используйте run_main_application() для полной интеграции")
    print("🔄 Перенаправление на новую систему...")
    run_main_application()

def show_help_v2():
    """Показать справку по V2"""
    print("Visual Solving Advanced V2 Demo Runner")
    print("=====================================")
    print()
    print("Использование:")
    print("  python run_advanced_demo_v2.py           - запуск с GUI и стартовой системой")
    print("  python run_advanced_demo_v2.py --console - консольная демонстрация V2")
    print("  python run_advanced_demo_v2.py --check   - проверка зависимостей")
    print("  python run_advanced_demo_v2.py --formula - интерактивное тестирование формул V2")
    print("  python run_advanced_demo_v2.py --help    - эта справка")
    print()
    print("Файлы системы V2:")
    print("  variable_system_v2.py                    - новая система переменных")
    print("  visual_solving_advanced_v2.py            - гибридная система (V2 + Legacy)")
    print("  complete_startup_system_v2.py            - стартовые диалоги и глобальные переменные")
    print("  visual_solving_ui_advanced_v2.py         - UI с поддержкой V2")
    print("  run_advanced_demo_v2.py                  - этот файл (интегрированный запуск)")
    print()
    print("🚀 РЕВОЛЮЦИОННЫЕ ВОЗМОЖНОСТИ V2:")
    print("   • Новая адресация: variable@solution=value")
    print("   • Чтение через точку: a=variable.solution")
    print("   • Локальные алиасы: L, W, H (изолированы в Solution)")
    print("   • Читаемые формулы: width.panel - 2*thickness.edge")
    print("   • Глобальные переменные: доступны везде")
    print("   • Стартовые диалоги: New/Open Solution")
    print("   • Обратная совместимость: #1.length работает")
    print("   • Валидация алиасов: @ и точка запрещены")
    print()
    print("🔧 ПРИМЕРЫ НОВОГО СИНТАКСИСА:")
    print("   length@box=600                           # Установка значения")
    print("   width@result=width.panel - 2*thickness.edge  # Формула с ссылками")
    print("   diagonal@panel=sqrt(length.panel^2 + width.panel^2)  # Математика")
    print("   a=volume.box                             # Чтение значения")
    print("   L=600                                    # Локальный алиас")
    print()
    print("📋 ПРЕИМУЩЕСТВА V2:")
    print("   ✅ Интуитивность - variable@solution понятнее #1.length")
    print("   ✅ Читаемость - width.panel - 2*thickness.edge")
    print("   ✅ Безопасность - алиасы изолированы в Solution")
    print("   ✅ Разделение - @ для записи, точка для чтения")
    print("   ✅ Совместимость - старый синтаксис работает")
    print("   ✅ Стартовая система - удобный запуск")
    print()
    print("Требования:")
    print("  Python 3.9+, PyQt6, NumPy")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--console":
            # Консольная демонстрация без GUI
            missing, v2_available = check_dependencies()
            if missing:
                print(f"\n❌ Отсутствуют зависимости: {', '.join(missing)}")
                print("Установите: pip install " + " ".join(missing))
                sys.exit(1)
            elif not v2_available:
                print("\n❌ V2 система недоступна")
                sys.exit(1)
            else:
                run_console_demo()
                
        elif arg == "--check":
            # Проверка зависимостей
            missing, v2_available = check_dependencies()
            if missing or not v2_available:
                print(f"\n❌ Проблемы с зависимостями")
                sys.exit(1)
            else:
                print("\n✅ Все компоненты V2 доступны")
                
        elif arg == "--formula":
            # Интерактивное тестирование формул
            run_interactive_formula_test_v2()
            
        elif arg in ["--help", "-h"]:
            # Справка
            show_help_v2()
            
        else:
            print(f"❌ Неизвестный аргумент: {arg}")
            print("Используйте --help для справки")
            sys.exit(1)
    else:
        # Основной запуск - проверяем зависимости и запускаем GUI с стартовой системой
        print("🔍 Проверка системных компонентов...")
        missing, all_available = check_dependencies()
        
        if missing:
            print(f"\n❌ Отсутствуют зависимости: {', '.join(missing)}")
            print("Установите: pip install " + " ".join(missing))
            sys.exit(1)
        
        if not all_available:
            print("\n❌ Не все компоненты V2 доступны")
            print("Убедитесь, что все файлы системы V2 находятся в каталоге:")
            print("  - variable_system_v2.py")
            print("  - visual_solving_advanced_v2.py") 
            print("  - complete_startup_system_v2.py")
            print("  - visual_solving_ui_advanced_v2.py")
            sys.exit(1)
        
        print("✅ Все компоненты V2 найдены")
        print()
        
        # Запускаем основное приложение с интегрированной стартовой системой
        run_main_application()
