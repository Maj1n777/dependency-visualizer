import os
from typing import Dict, List, Set


class GraphVisualizer:
    def __init__(self):
        self.node_colors = {}
        self.edge_styles = {}

    def generate_plantuml_code(self, graph: Dict[str, List[str]], start_package: str) -> str:
        plantuml_code = ["@startuml", "skinparam monochrome true", "skinparam shadowing false"]

        plantuml_code.append("title Граф зависимостей пакета: " + start_package)
        plantuml_code.append("")

        all_nodes = set(graph.keys())
        for deps in graph.values():
            all_nodes.update(deps)

        for node in sorted(all_nodes):
            if node == start_package:
                plantuml_code.append(f'rectangle "{node}" #FFEBCD')
            elif node in graph and graph[node]:
                plantuml_code.append(f'rectangle "{node}" #E6E6FA')
            else:
                plantuml_code.append(f'rectangle "{node}" #F0F0F0')

        plantuml_code.append("")

        added_edges = set()
        for source, targets in graph.items():
            for target in targets:
                if target in graph or target in all_nodes:
                    edge = (source, target)
                    if edge not in added_edges:
                        plantuml_code.append(f'"{source}" --> "{target}"')
                        added_edges.add(edge)

        plantuml_code.append("@enduml")
        return "\n".join(plantuml_code)

    def save_plantuml_file(self, plantuml_code: str, filename: str) -> None:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(plantuml_code)
        print(f"Файл PlantUML сохранен: {filename}")

    def generate_ascii_tree(self, graph: Dict[str, List[str]], start_package: str) -> str:
        lines = []

        def build_tree(node, prefix="", is_last=True):
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + node)

            if node in graph:
                children = graph[node]
                new_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    build_tree(child, new_prefix, is_last_child)

        lines.append("ДЕРЕВО ЗАВИСИМОСТЕЙ:")
        lines.append("=" * 40)
        build_tree(start_package)
        return "\n".join(lines)

    def print_graph_comparison(self, our_graph: Dict[str, List[str]], real_tools_info: str):
        print("\nСРАВНЕНИЕ С ШТАТНЫМИ ИНСТРУМЕНТАМИ:")
        print("=" * 50)

        print("СОЗДАННАЯ ВИЗУАЛИЗАЦИЯ:")
        print(f"- Пакетов: {len(our_graph)}")
        print(f"- Зависимостей: {sum(len(deps) for deps in our_graph.values())}")

        print("\nШТАТНЫЕ ИНСТРУМЕНТЫ APK:")
        print("- apk info -R <пакет>: показывает прямые зависимости")
        print("- apk search -R <пакет>: показывает рекурсивные зависимости")
        print("- apk list --depends <пакет>: список зависимостей")

        print("\nРАСХОЖДЕНИЯ:")
        print("✓ Созданная визуализация показывает полный граф - apk показывает линейные списки")
        print("✓ Созданная визуализация визуализирует связи - apk показывает текстовый список")
        print("✓ Созданная визуализация фильтрует библиотеки - apk включает все зависимости")
        print("✓ Созданная визуализация строит древовидную структуру - apk показывает плоский список")

        print("\nПРИЧИНЫ РАСХОЖДЕНИЙ:")
        print("1. APK инструменты предназначены для системного администрирования")
        print("2. Созданная визуализация ориентирована на анализ архитектуры")
        print("3. Созданная визуализация использует графовое представление для лучшего понимания связей")
        print("4. APK показывает фактические зависимости, созданная визуализация - логическую структуру")


def demonstrate_visualization():
    visualizer = GraphVisualizer()
    from graph_builder import TestRepositoryParser

    test_repo = TestRepositoryParser.parse_test_repository("test_repository.txt")

    def get_dependencies(package):
        return test_repo.get(package, [])

    test_packages = ["A", "B", "I"]

    for package in test_packages:
        print(f"\n{'=' * 70}")
        print(f"ВИЗУАЛИЗАЦИЯ ДЛЯ ПАКЕТА: {package}")
        print('=' * 70)

        from graph_builder import DependencyGraphBuilder
        builder = DependencyGraphBuilder(filter_substring="", max_depth=6)

        try:
            graph = builder.bfs_build_graph(package, get_dependencies)

            if graph:
                print(f"Размер графа: {len(graph)} пакетов")

                plantuml_code = visualizer.generate_plantuml_code(graph, package)
                filename = f"dependencies_{package}.puml"
                visualizer.save_plantuml_file(plantuml_code, filename)

                ascii_tree = visualizer.generate_ascii_tree(graph, package)
                print("\n" + ascii_tree)

                visualizer.print_graph_comparison(graph, f"APK tools for {package}")

        except Exception as e:
            print(f"Ошибка визуализации: {e}")


def main():
    print("ДЕМОНСТРАЦИЯ ВИЗУАЛИЗАЦИИ ГРАФА")
    demonstrate_visualization()


if __name__ == "__main__":
    main()