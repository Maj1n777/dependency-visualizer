from graph_builder import DependencyGraphBuilder, TestRepositoryParser, CircularDependencyError


def demonstrate_test_cases():
    test_repo = TestRepositoryParser.parse_test_repository("test_repository.txt")

    def get_dependencies(package):
        return test_repo.get(package, [])

    test_cases = [
        {
            "name": "Normal graph building",
            "start_package": "A",
            "filter_substring": "",
            "max_depth": 10
        },
        {
            "name": "With package filtering for 'H'",
            "start_package": "A",
            "filter_substring": "H",
            "max_depth": 10
        },
        {
            "name": "Limited depth",
            "start_package": "A",
            "filter_substring": "",
            "max_depth": 2
        },
        {
            "name": "Circular dependency detection",
            "start_package": "I",
            "filter_substring": "",
            "max_depth": 10
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"TEST {i}: {test_case['name']}")
        print(f"Start package: {test_case['start_package']}")
        print(f"Filter: '{test_case['filter_substring']}'")
        print(f"Max depth: {test_case['max_depth']}")
        print('=' * 50)

        builder = DependencyGraphBuilder(
            filter_substring=test_case['filter_substring'],
            max_depth=test_case['max_depth']
        )

        try:
            graph = builder.bfs_build_graph(test_case['start_package'], get_dependencies)
            builder.print_graph_statistics(graph)
            builder.print_graph_structure(graph, test_case['start_package'])

        except CircularDependencyError as e:
            print(f"Circular dependency: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("STAGE 3 DEMONSTRATION: GRAPH OPERATIONS")
    demonstrate_test_cases()