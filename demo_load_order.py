from dependency_analyzer import DependencyAnalyzer
from graph_builder import DependencyGraphBuilder, TestRepositoryParser


def demonstrate_load_order_cases():

    test_repo = TestRepositoryParser.parse_test_repository("test_repository.txt")

    def get_dependencies(package):
        return test_repo.get(package, [])

    test_cases = [
        {
            "name": "Простые линейные зависимости",
            "start_package": "A",
            "description": "A -> B -> C -> D"
        },
        {
            "name": "Сложные зависимости с циклами",
            "start_package": "I",
            "description": "I -> A -> B -> ... -> I (цикл)"
        },
        {
            "name": "Множественные зависимости на одном уровне",
            "start_package": "B",
            "description": "B -> D и B -> E"
        }
    ]

    analyzer = DependencyAnalyzer()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"ТЕСТОВЫЙ СЛУЧАЙ {i}: {test_case['name']}")
        print(f"Описание: {test_case['description']}")
        print(f"Стартовый пакет: {test_case['start_package']}")
        print('=' * 70)

        builder = DependencyGraphBuilder(filter_substring="", max_depth=10)

        try:
            graph = builder.bfs_build_graph(test_case['start_package'], get_dependencies)

            if graph:
                print(f"Размер графа: {len(graph)} пакетов")

                bfs_order, dfs_order, topological_order = analyzer.compare_load_orders(
                    graph, test_case['start_package']
                )

                analyzer.print_detailed_dependency_analysis(graph, test_case['start_package'])

                print(f"\nРЕКОМЕНДУЕМЫЙ ПОРЯДОК ЗАГРУЗКИ:")
                for j, package in enumerate(bfs_order, 1):
                    print(f"  {j:2d}. {package}")

        except Exception as e:
            print(f"Ошибка в тестовом случае: {e}")


def compare_with_real_package_manager():

    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ С РЕАЛЬНЫМ МЕНЕДЖЕРОМ ПАКЕТОВ")
    print("=" * 70)

    print("ПОВЕДЕНИЕ РЕАЛЬНОГО МЕНЕДЖЕРА ПАКЕТОВ APK:")
    print("1. Использует SAT-решатель для разрешения зависимостей")
    print("2. Учитывает ограничения версий и конфликты")
    print("3. Обрабатывает приоритеты репозиториев")
    print("4. Оптимизирует для минимальных загрузок")
    print("5. Может переупорядочивать пакеты для эффективности")

    print("\nСОЗДАННЫЙ АЛГОРИТМ VS РЕАЛЬНЫЙ APK:")
    print("РАЗЛИЧИЯ:")
    print("✓ В созданном алгоритме используются простые BFS/DFS - APK использует сложный SAT-решатель")
    print("✓ В созданном алгоритме игнорируются версии - APK обрабатывает ограничения версий")
    print("✓ В созданном алгоритме не разрешаются конфликты - APK имеет разрешение конфликтов")
    print("✓ В созданном алгоритме обрабатываются все зависимости - APK может пропускать опциональные зависимости")

    print("\nСХОДСТВА:")
    print("✓ Оба обрабатывают зависимости перед зависимыми пакетами")
    print("✓ Оба обрабатывают базовые цепочки зависимостей")
    print("✓ Оба обнаруживают циклические зависимости")


if __name__ == "__main__":
    print("ДЕМОНСТРАЦИЯ ЭТАПА 4: АНАЛИЗ ПОРЯДКА ЗАГРУЗКИ")
    demonstrate_load_order_cases()
    compare_with_real_package_manager()