# Visual Solving MVP - Иерархическая система адресации
# Каждый Solution имеет номер #x, переменные #x.1, #x.2, #x.length

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json
import uuid

# =============================================================================
# Глобальный менеджер номеров Solution
# =============================================================================

class SolutionNumberManager:
    """Глобальный менеджер для выдачи уникальных номеров Solution"""
    _instance = None
    _next_number = 1
    _solution_registry = {}  # {number: solution}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_next_number(self) -> int:
        """Получить следующий уникальный номер для Solution"""
        number = self._next_number
        self._next_number += 1
        return number
    
    def register_solution(self, number: int, solution: 'Solution'):
        """Зарегистрировать Solution под номером"""
        self._solution_registry[number] = solution
    
    def get_solution_by_number(self, number: int) -> Optional['Solution']:
        """Получить Solution по номеру"""
        return self._solution_registry.get(number)
    
    def reset(self):
        """Сброс для тестирования"""
        self._next_number = 1
        self._solution_registry.clear()

# Глобальный экземпляр менеджера
solution_number_manager = SolutionNumberManager()

# =============================================================================
# Иерархическая система переменных
# =============================================================================

class VariableType(Enum):
    INTERNAL = "internal"
    CONTROLLABLE = "controllable"
    DERIVED = "derived"

class HierarchicalVariable:
    """Переменная с иерархической адресацией #solution_number.variable_number"""
    
    def __init__(self, name: str, value: Any, var_type: VariableType, solution_number: int):
        self.solution_number: int = solution_number
        self.variable_number: int = 0  # Будет установлен менеджером
        self.name: str = name
        self.value: Any = value
        self.variable_type: VariableType = var_type
        self.aliases: List[str] = []
    
    @property
    def full_id(self) -> str:
        """Полный ID переменной: #1.2"""
        return f"#{self.solution_number}.{self.variable_number}"
    
    @property
    def named_id(self) -> str:
        """Именованный ID: #1.length"""
        return f"#{self.solution_number}.{self.name}"
    
    def add_alias(self, alias: str):
        if alias not in self.aliases:
            self.aliases.append(alias)
    
    def __str__(self):
        return f"{self.full_id} ({self.named_id}) = {self.value}"

class HierarchicalVariableManager:
    """Менеджер переменных с иерархической адресацией"""
    
    def __init__(self, solution_number: int):
        self.solution_number: int = solution_number
        self._variables: Dict[int, HierarchicalVariable] = {}  # {var_number: variable}
        self._name_map: Dict[str, int] = {}  # {name: var_number}
        self._alias_map: Dict[str, int] = {}  # {alias: var_number}
        self._next_var_number: int = 1
    
    def create_variable(self, name: str, value: Any, var_type: VariableType, aliases: List[str] = None) -> HierarchicalVariable:
        """Создать переменную с иерархической адресацией"""
        var = HierarchicalVariable(name, value, var_type, self.solution_number)
        var.variable_number = self._next_var_number
        
        # Сохраняем переменную
        self._variables[self._next_var_number] = var
        self._name_map[name] = self._next_var_number
        
        # Добавляем алиасы
        if aliases:
            for alias in aliases:
                var.add_alias(alias)
                self._alias_map[alias] = self._next_var_number
        
        self._next_var_number += 1
        return var
    
    def get_variable_by_reference(self, reference: str) -> Optional[HierarchicalVariable]:
        """
        Получить переменную по ссылке:
        - "#1.2" - по полному ID
        - "#1.length" - по именованному ID  
        - "length" - по локальному имени (в рамках этого Solution)
        - "L" - по локальному алиасу
        """
        
        # Полный ID: #1.2
        if reference.startswith('#') and '.' in reference:
            try:
                parts = reference[1:].split('.')
                solution_num = int(parts[0])
                
                # Проверяем, что это наш Solution
                if solution_num != self.solution_number:
                    return None
                
                # Второй элемент может быть числом или именем
                second_part = parts[1]
                
                # Пробуем как число: #1.2
                try:
                    var_number = int(second_part)
                    return self._variables.get(var_number)
                except ValueError:
                    # Пробуем как имя: #1.length
                    var_number = self._name_map.get(second_part)
                    if var_number:
                        return self._variables.get(var_number)
                    
                    # Пробуем как алиас: #1.L
                    var_number = self._alias_map.get(second_part)
                    if var_number:
                        return self._variables.get(var_number)
                        
            except (ValueError, IndexError):
                return None
        
        # Локальное имя: "length"
        var_number = self._name_map.get(reference)
        if var_number:
            return self._variables.get(var_number)
        
        # Локальный алиас: "L"
        var_number = self._alias_map.get(reference)
        if var_number:
            return self._variables.get(var_number)
        
        return None
    
    def get_all_variables(self) -> List[HierarchicalVariable]:
        """Получить все переменные"""
        return list(self._variables.values())
    
    def get_variable_info(self) -> Dict[str, Any]:
        """Получить информацию о всех переменных для отладки"""
        info = {
            "solution_number": self.solution_number,
            "variables": {},
            "name_mappings": {},
            "alias_mappings": {}
        }
        
        for var in self._variables.values():
            info["variables"][var.full_id] = {
                "name": var.name,
                "named_id": var.named_id,
                "value": var.value,
                "type": var.variable_type.value,
                "aliases": var.aliases
            }
        
        # Показать все возможные способы обращения
        for var in self._variables.values():
            # По имени
            info["name_mappings"][var.name] = var.full_id
            info["name_mappings"][var.named_id] = var.full_id
            info["name_mappings"][var.full_id] = var.full_id
            
            # По алиасам
            for alias in var.aliases:
                info["alias_mappings"][alias] = var.full_id
                info["alias_mappings"][f"#{self.solution_number}.{alias}"] = var.full_id
        
        return info

# =============================================================================
# Пространственная система (без изменений)
# =============================================================================

class CoordinateSystem:
    def __init__(self, origin=(0, 0, 0), rotation=(0, 0, 0)):
        self.origin = origin
        self.rotation = rotation

class Space(ABC):
    def __init__(self, name: str):
        self.name: str = name
        self.coordinate_system: CoordinateSystem = CoordinateSystem()
        self.child_spaces: List[Space] = []
        self.solutions: List['Solution'] = []
    
    def add_solution(self, solution: 'Solution'):
        if solution not in self.solutions:
            self.solutions.append(solution)
            solution.containing_space = self

class Part3DSpace(Space):
    def __init__(self, name: str):
        super().__init__(name)

# =============================================================================
# Иерархическая система решений
# =============================================================================

class IntegrationType(Enum):
    UNION = "union"
    DIFFERENCE = "difference"
    MODIFICATION = "modification"

class Solution(ABC):
    def __init__(self, name: str):
        self.solution_id: str = str(uuid.uuid4())
        self.name: str = name
        
        # Получаем уникальный номер Solution
        self.solution_number: int = solution_number_manager.get_next_number()
        solution_number_manager.register_solution(self.solution_number, self)
        
        # Создаем менеджер переменных с нашим номером
        self.variables: HierarchicalVariableManager = HierarchicalVariableManager(self.solution_number)
        
        self.containing_space: Optional[Space] = None
        self.parent_solutions: List[Solution] = []
        self.child_solutions: List[Solution] = []
        self.coordinate_system: CoordinateSystem = CoordinateSystem()
    
    def place_in_space(self, space: Space):
        space.add_solution(self)
    
    @abstractmethod
    def integrate_with(self, other: 'Solution', integration_type: IntegrationType) -> 'Solution':
        pass
    
    def apply_to(self, target: 'Solution') -> 'Solution':
        return self.integrate_with(target, IntegrationType.MODIFICATION)
    
    def __add__(self, other: 'Solution') -> 'Solution':
        return self.integrate_with(other, IntegrationType.UNION)
    
    def get_full_reference(self) -> str:
        """Получить полную ссылку на Solution: #3"""
        return f"#{self.solution_number}"
    
    def debug_variables(self):
        """Отладочная информация о переменных"""
        print(f"\nSolution #{self.solution_number}: {self.name}")
        print("=" * 50)
        
        for var in self.variables.get_all_variables():
            print(f"{var.full_id} | {var.named_id} | {var.name} = {var.value}")
            if var.aliases:
                for alias in var.aliases:
                    print(f"    └─ #{self.solution_number}.{alias} = {var.value}")
        
        print("\nВсе способы обращения:")
        info = self.variables.get_variable_info()
        for name, full_id in info["name_mappings"].items():
            print(f"  {name} → {full_id}")

class PrimitiveSolution(Solution):
    def __init__(self, name: str):
        super().__init__(name)
    
    def integrate_with(self, other: Solution, integration_type: IntegrationType) -> Solution:
        result = CompositeSolution(f"{self.name} + {other.name}")
        result.parent_solutions = [self, other]
        return result

class ModificationSolution(Solution):
    def __init__(self, name: str):
        super().__init__(name)
    
    def integrate_with(self, other: Solution, integration_type: IntegrationType) -> Solution:
        result = CompositeSolution(f"{other.name} + {self.name}")
        result.parent_solutions = [other, self]
        return result

class CompositeSolution(Solution):
    def __init__(self, name: str):
        super().__init__(name)
    
    def integrate_with(self, other: Solution, integration_type: IntegrationType) -> Solution:
        result = CompositeSolution(f"{self.name} + {other.name}")
        result.parent_solutions = [self, other]
        return result

# =============================================================================
# Конкретные решения с иерархической адресацией
# =============================================================================

class BoxSolution(PrimitiveSolution):
    def __init__(self, name: str, length: float, width: float, height: float):
        super().__init__(name)
        self._setup_variables(length, width, height)
    
    def _setup_variables(self, length: float, width: float, height: float):
        # Создаем переменные с иерархической адресацией
        self.variables.create_variable("length", length, VariableType.CONTROLLABLE, ["L", "len"])
        self.variables.create_variable("width", width, VariableType.CONTROLLABLE, ["W", "wid"])  
        self.variables.create_variable("height", height, VariableType.CONTROLLABLE, ["H", "hei"])
        
        # Вычисляемая переменная - объем
        volume = length * width * height
        self.variables.create_variable("volume", volume, VariableType.DERIVED, ["vol"])
    
    @property
    def length(self) -> float:
        # Теперь обращаемся к переменной #solution_number.1
        return self.variables.get_variable_by_reference("length").value
    
    @property  
    def width(self) -> float:
        return self.variables.get_variable_by_reference("width").value
    
    @property
    def height(self) -> float:
        return self.variables.get_variable_by_reference("height").value
    
    def update_dimensions(self, length: float = None, width: float = None, height: float = None):
        """Обновление размеров с пересчетом объема"""
        if length is not None:
            self.variables.get_variable_by_reference("length").value = length
        if width is not None:
            self.variables.get_variable_by_reference("width").value = width
        if height is not None:
            self.variables.get_variable_by_reference("height").value = height
        
        # Пересчитываем объем
        new_volume = self.length * self.width * self.height
        self.variables.get_variable_by_reference("volume").value = new_volume

class EdgeBandingSolution(ModificationSolution):
    def __init__(self, name: str, material: str, thickness: float, edges: List[str]):
        super().__init__(name)
        self._setup_variables(material, thickness, edges)
    
    def _setup_variables(self, material: str, thickness: float, edges: List[str]):
        self.variables.create_variable("material", material, VariableType.CONTROLLABLE, ["mat"])
        self.variables.create_variable("thickness", thickness, VariableType.CONTROLLABLE, ["thick"])
        self.variables.create_variable("edges", edges, VariableType.CONTROLLABLE, ["edge_list"])

# =============================================================================
# Обновленный файловый формат
# =============================================================================

class VsolFormat:
    @staticmethod
    def save_solution(solution: Solution, filepath: str):
        data = VsolFormat._serialize_solution(solution)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_solution(filepath: str) -> Solution:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return VsolFormat._deserialize_solution(data)
    
    @staticmethod
    def _serialize_solution(solution: Solution) -> dict:
        variables = {}
        
        for var in solution.variables.get_all_variables():
            variables[var.full_id] = {
                "name": var.name,
                "named_id": var.named_id,
                "value": var.value,
                "type": var.variable_type.value,
                "aliases": var.aliases
            }
        
        return {
            "solution_id": solution.solution_id,
            "solution_number": solution.solution_number,
            "name": solution.name,
            "type": type(solution).__name__,
            "variables": variables,
            "coordinate_system": {
                "origin": solution.coordinate_system.origin,
                "rotation": solution.coordinate_system.rotation
            },
            "parent_solutions": [VsolFormat._serialize_solution(parent) for parent in solution.parent_solutions]
        }
    
    @staticmethod
    def _deserialize_solution(data: dict) -> Solution:
        solution_type = data["type"]
        
        # Восстанавливаем номер Solution
        solution_number_manager._next_number = max(solution_number_manager._next_number, data["solution_number"] + 1)
        
        if solution_type == "BoxSolution":
            # Извлекаем параметры из variables по именованным ID
            vars_data = data["variables"]
            length = None
            width = None
            height = None
            
            for var_id, var_info in vars_data.items():
                if var_info["name"] == "length":
                    length = var_info["value"]
                elif var_info["name"] == "width":
                    width = var_info["value"]
                elif var_info["name"] == "height":
                    height = var_info["value"]
            
            solution = BoxSolution(data["name"], length, width, height)
            
        elif solution_type == "EdgeBandingSolution":
            vars_data = data["variables"]
            material = None
            thickness = None
            edges = None
            
            for var_id, var_info in vars_data.items():
                if var_info["name"] == "material":
                    material = var_info["value"]
                elif var_info["name"] == "thickness":
                    thickness = var_info["value"]
                elif var_info["name"] == "edges":
                    edges = var_info["value"]
            
            solution = EdgeBandingSolution(data["name"], material, thickness, edges)
        else:
            solution = CompositeSolution(data["name"])
        
        # Восстанавливаем номер Solution
        solution.solution_number = data["solution_number"]
        solution_number_manager.register_solution(solution.solution_number, solution)
        
        # Восстанавливаем родительские решения
        for parent_data in data["parent_solutions"]:
            parent = VsolFormat._deserialize_solution(parent_data)
            solution.parent_solutions.append(parent)
        
        return solution

# =============================================================================
# Демонстрационные функции
# =============================================================================

def demo_hierarchical_variables():
    """Демонстрация иерархической системы переменных"""
    print("ДЕМОНСТРАЦИЯ ИЕРАРХИЧЕСКОЙ АДРЕСАЦИИ")
    print("=" * 50)
    
    # Создаем несколько решений
    panel1 = BoxSolution("Боковая панель", 600, 400, 18)
    panel2 = BoxSolution("Верхняя панель", 800, 300, 18)
    edge_banding = EdgeBandingSolution("Кромка ПВХ", "белая", 2.0, ["верх", "низ"])
    
    print(f"Создано 3 решения:")
    print(f"  Solution {panel1.get_full_reference()}: {panel1.name}")
    print(f"  Solution {panel2.get_full_reference()}: {panel2.name}")
    print(f"  Solution {edge_banding.get_full_reference()}: {edge_banding.name}")
    
    # Показываем детальную информацию о переменных
    panel1.debug_variables()
    
    print(f"\nПРИМЕРЫ ОБРАЩЕНИЯ К ПЕРЕМЕННЫМ:")
    print("-" * 30)
    
    # Различные способы обращения к length панели #1
    length_var = panel1.variables.get_variable_by_reference("length")
    print(f"Локально 'length': {length_var.value}")
    
    length_var = panel1.variables.get_variable_by_reference("L")
    print(f"Локально 'L': {length_var.value}")
    
    length_var = panel1.variables.get_variable_by_reference("#1.length")
    print(f"Полный '#1.length': {length_var.value}")
    
    length_var = panel1.variables.get_variable_by_reference("#1.1")
    print(f"Числовой '#1.1': {length_var.value}")
    
    length_var = panel1.variables.get_variable_by_reference("#1.L")
    print(f"Алиас '#1.L': {length_var.value}")
    
    # Показываем разницу между решениями
    print(f"\nСРАВНЕНИЕ РЕШЕНИЙ:")
    print("-" * 20)
    print(f"#{panel1.solution_number}.length = {panel1.length}")
    print(f"#{panel2.solution_number}.length = {panel2.length}")
    
    # Глобальный доступ
    print(f"\nГЛОБАЛЬНЫЙ ДОСТУП:")
    print("-" * 20)
    solution_by_number = solution_number_manager.get_solution_by_number(1)
    if solution_by_number:
        print(f"Solution #{1}: {solution_by_number.name}")
    
    return panel1, panel2, edge_banding

def demo_variable_update():
    """Демонстрация обновления переменных"""
    print("\nДЕМОНСТРАЦИЯ ОБНОВЛЕНИЯ ПЕРЕМЕННЫХ")
    print("=" * 35)
    
    panel = BoxSolution("Тестовая панель", 600, 400, 18)
    
    print(f"Исходные размеры: {panel.length} x {panel.width} x {panel.height}")
    print(f"Исходный объем: {panel.variables.get_variable_by_reference('volume').value}")
    
    # Обновляем размеры
    panel.update_dimensions(length=800, width=500)
    
    print(f"Новые размеры: {panel.length} x {panel.width} x {panel.height}")
    print(f"Новый объем: {panel.variables.get_variable_by_reference('volume').value}")
    
    # Показываем все обновленные переменные
    print(f"\nВСЕ ПЕРЕМЕННЫЕ ПОСЛЕ ОБНОВЛЕНИЯ:")
    for var in panel.variables.get_all_variables():
        print(f"  {var}")

def demo_file_format():
    """Демонстрация файлового формата с иерархической адресацией"""
    print("\nДЕМОНСТРАЦИЯ ФАЙЛОВОГО ФОРМАТА")
    print("=" * 30)
    
    # Создаем и сохраняем решение
    panel = BoxSolution("Тестовая панель", 600, 400, 18)
    edge = EdgeBandingSolution("Кромка", "белая", 2.0, ["верх"])
    composite = edge.apply_to(panel)
    
    # Сохраняем
    VsolFormat.save_solution(composite, "hierarchical_test.vsol")
    print("✅ Решение сохранено в hierarchical_test.vsol")
    
    # Загружаем
    loaded = VsolFormat.load_solution("hierarchical_test.vsol")
    print(f"✅ Решение загружено: {loaded.name}")
    print(f"   Solution #{loaded.solution_number}")
    print(f"   Родительских решений: {len(loaded.parent_solutions)}")

if __name__ == "__main__":
    print("Visual Solving MVP - Иерархическая адресация")
    print("=" * 55)
    
    # Сброс для чистой демонстрации
    solution_number_manager.reset()
    
    # Демонстрации
    demo_hierarchical_variables()
    demo_variable_update()
    demo_file_format()
    
    print("\n🎯 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:")
    print("=" * 25)
    print("✅ Каждый Solution имеет уникальный номер: #1, #2, #3...")
    print("✅ Переменные адресуются иерархически: #1.1, #1.2, #1.3...")
    print("✅ Именованные ссылки: #1.length, #1.width, #1.height")
    print("✅ Алиасы работают: #1.L, #1.W, #1.H")
    print("✅ Локальный доступ: 'length', 'L' (в рамках Solution)")
    print("✅ Глобальная уникальность и отсутствие конфликтов")
