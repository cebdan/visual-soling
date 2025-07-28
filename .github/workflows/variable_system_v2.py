# Variable System V2 - New @ and . addressing
# Новая система адресации переменных: variable@solution и variable.solution

import re
from typing import Dict, List, Set, Optional, Union, Tuple
from enum import Enum

class ExpressionType(Enum):
    """Типы выражений в новой системе"""
    ASSIGNMENT = "assignment"      # length@box=600
    FORMULA = "formula"           # width@result=width.panel-2*thickness.edge  
    READ = "read"                 # a=volume.box
    ALIAS = "alias"               # L=600 (внутри solution)

class ExpressionParser:
    """Парсер новых выражений с @ и . синтаксисом"""
    
    # Паттерны для разбора выражений
    ASSIGNMENT_PATTERN = r'^([a-zA-Z_][a-zA-Z0-9_]*)@([a-zA-Z_][a-zA-Z0-9_]*)=(.+)$'
    READ_PATTERN = r'^([a-zA-Z_][a-zA-Z0-9_]*)=([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)$'
    VARIABLE_REF_PATTERN = r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
    ALIAS_PATTERN = r'^([a-zA-Z_][a-zA-Z0-9_]*)=(.+)$'
    
    @staticmethod
    def parse_expression(expression: str) -> Dict[str, any]:
        """
        Парсить выражение и определить его тип
        
        Примеры:
        - "length@box=600" → assignment
        - "width@result=width.panel-2*thickness.edge" → formula
        - "a=volume.box" → read
        - "L=600" → alias (если внутри solution)
        """
        expression = expression.strip()
        
        # Проверяем assignment (variable@solution=value)
        assignment_match = re.match(ExpressionParser.ASSIGNMENT_PATTERN, expression)
        if assignment_match:
            variable, solution, value_expr = assignment_match.groups()
            
            # Определяем, это значение или формула
            if ExpressionParser._contains_variable_references(value_expr):
                return {
                    'type': ExpressionType.FORMULA,
                    'variable': variable,
                    'solution': solution,
                    'formula': value_expr,
                    'dependencies': ExpressionParser.extract_variable_references(value_expr)
                }
            else:
                return {
                    'type': ExpressionType.ASSIGNMENT,
                    'variable': variable,
                    'solution': solution,
                    'value': ExpressionParser._parse_value(value_expr)
                }
        
        # Проверяем read (variable=other.solution)
        read_match = re.match(ExpressionParser.READ_PATTERN, expression)
        if read_match:
            target_var, source_var, source_solution = read_match.groups()
            return {
                'type': ExpressionType.READ,
                'target_variable': target_var,
                'source_variable': source_var,
                'source_solution': source_solution
            }
        
        # Проверяем alias (L=600) - только если внутри solution
        alias_match = re.match(ExpressionParser.ALIAS_PATTERN, expression)
        if alias_match:
            alias, value_expr = alias_match.groups()
            
            # Проверяем, что алиас не содержит запрещенные символы
            if not ExpressionParser._is_valid_alias(alias):
                raise ValueError(f"Invalid alias '{alias}': cannot contain @ or . symbols")
            
            return {
                'type': ExpressionType.ALIAS,
                'alias': alias,
                'value': ExpressionParser._parse_value(value_expr)
            }
        
        raise ValueError(f"Invalid expression: {expression}")
    
    @staticmethod
    def extract_variable_references(formula: str) -> Set[str]:
        """Извлечь все ссылки на переменные из формулы (variable.solution)"""
        references = set()
        matches = re.findall(ExpressionParser.VARIABLE_REF_PATTERN, formula)
        
        for variable, solution in matches:
            ref = f"{variable}.{solution}"
            references.add(ref)
        
        return references
    
    @staticmethod
    def _contains_variable_references(expression: str) -> bool:
        """Проверить, содержит ли выражение ссылки на переменные"""
        return bool(re.search(ExpressionParser.VARIABLE_REF_PATTERN, expression))
    
    @staticmethod
    def _parse_value(value_str: str) -> Union[int, float, str]:
        """Попытаться преобразовать строку в число"""
        value_str = value_str.strip()
        
        # Пробуем int
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Пробуем float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Возвращаем как строку
        return value_str
    
    @staticmethod
    def _is_valid_alias(alias: str) -> bool:
        """Проверить, что алиас не содержит @ и . символы"""
        return '@' not in alias and '.' not in alias

class V2FormulaEvaluator:
    """Вычислитель формул с новым синтаксисом variable.solution"""
    
    # Поддерживаемые функции (те же что в Advanced)
    FUNCTIONS = {
        'sin': lambda x: __import__('math').sin(x),
        'cos': lambda x: __import__('math').cos(x),
        'tan': lambda x: __import__('math').tan(x),
        'sqrt': lambda x: __import__('math').sqrt(x),
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
    }
    
    @staticmethod
    def evaluate_formula(formula: str, solution_registry: Dict[str, 'V2Solution']) -> float:
        """
        Вычислить формулу с новым синтаксисом
        
        Примеры формул:
        - "width.panel - 2*thickness.edge"
        - "sqrt(length.panel^2 + width.panel^2)"
        - "max(height.box, height.panel, 18)"
        """
        try:
            # Заменяем ссылки на переменные их значениями
            resolved_formula = V2FormulaEvaluator._resolve_variable_references(formula, solution_registry)
            
            # Заменяем ^ на ** для Python
            resolved_formula = resolved_formula.replace('^', '**')
            
            # Создаем безопасный контекст для eval
            safe_dict = {
                "__builtins__": {},
                **V2FormulaEvaluator.FUNCTIONS
            }
            
            # Вычисляем результат
            result = eval(resolved_formula, safe_dict)
            return float(result)
            
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {str(e)}")
    
    @staticmethod
    def _resolve_variable_references(formula: str, solution_registry: Dict[str, 'V2Solution']) -> str:
        """Заменить ссылки variable.solution их значениями"""
        def replace_reference(match):
            variable_name = match.group(1)
            solution_name = match.group(2)
            full_ref = f"{variable_name}.{solution_name}"
            
            # Получаем solution
            solution = solution_registry.get(solution_name)
            if solution is None:
                raise ValueError(f"Solution '{solution_name}' not found")
            
            # Получаем переменную
            variable = solution.get_variable(variable_name)
            if variable is None:
                raise ValueError(f"Variable '{variable_name}' not found in solution '{solution_name}'")
            
            # Получаем значение
            value = variable.get_computed_value() if variable.is_formula else variable.value
            
            if not isinstance(value, (int, float)):
                raise ValueError(f"Variable '{full_ref}' is not numeric: {value}")
            
            return str(value)
        
        # Заменяем все ссылки на переменные
        resolved = re.sub(ExpressionParser.VARIABLE_REF_PATTERN, replace_reference, formula)
        return resolved

class V2Variable:
    """Переменная с новой системой адресации"""
    
    def __init__(self, name: str, value: any, solution_name: str):
        self.name: str = name
        self.solution_name: str = solution_name
        self._value: any = value
        
        # Формулы и зависимости
        self.is_formula: bool = False
        self.formula: str = None
        self.dependencies: Set[str] = set()
        self.last_computed_value: any = None
        self.computation_error: str = None
    
    @property
    def full_id(self) -> str:
        """Полный ID переменной: variable@solution"""
        return f"{self.name}@{self.solution_name}"
    
    @property
    def read_id(self) -> str:
        """ID для чтения: variable.solution"""
        return f"{self.name}.{self.solution_name}"
    
    @property
    def value(self) -> any:
        """Получить значение переменной"""
        if self.is_formula:
            return self.get_computed_value()
        return self._value
    
    @value.setter
    def value(self, new_value):
        """Установить значение переменной"""
        self._value = new_value
        self.is_formula = False
        self.formula = None
        self.dependencies.clear()
        self.computation_error = None
    
    def set_formula(self, formula: str, solution_registry: Dict[str, 'V2Solution']):
        """Установить формулу для переменной"""
        self.formula = formula
        self.is_formula = True
        
        # Извлекаем зависимости
        self.dependencies = ExpressionParser.extract_variable_references(formula)
        
        # Вычисляем начальное значение
        try:
            self.last_computed_value = V2FormulaEvaluator.evaluate_formula(formula, solution_registry)
            self.computation_error = None
        except Exception as e:
            self.computation_error = str(e)
            self.last_computed_value = 0.0
    
    def get_computed_value(self, solution_registry: Dict[str, 'V2Solution'] = None) -> any:
        """Вычислить значение формулы"""
        if not self.is_formula:
            return self._value
        
        if solution_registry is None:
            return self.last_computed_value if self.last_computed_value is not None else 0.0
        
        try:
            computed = V2FormulaEvaluator.evaluate_formula(self.formula, solution_registry)
            self.last_computed_value = computed
            self.computation_error = None
            return computed
        except Exception as e:
            self.computation_error = str(e)
            return self.last_computed_value if self.last_computed_value is not None else 0.0
    
    def __str__(self):
        if self.is_formula:
            return f"{self.full_id} = {self.formula} → {self.get_computed_value()}"
        else:
            return f"{self.full_id} = {self._value}"

class V2Solution:
    """Solution с новой системой переменных"""
    
    def __init__(self, name: str):
        self.name: str = name
        self.variables: Dict[str, V2Variable] = {}
        self.aliases: Dict[str, str] = {}  # {alias: variable_name}
        
    def create_variable(self, name: str, value: any = None) -> V2Variable:
        """Создать переменную"""
        variable = V2Variable(name, value, self.name)
        self.variables[name] = variable
        return variable
    
    def get_variable(self, name_or_alias: str) -> Optional[V2Variable]:
        """Получить переменную по имени или алиасу"""
        # Сначала проверяем прямое имя
        if name_or_alias in self.variables:
            return self.variables[name_or_alias]
        
        # Затем проверяем алиасы
        if name_or_alias in self.aliases:
            real_name = self.aliases[name_or_alias]
            return self.variables.get(real_name)
        
        return None
    
    def set_alias(self, alias: str, variable_name: str):
        """Установить алиас для переменной"""
        if not ExpressionParser._is_valid_alias(alias):
            raise ValueError(f"Invalid alias '{alias}': cannot contain @ or . symbols")
        
        if variable_name not in self.variables:
            raise ValueError(f"Variable '{variable_name}' not found")
        
        self.aliases[alias] = variable_name
    
    def execute_expression(self, expression: str, solution_registry: Dict[str, 'V2Solution']):
        """Выполнить выражение с новым синтаксисом"""
        parsed = ExpressionParser.parse_expression(expression)
        
        if parsed['type'] == ExpressionType.ASSIGNMENT:
            # variable@solution=value
            var_name = parsed['variable']
            if parsed['solution'] != self.name:
                raise ValueError(f"Cannot assign to variable in different solution: {parsed['solution']}")
            
            # Создаем или обновляем переменную
            if var_name not in self.variables:
                self.create_variable(var_name)
            
            self.variables[var_name].value = parsed['value']
            
        elif parsed['type'] == ExpressionType.FORMULA:
            # variable@solution=formula
            var_name = parsed['variable']
            if parsed['solution'] != self.name:
                raise ValueError(f"Cannot assign to variable in different solution: {parsed['solution']}")
            
            # Создаем или обновляем переменную
            if var_name not in self.variables:
                self.create_variable(var_name)
            
            self.variables[var_name].set_formula(parsed['formula'], solution_registry)
            
        elif parsed['type'] == ExpressionType.ALIAS:
            # L=600 (внутри solution)
            alias = parsed['alias']
            value = parsed['value']
            
            # Создаем временную переменную для алиаса если её нет
            if alias not in self.variables and alias not in self.aliases:
                var = self.create_variable(f"_alias_{alias}")
                var.value = value
                self.set_alias(alias, var.name)
            else:
                # Обновляем существующую
                var = self.get_variable(alias)
                if var:
                    var.value = value
        
        else:
            raise ValueError(f"Cannot execute expression type: {parsed['type']}")
    
    def get_all_variables(self) -> List[V2Variable]:
        """Получить все переменные"""
        return list(self.variables.values())
    
    def debug_info(self) -> str:
        """Отладочная информация"""
        info = f"Solution '{self.name}':\n"
        info += f"Variables ({len(self.variables)}):\n"
        
        for var in self.variables.values():
            info += f"  {var}\n"
        
        if self.aliases:
            info += f"Aliases ({len(self.aliases)}):\n"
            for alias, var_name in self.aliases.items():
                info += f"  {alias} → {var_name}\n"
        
        return info

# Демонстрационные функции
def demo_new_syntax():
    """Демонстрация новой системы адресации"""
    print("=== DEMO: Новая система переменных V2 ===")
    
    # Создаем registry решений
    solutions = {}
    
    # Solution "box"
    box = V2Solution("box")
    solutions["box"] = box
    
    # Solution "edge"
    edge = V2Solution("edge")
    solutions["edge"] = edge
    
    # Solution "result"
    result = V2Solution("result")
    solutions["result"] = result
    
    print("\n1. Создание переменных через новый синтаксис:")
    
    # Создаем переменные в box
    box.execute_expression("length@box=600", solutions)
    box.execute_expression("width@box=400", solutions)
    box.execute_expression("height@box=18", solutions)
    
    print(f"box.length = {box.get_variable('length').value}")
    print(f"box.width = {box.get_variable('width').value}")
    print(f"box.height = {box.get_variable('height').value}")
    
    # Создаем переменные в edge
    edge.execute_expression("thickness@edge=2", solutions)
    edge.execute_expression("material@edge=white", solutions)
    
    print(f"edge.thickness = {edge.get_variable('thickness').value}")
    print(f"edge.material = {edge.get_variable('material').value}")
    
    print("\n2. Формулы с новым синтаксисом:")
    
    # Формулы в result
    result.execute_expression("length@result=length.box", solutions)
    result.execute_expression("width@result=width.box - 2*thickness.edge", solutions)
    result.execute_expression("height@result=height.box", solutions)
    
    print(f"result.length = {result.get_variable('length').value}")
    print(f"result.width = {result.get_variable('width').value}")
    print(f"result.height = {result.get_variable('height').value}")
    
    print("\n3. Алиасы (локальные):")
    
    # Алиасы в box
    box.set_alias("L", "length")
    box.set_alias("W", "width")
    box.set_alias("H", "height")
    
    print(f"box.L (alias) = {box.get_variable('L').value}")
    print(f"box.W (alias) = {box.get_variable('W').value}")
    print(f"box.H (alias) = {box.get_variable('H').value}")
    
    print("\n4. Обновление и автопересчет:")
    
    # Изменяем значение
    box.execute_expression("width@box=500", solutions)
    
    # Пересчитываем зависимые
    result.get_variable('width').get_computed_value(solutions)
    
    print(f"После изменения box.width:")
    print(f"box.width = {box.get_variable('width').value}")
    print(f"result.width = {result.get_variable('width').value}")
    
    print("\n5. Математические функции:")
    
    # Диагональ
    result.execute_expression("diagonal@result=sqrt(length.box^2 + width.box^2)", solutions)
    print(f"result.diagonal = {result.get_variable('diagonal').value:.2f}")
    
    # Максимум
    result.execute_expression("max_size@result=max(length.box, width.box, height.box)", solutions)
    print(f"result.max_size = {result.get_variable('max_size').value}")
    
    print("\n=== Отладочная информация ===")
    print(box.debug_info())
    print(edge.debug_info())
    print(result.debug_info())

if __name__ == "__main__":
    demo_new_syntax()
