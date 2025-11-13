from typing import Dict, List, Set, Tuple
from collections import deque, defaultdict
from graph_builder import DependencyGraphBuilder, TestRepositoryParser


class DependencyAnalyzer:
    def __init__(self):
        self.visited = set()
        self.load_order = []

    def topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        in_degree = defaultdict(int)

        for node in graph:
            in_degree[node] = 0

        for node, dependencies in graph.items():
            for dep in dependencies:
                in_degree[dep] += 1

        queue = deque([node for node in graph if in_degree[node] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(graph):
            cyclic_nodes = set(graph.keys()) - set(result)
            print(f"Предупреждение: Обнаружены циклические зависимости в узлах: {cyclic_nodes}")

            for node in graph:
                if node not in result:
                    result.append(node)

        return result

    def bfs_load_order(self, graph: Dict[str, List[str]], start_package: str) -> List[str]:
        visited = set()
        queue = deque([start_package])
        load_order = []

        while queue:
            level_size = len(queue)
            level_packages = []

            for _ in range(level_size):
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    level_packages.append(current)

                    for dep in graph.get(current, []):
                        if dep not in visited:
                            queue.append(dep)

            level_packages.sort()
            load_order.extend(level_packages)

        return load_order

    def dfs_load_order(self, graph: Dict[str, List[str]], start_package: str) -> List[str]:
        visited = set()
        load_order = []

        def dfs(package):
            if package in visited:
                return
            visited.add(package)

            for dep in graph.get(package, []):
                dfs(dep)

            load_order.append(package)

        dfs(start_package)
        return load_order

    def compare_load_orders(self, graph: Dict[str, List[str]], start_package: str):
        print("СРАВНЕНИЕ АЛГОРИТМОВ ПОРЯДКА ЗАГРУЗКИ")
        print("=" * 50)

        topological_order = self.topological_sort(graph)
        print(f"Порядок топологической сортировки: {topological_order}")

        bfs_order = self.bfs_load_order(graph, start_package)
        print(f"Порядок BFS: {bfs_order}")

        dfs_order = self.dfs_load_order(graph, start_package)
        print(f"Порядок DFS: {dfs_order}")

        print("\nРЕЗУЛЬТАТЫ СРАВНЕНИЯ:")
        print(f"Все алгоритмы дают одинаковый результат: {bfs_order == dfs_order == topological_order}")

        if bfs_order != topological_order:
            print("Обнаружено различие между BFS и топологической сортировкой")
            print("Это нормально - BFS обрабатывает по уровням, топологическая сортировка по зависимостям")

        return bfs_order, dfs_order, topological_order

    def print_detailed_dependency_analysis(self, graph: Dict[str, List[str]], start_package: str):
        print("\nДЕТАЛЬНЫЙ АНАЛИЗ ЗАВИСИМОСТЕЙ")
        print("=" * 50)

        levels = self.calculate_dependency_levels(graph, start_package)
        for level, packages in sorted(levels.items()):
            print(f"Уровень {level}: {packages}")

        cycles = self.find_cycles(graph)
        if cycles:
            print(f"\nОбнаружены циклические зависимости: {cycles}")
        else:
            print("\nЦиклические зависимости не обнаружены")

    def calculate_dependency_levels(self, graph: Dict[str, List[str]], start_package: str) -> Dict[int, List[str]]:
        levels = defaultdict(list)
        visited = set()
        queue = deque([(start_package, 0)])

        while queue:
            package, level = queue.popleft()
            if package in visited:
                continue

            visited.add(package)
            levels[level].append(package)

            for dep in graph.get(package, []):
                if dep not in visited:
                    queue.append((dep, level + 1))

        return levels

    def find_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        visited = set()
        recursion_stack = set()
        cycles = []

        def dfs_cycle(node, path):
            if node in recursion_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in graph.get(node, []):
                dfs_cycle(neighbor, path + [node])

            recursion_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs_cycle(node, [])

        return cycles


def main():
    test_repo = TestRepositoryParser.parse_test_repository("test_repository.txt")

    def get_dependencies(package):
        return test_repo.get(package, [])

    builder = DependencyGraphBuilder(filter_substring="", max_depth=10)

    try:
        print("АНАЛИЗ ПОРЯДКА ЗАГРУЗКИ ЗАВИСИМОСТЕЙ")
        print("=" * 50)

        graph = builder.bfs_build_graph("A", get_dependencies)

        if graph:
            builder.print_graph_statistics(graph)

            analyzer = DependencyAnalyzer()
            bfs_order, dfs_order, topological_order = analyzer.compare_load_orders(graph, "A")

            analyzer.print_detailed_dependency_analysis(graph, "A")

            print(f"\nРЕКОМЕНДУЕМЫЙ ПОРЯДОК ЗАГРУЗКИ (BFS):")
            for i, package in enumerate(bfs_order, 1):
                print(f"{i:2d}. {package}")

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()