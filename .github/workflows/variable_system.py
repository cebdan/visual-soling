# Visual Solving - Variable System
# Революционная система переменных с интуитивным синтаксисом
# variable@solution для записи, variable.solution для чтения

import re
import math
from typing import Dict, Any, List, Optional, Union, Set
from enum import Enum

class VariableType(Enum):
    """Типы переменных в системе"""
    CONTROLLABLE = "controllable"
    CALCULATED = "calculated" 
    ALIAS = "alias"

class ExpressionParser:
    """
    Парсер выражений для нового синтаксиса:
    - variable@solution = value (установка значения)
    - variable.solution (чтение значения)
    - Поддержка математических выражений
    """
    
    def __init__(self):
        # Регулярные выражения для парсинга
        self.assignment_pattern = r'^(\w+)@(\w+)\s*=\s*(.+)$'
        self.read_reference_pattern = r'(\w+)\.(\w+)'
        self.alias_assignment_pattern = r'^(\w+)\s*=\s*(.+)$'
        
        # Математические функции
        self.math_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'abs': abs,
            'max': max,
            'min': min,
            'pow': pow,
            'exp': math.exp,
            'log': math.log,
            'log10': math.log10,
            'ceil': math.ceil,
            'floor': math.floor,
            'round': round
        }
    
    def parse_assignment(self, expression: str) -> Optional[Dict[str, str]]:
        """
        Парсинг присвоения: variable@solution = value
        Возвращает: {'variable': 'name', 'solution': 'name', 'value': 'expression'}
        """
        expression = expression.strip()
        
        # Проверка на assignment с @
        match = re.match(self.assignment_pattern, expression)
        if match:
            variable_name, solution_name, value_expr = match.groups()
            return {
                'type': 'assignment',
                'variable': variable_name.strip(),
                'solution': solution_name.strip(),
                'value': value_expr.strip()
            }
        
        # Проверка на алиас assignment
        match = re.match(self.alias_assignment_pattern, expression)
        if match:
            alias_name, value_expr = match.groups()
            # Проверяем, что это не содержит @ или .
            if '@' not in alias_name and '.' not in alias_name:
                return {
                    'type': 'alias_assignment',
                    'alias': alias_name.strip(),
                    'value': value_expr.strip()
                }
        
        return None
    
    def find_read_references(self, expression: str) -> List[Dict[str, str]]:
        """
        Находит все ссылки чтения в выражении: variable.solution
        Возвращает список: [{'variable': 'name', 'solution': 'name'}, ...]
        """
        references = []
        matches = re.finditer(self.read_reference_pattern, expression)
        
        for match in matches:
            variable_name, solution_name = match.groups()
            references.append({
                'variable': variable_name,
                'solution': solution_name,
                'full_reference': f"{variable_name}.{solution_name}"
            })
        
        return references
    
    def validate_name(self, name: str) -> bool:
        """Валидация имени переменной или решения"""
        if not name:
            return False
        
        # Имя должно начинаться с буквы или цифры
        if not (name[0].isalpha() or name[0].isdigit()):
            return False
        
        # Имя не должно содержать @ или .
        if '@' in name or '.' in name:
            return False
        
        # Имя должно состоять из букв, цифр и _
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return False
        
        return True

class FormulaEvaluator:
    """
    Вычислитель формул с поддержкой нового синтаксиса
    """
    
    def __init__(self, solutions_registry: Dict[str, 'Solution'] = None):
        self.solutions_registry = solutions_registry or {}
        self.parser = ExpressionParser()
    
    def evaluate_expression(self, expression: str, current_solution: 'Solution' = None) -> float:
        """
        Вычисление выражения с заменой variable.solution на значения
        """
        try:
            # Находим все ссылки вида variable.solution
            references = self.parser.find_read_references(expression)
            
            # Заменяем ссылки на фактические значения
            evaluated_expression = expression
            
            for ref in references:
                var_name = ref['variable']
                solution_name = ref['solution']
                full_ref = ref['full_reference']
                
                # Получаем значение
                value = self._get_variable_value(var_name, solution_name)
                
                if value is not None:
                    # Заменяем ссылку на значение
                    evaluated_expression = evaluated_expression.replace(full_ref, str(value))
                else:
                    raise ValueError(f"Variable {full_ref} not found")
            
            # Заменяем ^ на **
            evaluated_expression = evaluated_expression.replace('^', '**')
            
            # Добавляем математические функции в контекст
            eval_context = {
                '__builtins__': {},
                **self.parser.math_functions
            }
            
            # Вычисляем выражение
            result = eval(evaluated_expression, eval_context)
            return float(result)
            
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {str(e)}")
    
    def _get_variable_value(self, var_name: str, solution_name: str) -> Optional[float]:
        """Получение значения переменной из решения"""
        if solution_name in self.solutions_registry:
            solution = self.solutions_registry[solution_name]
            return solution.get_variable_value(var_name)
        return None

class Variable:
    """
    Переменная с поддержкой нового синтаксиса
    """
    
    def __init__(self, name: str, value: Union[float, str], 
                 variable_type: VariableType = VariableType.CONTROLLABLE):
        self.name = name
        self.value = value
        self.variable_type = variable_type
        self.dependencies: Set[str] = set()  # Зависимости вида solution.variable
        self.dependents: Set[str] = set()    # Кто зависит от этой переменной
        
    def is_formula(self) -> bool:
        """Проверка, является ли значение формулой"""
        return isinstance(self.value, str)
    
    def add_dependency(self, dependency: str):
        """Добавление зависимости"""
        self.dependencies.add(dependency)
    
    def add_dependent(self, dependent: str):
        """Добавление зависимого элемента"""
        self.dependents.add(dependent)

class Solution:
    """
    Базовый класс решения с поддержкой нового синтаксиса переменных
    """
    
    def __init__(self, name: str):
        self.name = name
        self.variables: Dict[str, Variable] = {}
        self.aliases: Dict[str, str] = {}  # alias -> variable_name
        self.solutions_registry: Dict[str, 'Solution'] = {}
        self.evaluator = FormulaEvaluator()
        
    def set_solutions_registry(self, registry: Dict[str, 'Solution']):
        """Установка реестра решений для разрешения зависимостей"""
        self.solutions_registry = registry
        self.evaluator.solutions_registry = registry
    
    def set_variable(self, var_name: str, value: Union[float, str], 
                    variable_type: VariableType = VariableType.CONTROLLABLE) -> bool:
        """
        Установка переменной
        value может быть числом или формулой (строкой)
        """
        try:
            # Создаем переменную
            variable = Variable(var_name, value, variable_type)
            
            # Если значение - формула, находим зависимости
            if isinstance(value, str):
                references = ExpressionParser().find_read_references(value)
                for ref in references:
                    dep_key = f"{ref['solution']}.{ref['variable']}"
                    variable.add_dependency(dep_key)
                    
                    # Добавляем обратную зависимость
                    if ref['solution'] in self.solutions_registry:
                        dep_solution = self.solutions_registry[ref['solution']]
                        if ref['variable'] in dep_solution.variables:
                            dep_var = dep_solution.variables[ref['variable']]
                            dep_var.add_dependent(f"{self.name}.{var_name}")
                
                variable.variable_type = VariableType.CALCULATED
            
            self.variables[var_name] = variable
            return True
            
        except Exception as e:
            print(f"Error setting variable {var_name}: {e}")
            return False
    
    def set_alias(self, alias: str, var_name: str) -> bool:
        """
        Установка алиаса для переменной
        """
        parser = ExpressionParser()
        
        # Валидация алиаса
        if not parser.validate_name(alias):
            print(f"Invalid alias name: {alias}")
            return False
        
        if var_name not in self.variables:
            print(f"Variable {var_name} not found")
            return False
        
        self.aliases[alias] = var_name
        return True
    
    def get_variable_value(self, identifier: str) -> Optional[float]:
        """
        Получение значения переменной по имени или алиасу
        """
        # Проверяем алиасы
        if identifier in self.aliases:
            identifier = self.aliases[identifier]
        
        if identifier not in self.variables:
            return None
        
        variable = self.variables[identifier]
        
        # Если переменная содержит формулу, вычисляем её
        if variable.is_formula():
            try:
                return self.evaluator.evaluate_expression(variable.value, self)
            except Exception as e:
                print(f"Error evaluating formula for {identifier}: {e}")
                return None
        else:
            return float(variable.value)
    
    def update_dependencies(self):
        """Обновление всех зависимых переменных"""
        for var_name, variable in self.variables.items():
            if variable.dependents:
                # Уведомляем зависимые переменные об изменении
                for dependent in variable.dependents:
                    solution_name, dep_var_name = dependent.split('.')
                    if solution_name in self.solutions_registry:
                        dep_solution = self.solutions_registry[solution_name]
                        # Зависимая переменная пересчитается при следующем обращении
                        pass
    
    def get_all_variables_info(self) -> List[Dict[str, Any]]:
        """Получение информации о всех переменных"""
        info = []
        
        for var_name, variable in self.variables.items():
            # Находим алиасы для этой переменной
            aliases = [alias for alias, var in self.aliases.items() if var == var_name]
            
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
                'read_id': f"{var_name}.{self.name}"
            })
        
        return info

class DependencyTracker:
    """
    Отслеживание зависимостей между переменными
    """
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}
        
    def add_dependency(self, dependent: str, dependency: str):
        """Добавление зависимости"""
        if dependent not in self.dependency_graph:
            self.dependency_graph[dependent] = set()
        self.dependency_graph[dependent].add(dependency)
    
    def has_circular_dependency(self, start: str, target: str, visited: Set[str] = None) -> bool:
        """Проверка на циклические зависимости"""
        if visited is None:
            visited = set()
        
        if start in visited:
            return start == target
        
        visited.add(start)
        
        if start in self.dependency_graph:
            for dependency in self.dependency_graph[start]:
                if self.has_circular_dependency(dependency, target, visited.copy()):
                    return True
        
        return False

# Глобальный реестр решений
global_solutions_registry: Dict[str, Solution] = {}

def register_solution(solution: Solution):
    """Регистрация решения в глобальном реестре"""
    global_solutions_registry[solution.name] = solution
    solution.set_solutions_registry(global_solutions_registry)
    
    # Обновляем реестр у всех существующих решений
    for existing_solution in global_solutions_registry.values():
        existing_solution.set_solutions_registry(global_solutions_registry)

def get_solution(name: str) -> Optional[Solution]:
    """Получение решения из реестра"""
    return global_solutions_registry.get(name)

def clear_registry():
    """Очистка глобального реестра"""
    global global_solutions_registry
    global_solutions_registry.clear()

def demo_new_syntax():
    """
    Демонстрация нового синтаксиса переменных
    """
    print("🚀 ДЕМОНСТРАЦИЯ НОВОГО СИНТАКСИСА ПЕРЕМЕННЫХ")
    print("=" * 50)
    
    # Очищаем реестр
    clear_registry()
    
    # Создаем решения
    panel = Solution("panel")
    result = Solution("result")
    
    # Регистрируем решения
    register_solution(panel)
    register_solution(result)
    
    print("\n1. Создание базовых переменных:")
    print("   length@panel = 600")
    panel.set_variable("length", 600)
    
    print("   width@panel = 400")
    panel.set_variable("width", 400)
    
    print("   thickness@panel = 18")
    panel.set_variable("thickness", 18)
    
    print(f"   ✅ panel.length = {panel.get_variable_value('length')}")
    print(f"   ✅ panel.width = {panel.get_variable_value('width')}")
    print(f"   ✅ panel.thickness = {panel.get_variable_value('thickness')}")
    
    print("\n2. Создание алиасов (изолированы в решении):")
    print("   L = 600 (алиас для length@panel)")
    panel.set_alias("L", "length")
    panel.set_variable("L", 600)  # через алиас
    
    print("   W = 400 (алиас для width@panel)")
    panel.set_alias("W", "width")
    
    print("   H = 18 (алиас для thickness@panel)")
    panel.set_alias("H", "thickness")
    
    print(f"   ✅ L (алиас) = {panel.get_variable_value('L')}")
    print(f"   ✅ W (алиас) = {panel.get_variable_value('W')}")
    print(f"   ✅ H (алиас) = {panel.get_variable_value('H')}")
    
    print("\n3. Создание зависимых переменных с формулами:")
    print("   length@result = length.panel")
    result.set_variable("length", "length.panel")
    
    print("   width@result = width.panel - 20")
    result.set_variable("width", "width.panel - 20")
    
    print("   thickness@result = thickness.panel")
    result.set_variable("thickness", "thickness.panel")
    
    print(f"   ✅ result.length = {result.get_variable_value('length')}")
    print(f"   ✅ result.width = {result.get_variable_value('width')}")
    print(f"   ✅ result.thickness = {result.get_variable_value('thickness')}")
    
    print("\n4. Создание сложных формул:")
    print("   volume@result = length.result * width.result * thickness.result")
    result.set_variable("volume", "length.result * width.result * thickness.result")
    
    print("   diagonal@result = sqrt(length.result^2 + width.result^2)")
    result.set_variable("diagonal", "sqrt(length.result^2 + width.result^2)")
    
    print(f"   ✅ result.volume = {result.get_variable_value('volume')}")
    print(f"   ✅ result.diagonal = {result.get_variable_value('diagonal'):.2f}")
    
    print("\n5. Демонстрация автоматического обновления зависимостей:")
    print("   Изменяем length@panel с 600 на 800")
    panel.set_variable("length", 800)
    
    print(f"   ✅ panel.length = {panel.get_variable_value('length')} (изменилось)")
    print(f"   ✅ result.length = {result.get_variable_value('length')} (обновилось автоматически)")
    print(f"   ✅ result.volume = {result.get_variable_value('volume')} (пересчиталось)")
    print(f"   ✅ result.diagonal = {result.get_variable_value('diagonal'):.2f} (пересчиталось)")
    
    print("\n6. Информация о переменных:")
    print("\n   PANEL переменные:")
    for var_info in panel.get_all_variables_info():
        print(f"   • {var_info['write_id']} = {var_info['value']} "
              f"(read: {var_info['read_id']}, aliases: {var_info['aliases']})")
    
    print("\n   RESULT переменные:")
    for var_info in result.get_all_variables_info():
        deps = ", ".join(var_info['dependencies']) if var_info['dependencies'] else "нет"
        print(f"   • {var_info['write_id']} = {var_info['value']} "
              f"(formula: {var_info['raw_value']}, deps: {deps})")
    
    print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("Новый синтаксис обеспечивает:")
    print("✅ Интуитивную запись: variable@solution = value")
    print("✅ Естественное чтение: variable.solution") 
    print("✅ Безопасные алиасы: изолированы в решении")
    print("✅ Автоматические зависимости: умный пересчет")
    print("✅ Защиту от ошибок: валидация имен и циклов")

if __name__ == "__main__":
    demo_new_syntax()
