from collections import deque
from typing import Dict, List
import os


class GraphBuilderError(Exception):
    pass


class CircularDependencyError(GraphBuilderError):
    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


class DependencyGraphBuilder:
    def __init__(self, filter_substring: str = "", max_depth: int = 10):
        self.filter_substring = filter_substring
        self.max_depth = max_depth

    def should_skip_package(self, package_name: str) -> bool:
        if self.filter_substring and self.filter_substring in package_name:
            return True
        if package_name.startswith('so:') or package_name.startswith('/'):
            return True
        if '.so.' in package_name:
            return True
        return False

    def bfs_build_graph(self, start_package: str, get_dependencies_func) -> Dict[str, List[str]]:
        if self.should_skip_package(start_package):
            raise GraphBuilderError(f"Start package '{start_package}' filtered by substring '{self.filter_substring}'")

        queue = deque([(start_package, 0)])
        visited = set()
        graph = {}
        parent_map = {}

        while queue:
            current_package, depth = queue.popleft()

            if current_package in visited:
                continue

            if depth > self.max_depth:
                print(f"Max depth {self.max_depth} reached for package {current_package}")
                continue

            visited.add(current_package)
            print(f"Analyzing package: {current_package} (depth: {depth})")

            try:
                dependencies = get_dependencies_func(current_package)

                filtered_dependencies = []
                for dep in dependencies:
                    if self.should_skip_package(dep):
                        print(f"   Skipping dependency {dep} (filter: '{self.filter_substring}')")
                        continue
                    filtered_dependencies.append(dep)

                graph[current_package] = filtered_dependencies

                for dep in filtered_dependencies:
                    if dep not in visited:
                        if dep in parent_map:
                            cycle = self._find_cycle(parent_map, current_package, dep)
                            raise CircularDependencyError(cycle)

                        parent_map[dep] = current_package
                        queue.append((dep, depth + 1))

            except Exception as e:
                print(f"   Error analyzing {current_package}: {e}")
                graph[current_package] = []

        return graph

    def _find_cycle(self, parent_map: Dict[str, str], start: str, end: str) -> List[str]:
        cycle = [end]
        current = start

        while current != end:
            cycle.append(current)
            current = parent_map.get(current)
            if current is None:
                break

        cycle.append(end)
        cycle.reverse()
        return cycle

    def print_graph_statistics(self, graph: Dict[str, List[str]]) -> None:
        total_packages = len(graph)
        total_dependencies = sum(len(deps) for deps in graph.values())
        packages_without_deps = sum(1 for deps in graph.values() if not deps)

        print(f"GRAPH STATISTICS:")
        print(f"   Total packages: {total_packages}")
        print(f"   Total dependencies: {total_dependencies}")
        print(f"   Packages without dependencies: {packages_without_deps}")
        print(f"   Max depth: {self.max_depth}")
        if self.filter_substring:
            print(f"   Filter: '{self.filter_substring}'")

    def print_graph_structure(self, graph: Dict[str, List[str]], start_package: str) -> None:
        print(f"DEPENDENCY GRAPH STRUCTURE:")

        def print_tree(package: str, depth: int = 0, prefix: str = "", is_last: bool = True):
            connector = "└── " if is_last else "├── "
            print(prefix + connector + package)

            if package in graph:
                children = graph[package]
                new_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    print_tree(child, depth + 1, new_prefix, is_last_child)

        print_tree(start_package)


class TestRepositoryParser:

    @staticmethod
    def parse_test_repository(file_path: str) -> Dict[str, List[str]]:
        if not os.path.exists(file_path):
            raise GraphBuilderError(f"Test repository file '{file_path}' not found")

        repository = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if ':' not in line:
                    raise GraphBuilderError(f"Invalid format line {line_num}: {line}")

                package, deps_str = line.split(':', 1)
                package = package.strip()

                if not package:
                    raise GraphBuilderError(f"Empty package name in line {line_num}")

                dependencies = []
                if deps_str.strip():
                    dependencies = [dep.strip() for dep in deps_str.split() if dep.strip()]

                repository[package] = dependencies

        if not repository:
            raise GraphBuilderError("Test repository is empty")

        print(f"Test repository loaded: {len(repository)} packages")
        return repository


def main():
    test_repo = TestRepositoryParser.parse_test_repository("test_repository.txt")

    def get_test_dependencies(package):
        return test_repo.get(package, [])

    builder = DependencyGraphBuilder(filter_substring="", max_depth=5)

    try:
        print("TESTING BFS GRAPH BUILDING")
        print("=" * 50)

        graph = builder.bfs_build_graph("A", get_test_dependencies)
        builder.print_graph_statistics(graph)
        builder.print_graph_structure(graph, "A")

    except CircularDependencyError as e:
        print(f"Circular dependency: {e}")
    except GraphBuilderError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()