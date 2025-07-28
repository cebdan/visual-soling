# Visual Solving - Advanced System
# Гибридная система с поддержкой нового синтаксиса и обратной совместимости
# Поддерживает: variable@solution, variable.solution и #1.length

from variable_system import (
    Solution, Variable, VariableType, ExpressionParser, 
    FormulaEvaluator, register_solution, get_solution, clear_registry
)
from typing import Dict, Any, List, Optional, Union, Set
import re

class HybridVariable(Variable):
    """
    Гибридная переменная с поддержкой нового и старого синтаксиса
    """
    
    def __init__(self, name: str, value: Union[float, str], 
                 variable_type: VariableType = VariableType.CONTROLLABLE,
                 legacy_id: Optional[int] = None):
        super().__init__(name, value, variable_type)
        self.legacy_id = legacy_id  # Старый #1, #2, #3 ID
        
    def get_legacy_reference(self, solution_name: str) -> str:
        """Получение legacy ссылки вида #1.length"""
        if self.legacy_id is not None:
            return f"#{self.legacy_id}.{self.name}"
        return f"#{self.name}.{solution_name}"

class HybridFormulaEvaluator(FormulaEvaluator):
    """
    Гибридный вычислитель формул с поддержкой старого и нового синтаксиса
    """
    
    def __init__(self, solutions_registry: Dict[str, 'HybridSolution'] = None):
        super().__init__(solutions_registry)
        self.legacy_pattern = r'#(\d+)\.(\w+)'  # Паттерн для #1.length
        
    def evaluate_expression(self, expression: str, current_solution: 'HybridSolution' = None) -> float:
        """
        Вычисление выражения с поддержкой обоих синтаксисов
        """
        try:
            # Сначала обрабатываем legacy синтаксис #1.length
            expression = self._convert_legacy_references(expression, current_solution)
            
            # Затем используем родительский метод для нового синтаксиса
            return super().evaluate_expression(expression, current_solution)
            
        except Exception as e:
            raise ValueError(f"Error evaluating hybrid expression '{expression}': {str(e)}")
    
    def _convert_legacy_references(self, expression: str, current_solution: 'HybridSolution') -> str:
        """
        Конвертация legacy ссылок #1.length в новый синтаксис variable.solution
        """
        if not current_solution:
            return expression
        
        # Находим все legacy ссылки
        legacy_matches = re.finditer(self.legacy_pattern, expression)
        converted_expression = expression
        
        for match in legacy_matches:
            legacy_id = int(match.group(1))
            var_name = match.group(2)
            full_legacy_ref = match.group(0)
            
            # Находим переменную по legacy_id
            target_solution = current_solution._find_solution_by_legacy_id(legacy_id, var_name)
            
            if target_solution:
                # Заменяем на новый синтаксис
                new_ref = f"{var_name}.{target_solution.name}"
                converted_expression = converted_expression.replace(full_legacy_ref, new_ref)
            else:
                print(f"Warning: Legacy reference {full_legacy_ref} not found")
        
        return converted_expression

class HybridSolution(Solution):
    """
    Гибридное решение с поддержкой нового и старого синтаксиса
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.legacy_id_counter = 1  # Счетчик для автоматического назначения legacy ID
        self.evaluator = HybridFormulaEvaluator()
        self.legacy_references: Dict[int, str] = {}  # legacy_id -> variable_name
        
    def set_variable(self, var_name: str, value: Union[float, str], 
                    variable_type: VariableType = VariableType.CONTROLLABLE,
                    auto_assign_legacy_id: bool = True) -> bool:
        """
        Установка переменной с автоматическим назначением legacy ID
        """
        try:
            # Назначаем legacy ID если его нет
            legacy_id = None
            if auto_assign_legacy_id:
                legacy_id = self.legacy_id_counter
                self.legacy_id_counter += 1
                self.legacy_references[legacy_id] = var_name
            
            # Создаем гибридную переменную
            variable = HybridVariable(var_name, value, variable_type, legacy_id)
            
            # Обрабатываем зависимости для обоих синтаксисов
            if isinstance(value, str):
                # Новый синтаксис
                references = ExpressionParser().find_read_references(value)
                for ref in references:
                    dep_key = f"{ref['solution']}.{ref['variable']}"
                    variable.add_dependency(dep_key)
                
                # Legacy синтаксис - обрабатывается в evaluate_expression
                variable.variable_type = VariableType.CALCULATED
            
            self.variables[var_name] = variable
            return True
            
        except Exception as e:
            print(f"Error setting hybrid variable {var_name}: {e}")
            return False
    
    def set_variable_formula(self, var_name: str, formula: str) -> bool:
        """
        Установка формулы для переменной (поддерживает оба синтаксиса)
        """
        return self.set_variable(var_name, formula, VariableType.CALCULATED)
    
    def set_alias_variable(self, alias: str, value: Union[float, str]) -> bool:
        """
        Установка переменной через алиас
        """
        # Создаем переменную с именем алиаса
        result = self.set_variable(alias, value)
        if result:
            # Устанавливаем алиас
            self.set_alias(alias, alias)
        return result
    
    def get_legacy_reference(self, var_name: str) -> Optional[str]:
        """Получение legacy ссылки для переменной"""
        if var_name in self.variables:
            var = self.variables[var_name]
            if isinstance(var, HybridVariable) and var.legacy_id:
                return f"#{var.legacy_id}.{var_name}"
        return None
    
    def _find_solution_by_legacy_id(self, legacy_id: int, var_name: str) -> Optional['HybridSolution']:
        """
        Поиск решения по legacy ID переменной
        Логика: #1 обычно ссылается на первую переменную текущего решения
        """
        # Сначала проверяем текущее решение
        if legacy_id in self.legacy_references:
            return self
        
        # Затем проверяем другие решения в реестре
        for solution in self.solutions_registry.values():
            if isinstance(solution, HybridSolution):
                if legacy_id in solution.legacy_references:
                    stored_var_name = solution.legacy_references[legacy_id]
                    if stored_var_name == var_name:
                        return solution
        
        return None
    
    def get_all_variables_info(self) -> List[Dict[str, Any]]:
        """Получение информации о всех переменных с поддержкой legacy"""
        info = []
        
        for var_name, variable in self.variables.items():
            # Находим алиасы для этой переменной
            aliases = [alias for alias, var in self.aliases.items() if var == var_name]
            
            # Legacy ссылка
            legacy_ref = None
            if isinstance(variable, HybridVariable) and variable.legacy_id:
                legacy_ref = f"#{variable.legacy_id}.{var_name}"
            
            info.append({
                'name': var_name,
                'value': self.get_variable_value(var_name),
                'raw_value': variable.value,
                'type': variable.variable_type.value,
                'aliases': aliases,
                'is_formula': variable.is_formula(),
                'dependencies': list(variable.dependencies),
                'dependents': list(variable.dependents),
                'write_id': f"{var_name}@{self.name}",
                'read_id': f"{var_name}.{self.name}",
                'legacy_id': legacy_ref
            })
        
        return info

class HybridBoxSolution(HybridSolution):
    """
    Коробка/панель с поддержкой нового синтаксиса
    """
    
    def __init__(self, name: str, length: Union[float, str], 
                 width: Union[float, str], height: Union[float, str]):
        super().__init__(name)
        
        # Создаем базовые переменные
        self.set_variable("length", length)
        self.set_variable("width", width) 
        self.set_variable("height", height)
        
        # Создаем удобные алиасы
        self.set_alias("L", "length")
        self.set_alias("W", "width")
        self.set_alias("H", "height")
        
        # Регистрируем в глобальном реестре
        register_solution(self)
    
    @property
    def length(self) -> float:
        """Длина (с автоматическим вычислением формул)"""
        return self.get_variable_value("length") or 0.0
    
    @property 
    def width(self) -> float:
        """Ширина (с автоматическим вычислением формул)"""
        return self.get_variable_value("width") or 0.0
    
    @property
    def height(self) -> float:
        """Высота (с автоматическим вычислением формул)"""
        return self.get_variable_value("height") or 0.0
    
    @property
    def volume(self) -> float:
        """Объем (вычисляемое свойство)"""
        return self.length * self.width * self.height
    
    def __str__(self) -> str:
        return f"HybridBoxSolution('{self.name}', {self.length}x{self.width}x{self.height})"
    
    def __repr__(self) -> str:
        return self.__str__()

class SolutionManager:
    """
    Менеджер решений с поддержкой гибридной системы
    """
    
    def __init__(self):
        self.solutions: Dict[str, HybridSolution] = {}
        self.dependency_tracker = None
    
    def create_box_solution(self, name: str, length: Union[float, str], 
                           width: Union[float, str], height: Union[float, str]) -> HybridBoxSolution:
        """Создание решения-коробки"""
        solution = HybridBoxSolution(name, length, width, height)
        self.solutions[name] = solution
        return solution
    
    def get_solution(self, name: str) -> Optional[HybridSolution]:
        """Получение решения по имени"""
        return self.solutions.get(name)
    
    def get_all_solutions(self) -> List[HybridSolution]:
        """Получение всех решений"""
        return list(self.solutions.values())
    
    def reset(self):
        """Сброс всех решений"""
        self.solutions.clear()
        clear_registry()
    
    def get_global_registry_info(self) -> List[Dict[str, Any]]:
        """Получение информации о всех переменных во всех решениях"""
        all_variables = []
        
        for solution_name, solution in self.solutions.items():
            for var_info in solution.get_all_variables_info():
                var_info['solution_name'] = solution_name
                all_variables.append(var_info)
        
        return all_variables

# Глобальный менеджер решений
solution_manager = SolutionManager()

def demo_hybrid_system():
    """
    Демонстрация гибридной системы с поддержкой обоих синтаксисов
    """
    print("🚀 ДЕМОНСТРАЦИЯ ГИБРИДНОЙ СИСТЕМЫ")
    print("Поддержка НОВОГО и СТАРОГО синтаксиса")
    print("=" * 50)
    
    # Сброс системы
    solution_manager.reset()
    
    print("\n1. Создание решений с новым синтаксисом:")
    
    # Создаем панель
    panel = solution_manager.create_box_solution("panel", 600, 400, 18)
    print(f"   panel = HybridBoxSolution('panel', 600, 400, 18)")
    print(f"   ✅ Создано: {panel}")
    
    print("\n2. Автоматические legacy ID и алиасы:")
    for var_info in panel.get_all_variables_info():
        print(f"   • {var_info['write_id']} = {var_info['value']}")
        print(f"     Legacy: {var_info['legacy_id']}")
        print(f"     Read: {var_info['read_id']}")
        print(f"     Aliases: {var_info['aliases']}")
    
    print("\n3. Создание зависимого решения с НОВЫМ синтаксисом:")
    result = solution_manager.create_box_solution(
        "result",
        "length.panel",           # Новый синтаксис
        "width.panel - 20",       # Формула с новым синтаксисом
        "height.panel"            # Новый синтаксис
    )
    print(f"   result = HybridBoxSolution('result', 'length.panel', 'width.panel - 20', 'height.panel')")
    print(f"   ✅ Создано: {result}")
    
    print("\n4. Создание решения с LEGACY синтаксисом:")
    legacy_result = HybridBoxSolution("legacy_result", "#1.length", "#2.width - 10", "#3.height")
    print(f"   legacy_result = HybridBoxSolution('legacy_result', '#1.length', '#2.width - 10', '#3.height')")
    print(f"   ✅ Создано: {legacy_result}")
    
    print("\n5. Смешанный синтаксис в одной формуле:")
    mixed = HybridBoxSolution(
        "mixed",
        "length.panel + #1.length",  # Новый + Legacy
        "max(width.panel, #2.width)", # Функция с разными синтаксисами
        "18"
    )
    print(f"   mixed = формула с новым и legacy синтаксисом")
    print(f"   ✅ Создано: {mixed}")
    
    print("\n6. Результаты вычислений:")
    all_solutions = solution_manager.get_all_solutions()
    
    for sol in all_solutions:
        print(f"\n   📦 {sol.name.upper()}:")
        print(f"      Размеры: {sol.length:.1f} x {sol.width:.1f} x {sol.height:.1f}")
        print(f"      Объем: {sol.volume:.1f}")
        
        # Показываем формулы
        for var_info in sol.get_all_variables_info():
            if var_info['is_formula']:
                print(f"      {var_info['name']}: {var_info['raw_value']} = {var_info['value']:.1f}")
    
    print("\n7. Демонстрация автоматического обновления:")
    print("   Изменяем length@panel с 600 на 800...")
    panel.set_variable("length", 800)
    
    print("\n   📊 ОБНОВЛЕННЫЕ РЕЗУЛЬТАТЫ:")
    for sol in all_solutions:
        print(f"   {sol.name}: {sol.length:.1f} x {sol.width:.1f} x {sol.height:.1f}")
    
    print("\n8. Работа с алиасами:")
    print("   Устанавливаем L = 1000 через алиас...")
    panel.set_alias_variable("L", 1000)
    
    print(f"   ✅ panel.L (алиас) = {panel.get_variable_value('L')}")
    print(f"   ✅ panel.length = {panel.get_variable_value('length')}")
    print(f"   ✅ result.length = {result.length} (обновилось автоматически)")
    
    print("\n9. Глобальный реестр переменных:")
    global_info = solution_manager.get_global_registry_info()
    
    print(f"   Всего переменных в системе: {len(global_info)}")
    print("   Детальная информация:")
    
    for var_info in global_info:
        solution_name = var_info['solution_name']
        var_name = var_info['name']
        value = var_info['value']
        legacy = var_info.get('legacy_id', 'N/A')
        
        print(f"   • {solution_name}.{var_name} = {value:.1f} (legacy: {legacy})")
    
    print("\n🎉 ДЕМОНСТРАЦИЯ ГИБРИДНОЙ СИСТЕМЫ ЗАВЕРШЕНА!")
    print("\nВозможности гибридной системы:")
    print("✅ Новый синтаксис: variable@solution и variable.solution")
    print("✅ Legacy поддержка: #1.length продолжает работать")
    print("✅ Смешанные формулы: новый + legacy в одном выражении")
    print("✅ Автоматические legacy ID: совместимость с существующими проектами")
    print("✅ Безопасные алиасы: L, W, H изолированы в каждом решении")
    print("✅ Умные зависимости: автоматический пересчет при изменениях")
    print("✅ Глобальный реестр: централизованное управление переменными")

if __name__ == "__main__":
    demo_hybrid_system()
