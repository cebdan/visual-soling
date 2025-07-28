# Visual Solving Advanced V2 - Hybrid System (V2 + Legacy)
# Исправленная версия с правильным порядком создания переменных

import re
from typing import Dict, List, Set, Optional, Union, Tuple, Any
from enum import Enum
import uuid
import json

# Импорт новой системы V2
try:
    from variable_system_v2 import (
        ExpressionParser, V2FormulaEvaluator, V2Variable, V2Solution,
        ExpressionType
    )
    V2_AVAILABLE = True
except ImportError as e:
    print(f"Ошибка импорта V2 системы: {e}")
    V2_AVAILABLE = False

# =============================================================================
# Типы переменных и зависимостей
# =============================================================================

class VariableType(Enum):
    """Типы переменных в системе"""
    CONTROLLABLE = "controllable"  # Управляемые пользователем
    CALCULATED = "calculated"     # Вычисляемые по формуле
    AUXILIARY = "auxiliary"       # Вспомогательные
    REFERENCE = "reference"       # Ссылки на другие переменные

class IntegrationType(Enum):
    """Типы интеграции решений"""
    ADDITION = "addition"         # Сложение (пример: panel + edge)
    SUBTRACTION = "subtraction"   # Вычитание (пример: panel - hole)
    MODIFICATION = "modification" # Модификация (пример: color, material)
    ASSEMBLY = "assembly"         # Сборка (пример: cabinet assembly)

# =============================================================================
# Гибридная переменная (V2 + Legacy)
# =============================================================================

class HybridVariable:
    """Переменная, поддерживающая и V2, и Legacy синтаксис"""
    
    def __init__(self, name: str, value: any, var_type: VariableType, 
                 solution_name: str, variable_id: int, aliases: List[str] = None):
        self.name = name
        self.solution_name = solution_name
        self.variable_id = variable_id  # Legacy #number
        self.var_type = var_type
        self.aliases = aliases or []
        
        # V2 переменная (создаётся автоматически)
        if V2_AVAILABLE:
            self.v2_variable = V2Variable(name, value, solution_name)
        else:
            self.v2_variable = None
            self._value = value
    
    @property
    def value(self) -> any:
        """Получить значение переменной"""
        if self.v2_variable:
            return self.v2_variable.value
        return self._value
    
    @value.setter  
    def value(self, new_value):
        """Установить значение переменной"""
        if self.v2_variable:
            self.v2_variable.value = new_value
        else:
            self._value = new_value
    
    @property
    def legacy_id(self) -> str:
        """Legacy ID: #number"""
        return f"#{self.variable_id}"
    
    @property
    def legacy_full_id(self) -> str:
        """Legacy полный ID: #number.name"""
        return f"#{self.variable_id}.{self.name}"
    
    @property
    def new_write_id(self) -> str:
        """Новый ID для записи: variable@solution"""
        return f"{self.name}@{self.solution_name}"
    
    @property
    def new_read_id(self) -> str:
        """Новый ID для чтения: variable.solution"""
        return f"{self.name}.{self.solution_name}"
    
    def set_formula(self, formula: str, solution_registry: Dict[str, 'V2Solution']):
        """Установить формулу V2"""
        if self.v2_variable:
            self.v2_variable.set_formula(formula, solution_registry)
    
    def get_computed_value(self, solution_registry: Dict[str, 'V2Solution'] = None) -> any:
        """Вычислить значение формулы"""
        if self.v2_variable:
            return self.v2_variable.get_computed_value(solution_registry)
        return self.value
    
    def __str__(self):
        return f"HybridVar({self.new_write_id} = {self.value}, legacy: {self.legacy_id})"

# =============================================================================
# Менеджер гибридных решений V2
# =============================================================================

class V2SolutionManager:
    """Менеджер для управления решениями V2"""
    
    def __init__(self):
        self.solutions: Dict[str, 'HybridSolution'] = {}
        self.v2_solutions: Dict[str, V2Solution] = {}
    
    def register_solution(self, solution: 'HybridSolution'):
        """Зарегистрировать решение"""
        self.solutions[solution.name] = solution
        if solution.v2_solution:
            self.v2_solutions[solution.name] = solution.v2_solution
    
    def get_solution(self, name: str) -> Optional['HybridSolution']:
        """Получить решение по имени"""
        return self.solutions.get(name)
    
    def get_all_solutions(self) -> Dict[str, V2Solution]:
        """Получить все V2 решения для формул"""
        return self.v2_solutions
    
    def reset(self):
        """Сбросить все решения"""
        self.solutions.clear()
        self.v2_solutions.clear()

# Глобальный менеджер решений V2
v2_solution_manager = V2SolutionManager()

# =============================================================================
# Трекер зависимостей V2
# =============================================================================

class V2DependencyTracker:
    """Отслеживание зависимостей между переменными V2"""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = {}  # variable.solution -> dependencies
        self.reverse_dependencies: Dict[str, Set[str]] = {}  # variable.solution -> dependents
    
    def add_dependency(self, variable_id: str, dependencies: Set[str]):
        """Добавить зависимости для переменной"""
        self.dependency_graph[variable_id] = dependencies
        
        # Обновляем обратные зависимости
        for dep in dependencies:
            if dep not in self.reverse_dependencies:
                self.reverse_dependencies[dep] = set()
            self.reverse_dependencies[dep].add(variable_id)
    
    def get_dependencies(self, variable_id: str) -> Set[str]:
        """Получить зависимости переменной"""
        return self.dependency_graph.get(variable_id, set())
    
    def get_dependent_variables(self, variable_id: str) -> Set[str]:
        """Получить переменные, зависящие от данной"""
        return self.reverse_dependencies.get(variable_id, set())
    
    def has_circular_dependency(self, variable_id: str, dependencies: Set[str]) -> bool:
        """Проверить наличие циклических зависимостей"""
        visited = set()
        
        def check_circular(var_id: str, path: Set[str]) -> bool:
            if var_id in path:
                return True
            if var_id in visited:
                return False
            
            visited.add(var_id)
            path.add(var_id)
            
            var_deps = self.dependency_graph.get(var_id, set())
            for dep in var_deps:
                if check_circular(dep, path):
                    return True
            
            path.remove(var_id)
            return False
        
        return check_circular(variable_id, set())

# Глобальный трекер зависимостей
v2_dependency_tracker = V2DependencyTracker()

# =============================================================================
# Глобальный реестр переменных V2
# =============================================================================

class V2GlobalVariableRegistry:
    """Глобальный реестр всех переменных V2 в системе"""
    
    @staticmethod
    def get_all_variables_info() -> List[Dict[str, any]]:
        """Получить информацию о всех переменных в системе"""
        variables_info = []
        
        for solution_name, solution in v2_solution_manager.solutions.items():
            for var in solution.get_all_variables():
                var_info = {
                    'name': var.name,
                    'solution_name': solution_name,
                    'value': var.value,
                    'type': var.var_type.value,
                    'variable_id': var.variable_id,
                    'legacy_id': var.legacy_id,
                    'legacy_full_id': var.legacy_full_id,
                    'new_write_id': var.new_write_id,
                    'new_read_id': var.new_read_id,
                    'aliases': var.aliases,
                    'is_formula': var.v2_variable.is_formula if var.v2_variable else False,
                    'formula': var.v2_variable.formula if var.v2_variable and var.v2_variable.is_formula else None,
                    'computed_value': var.get_computed_value() if var.v2_variable and var.v2_variable.is_formula else var.value,
                    'dependencies': list(var.v2_variable.dependencies) if var.v2_variable else [],
                    'dependents': list(v2_dependency_tracker.get_dependent_variables(var.new_read_id))
                }
                variables_info.append(var_info)
        
        return variables_info
    
    @staticmethod
    def find_variable_by_reference(reference: str) -> Optional[HybridVariable]:
        """Найти переменную по любому типу ссылки"""
        for solution in v2_solution_manager.solutions.values():
            var = solution.get_variable_by_reference(reference)
            if var:
                return var
        return None

# =============================================================================
# Базовое гибридное решение (V2 + Legacy)
# =============================================================================

class HybridSolution:
    """Базовое решение с поддержкой V2 и Legacy синтаксиса"""
    
    def __init__(self, name: str):
        self.name = name
        self.solution_id = str(uuid.uuid4())
        
        # V2 система
        if V2_AVAILABLE:
            self.v2_solution = V2Solution(name)
        else:
            self.v2_solution = None
        
        # Legacy система  
        self.variables: Dict[str, HybridVariable] = {}
        self.next_variable_id = 1
        
        # Метаданные
        self.attributes: Dict[str, any] = {}
        self.parent_solutions: List['HybridSolution'] = []
        self.child_solutions: List['HybridSolution'] = []
        self.containing_space: Optional['Part3DSpace'] = None
        
        # Регистрируем в менеджере
        v2_solution_manager.register_solution(self)
    
    def create_variable(self, name: str, value: any, var_type: VariableType, aliases: List[str] = None) -> HybridVariable:
        """Создать переменную с поддержкой V2 и Legacy"""
        aliases = aliases or []
        
        # Создаём V2 переменную сначала
        if self.v2_solution:
            self.v2_solution.create_variable(name, value)
        
        # Создаём гибридную переменную
        hybrid_var = HybridVariable(name, value, var_type, self.name, self.next_variable_id, aliases)
        self.variables[name] = hybrid_var
        self.next_variable_id += 1
        
        # Устанавливаем алиасы ПОСЛЕ создания переменной
        if self.v2_solution and aliases:
            for alias in aliases:
                try:
                    self.v2_solution.set_alias(alias, name)
                except ValueError as e:
                    print(f"Warning: Could not set alias '{alias}' for '{name}': {e}")
        
        return hybrid_var
    
    def get_variable_by_reference(self, reference: str) -> Optional[HybridVariable]:
        """Получить переменную по любому типу ссылки"""
        reference = reference.strip()
        
        # Прямое имя переменной
        if reference in self.variables:
            return self.variables[reference]
        
        # Legacy #number ссылка
        if reference.startswith('#'):
            try:
                var_id = int(reference[1:])
                for var in self.variables.values():
                    if var.variable_id == var_id:
                        return var
            except ValueError:
                pass
        
        # Legacy #number.name ссылка
        if '.' in reference and reference.startswith('#'):
            try:
                parts = reference.split('.')
                var_id = int(parts[0][1:])
                for var in self.variables.values():
                    if var.variable_id == var_id:
                        return var
            except (ValueError, IndexError):
                pass
        
        # V2 алиас
        if self.v2_solution:
            v2_var = self.v2_solution.get_variable(reference)
            if v2_var:
                # Найти соответствующую гибридную переменную
                for var in self.variables.values():
                    if var.v2_variable is v2_var:
                        return var
        
        # Поиск по алиасам в Legacy
        for var in self.variables.values():
            if reference in var.aliases:
                return var
        
        return None
    
    def execute_v2_expression(self, expression: str):
        """Выполнить выражение V2"""
        if not self.v2_solution:
            raise ValueError("V2 system not available")
        
        solution_registry = v2_solution_manager.get_all_solutions()
        self.v2_solution.execute_expression(expression, solution_registry)
        
        # Обновляем зависимости
        try:
            parsed = ExpressionParser.parse_expression(expression)
            if parsed['type'] in [ExpressionType.FORMULA]:
                var_name = parsed['variable']
                dependencies = parsed['dependencies']
                
                var = self.get_variable_by_reference(var_name)
                if var:
                    v2_dependency_tracker.add_dependency(var.new_read_id, dependencies)
        except Exception as e:
            print(f"Warning: Could not update dependencies for '{expression}': {e}")
    
    def get_all_variables(self) -> List[HybridVariable]:
        """Получить все переменные"""
        return list(self.variables.values())
    
    def place_in_space(self, space: 'Part3DSpace'):
        """Разместить решение в пространстве"""
        self.containing_space = space
        space.add_solution(self)
    
    def debug_variables(self):
        """Отладочная информация о переменных"""
        print(f"\n=== Solution '{self.name}' Variables Debug ===")
        for var in self.variables.values():
            print(f"  {var}")
            print(f"    Legacy: {var.legacy_full_id}")
            print(f"    V2 Write: {var.new_write_id}")
            print(f"    V2 Read: {var.new_read_id}")
            if var.aliases:
                print(f"    Aliases: {var.aliases}")
            if var.v2_variable and var.v2_variable.is_formula:
                print(f"    Formula: {var.v2_variable.formula}")

# =============================================================================
# Специализированные решения
# =============================================================================

class HybridBoxSolution(HybridSolution):
    """Коробка с поддержкой V2 синтаксиса"""
    
    def __init__(self, name: str, length: Union[float, str], width: Union[float, str], height: Union[float, str]):
        super().__init__(name)
        self._setup_variables(length, width, height)
        self._setup_attributes()
    
    def _setup_variables(self, length, width, height):
        """Настроить переменные коробки"""
        # Создаём переменные
        length_var = self.create_variable("length", 0, VariableType.CONTROLLABLE, ["L", "len"])
        width_var = self.create_variable("width", 0, VariableType.CONTROLLABLE, ["W", "wid"])
        height_var = self.create_variable("height", 0, VariableType.CONTROLLABLE, ["H", "hei"])
        
        # Устанавливаем значения или формулы
        self._set_dimension_value(length_var, length, "length")
        self._set_dimension_value(width_var, width, "width")
        self._set_dimension_value(height_var, height, "height")
        
        # Создаём вычисляемые переменные
        self.create_variable("volume", 0, VariableType.CALCULATED, ["vol"])
        if self.v2_solution:
            self.execute_v2_expression("volume@{0}=length.{0} * width.{0} * height.{0}".format(self.name))
    
    def _set_dimension_value(self, var: HybridVariable, value: Union[float, str], dimension_name: str):
        """Установить значение размера (число или формула V2)"""
        if isinstance(value, (int, float)):
            var.value = float(value)
        elif isinstance(value, str):
            # Это формула V2
            if self.v2_solution:
                expression = f"{dimension_name}@{self.name}={value}"
                self.execute_v2_expression(expression)
            else:
                # Fallback: пытаемся преобразовать в число
                try:
                    var.value = float(value)
                except ValueError:
                    var.value = 0.0
                    print(f"Warning: Could not parse '{value}' as number or V2 formula")
    
    def _setup_attributes(self):
        """Настроить атрибуты коробки"""
        self.attributes.update({
            'material': 'chipboard',
            'color': 'natural',
            'finish': 'none',
            'visible': True
        })
    
    @property
    def length(self) -> float:
        """Длина коробки"""
        var = self.get_variable_by_reference("length")
        return var.get_computed_value() if var else 0.0
    
    @property
    def width(self) -> float:
        """Ширина коробки"""
        var = self.get_variable_by_reference("width")
        return var.get_computed_value() if var else 0.0
    
    @property
    def height(self) -> float:
        """Высота коробки"""
        var = self.get_variable_by_reference("height")
        return var.get_computed_value() if var else 0.0
    
    @property
    def volume(self) -> float:
        """Объём коробки"""
        var = self.get_variable_by_reference("volume")
        return var.get_computed_value() if var else 0.0

class HybridEdgeBandingSolution(HybridSolution):
    """Кромкование с поддержкой V2 синтаксиса"""
    
    def __init__(self, name: str, material: str, thickness: float, edges: List[str]):
        super().__init__(name)
        self._setup_variables(material, thickness, edges)
    
    def _setup_variables(self, material, thickness, edges):
        """Настроить переменные кромкования"""
        self.create_variable("material", material, VariableType.CONTROLLABLE, ["mat"])
        self.create_variable("thickness", thickness, VariableType.CONTROLLABLE, ["thick", "t"])
        self.create_variable("edges_count", len(edges), VariableType.CALCULATED, ["count"])
        
        # Сохраняем список кромок как атрибут
        self.attributes['edges'] = edges
    
    def apply_to(self, panel: HybridBoxSolution) -> HybridBoxSolution:
        """Применить кромкование к панели"""
        # Создаём новое решение как результат
        result_name = f"{panel.name}_edged"
        
        # Вычисляем новые размеры с учётом кромки
        edges = self.attributes.get('edges', [])
        thickness = self.get_variable_by_reference("thickness").value
        
        length_reduction = 2 * thickness if 'front' in edges or 'back' in edges else 0
        width_reduction = 2 * thickness if 'left' in edges or 'right' in edges else 0
        
        # Создаём результирующую панель
        if self.v2_solution:
            # Используем V2 формулы
            result = HybridBoxSolution(
                result_name,
                f"length.{panel.name} - {length_reduction}",
                f"width.{panel.name} - {width_reduction}",
                f"height.{panel.name}"
            )
        else:
            # Fallback: числовые значения
            result = HybridBoxSolution(
                result_name,
                panel.length - length_reduction,
                panel.width - width_reduction,
                panel.height
            )
        
        # Устанавливаем связи
        result.parent_solutions = [panel, self]
        panel.child_solutions.append(result)
        self.child_solutions.append(result)
        
        return result

# =============================================================================
# Пространство для размещения решений
# =============================================================================

class Part3DSpace:
    """3D пространство для размещения решений"""
    
    def __init__(self, name: str):
        self.name = name
        self.space_id = str(uuid.uuid4())
        self.solutions: List[HybridSolution] = []
        self.coordinate_system = "cartesian"  # или "cylindrical", "spherical"
        
    def add_solution(self, solution: HybridSolution):
        """Добавить решение в пространство"""
        if solution not in self.solutions:
            self.solutions.append(solution)
            solution.containing_space = self
    
    def remove_solution(self, solution: HybridSolution):
        """Удалить решение из пространства"""
        if solution in self.solutions:
            self.solutions.remove(solution)
            solution.containing_space = None
    
    def get_solutions_by_type(self, solution_type: type) -> List[HybridSolution]:
        """Получить решения определённого типа"""
        return [sol for sol in self.solutions if isinstance(sol, solution_type)]

# =============================================================================
# Демонстрационные функции
# =============================================================================

def demo_hybrid_system():
    """Демонстрация гибридной системы V2 + Legacy"""
    print("ДЕМОНСТРАЦИЯ ГИБРИДНОЙ СИСТЕМЫ V2")
    print("=" * 50)
    
    try:
        # Сбрасываем состояние
        v2_solution_manager.reset()
        
        print("1. Создание решений с новым синтаксисом:")
        
        # Базовая панель
        panel = HybridBoxSolution("panel", 600, 400, 18)
        print(f"✅ Панель: {panel.length} x {panel.width} x {panel.height}")
        
        # Кромка
        edge = HybridEdgeBandingSolution("edge", "white", 2.0, ["top", "bottom"])
        print(f"✅ Кромка: {edge.get_variable_by_reference('material').value}, толщина {edge.get_variable_by_reference('thickness').value}")
        
        print("\n2. V2 синтаксис в действии:")
        
        # Создаём результирующую панель с V2 формулами
        result = HybridBoxSolution(
            "result",
            "length.panel",                    # V2 синтаксис!
            "width.panel - 2*thickness.edge", # V2 синтаксис!
            "height.panel"                     # V2 синтаксис!
        )
        
        print(f"✅ Результат: {result.length:.1f} x {result.width:.1f} x {result.height:.1f}")
        print(f"   Формула ширины: width.panel - 2*thickness.edge = {panel.width} - 2*{edge.get_variable_by_reference('thickness').value} = {result.width}")
        
        print("\n3. Двойная адресация (V2 + Legacy):")
        
        var = panel.get_variable_by_reference("length")
        print(f"Переменная длины панели:")
        print(f"  Legacy ID: {var.legacy_id}")
        print(f"  Legacy Full: {var.legacy_full_id}")
        print(f"  V2 Write: {var.new_write_id}")
        print(f"  V2 Read: {var.new_read_id}")
        print(f"  Алиасы: {var.aliases}")
        
        print("\n4. Математические функции V2:")
        
        # Панель с математикой
        math_panel = HybridBoxSolution(
            "math",
            "sqrt(length.panel^2 + width.panel^2)",  # Диагональ
            "max(width.panel, width.result, 350)",   # Максимум
            "height.panel * 2"                       # Удвоенная высота
        )
        
        print(f"✅ Математическая панель:")
        print(f"  Длина (диагональ): {math_panel.length:.1f}")
        print(f"  Ширина (максимум): {math_panel.width:.1f}")
        print(f"  Высота (удвоенная): {math_panel.height:.1f}")
        
        print("\n5. Глобальный реестр переменных:")
        all_vars = V2GlobalVariableRegistry.get_all_variables_info()
        print(f"Всего переменных в системе: {len(all_vars)}")
        
        for var_info in all_vars[:5]:  # Показываем первые 5
            print(f"  {var_info['new_write_id']}: {var_info['computed_value']}")
        
        print("\n✅ Демонстрация гибридной системы завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка в демонстрации: {e}")
        import traceback
        traceback.print_exc()

def demo_expression_parsing():
    """Демонстрация парсинга выражений V2"""
    print("ДЕМОНСТРАЦИЯ ПАРСИНГА ВЫРАЖЕНИЙ V2")
    print("=" * 40)
    
    if not V2_AVAILABLE:
        print("❌ V2 система недоступна")
        return
    
    expressions = [
        "length@panel=600",
        "width@result=width.panel - 2*thickness.edge",
        "diagonal@math=sqrt(length.panel^2 + width.panel^2)",
        "a=volume.panel",
        "L=600"
    ]
    
    for expr in expressions:
        try:
            parsed = ExpressionParser.parse_expression(expr)
            print(f"✅ {expr}")
            print(f"   Тип: {parsed['type'].value}")
            
            if 'dependencies' in parsed:
                print(f"   Зависимости: {parsed['dependencies']}")
            
        except Exception as e:
            print(f"❌ {expr}: {e}")
        
        print()

if __name__ == "__main__":
    print("Visual Solving Advanced V2 - Hybrid System")
    print("==========================================")
    demo_hybrid_system()
    print()
    demo_expression_parsing()
