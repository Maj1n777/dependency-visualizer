import xml.etree.ElementTree as ET
import sys
import os
from typing import Dict, Any, Callable, List
import urllib.request
import urllib.error
import gzip
import re
from graph_builder import (
    DependencyGraphBuilder,
    TestRepositoryParser,
    CircularDependencyError,
    GraphBuilderError
)


class ConfigError(Exception):
    pass


class APKParserError(Exception):
    pass


class AlpineDependencyParser:
    def __init__(self, repository_url: str, architecture: str = "x86_64"):
        self.repository_url = repository_url.rstrip('/')
        self.architecture = architecture
        self.packages_cache = None

    def _load_packages_index(self) -> Dict[str, Dict]:
        if self.packages_cache is not None:
            return self.packages_cache

        try:
            index_url = f"{self.repository_url}/{self.architecture}/APKINDEX.tar.gz"

            with urllib.request.urlopen(index_url) as response:
                if response.status != 200:
                    raise APKParserError(f"Index download error: HTTP {response.status}")

                with gzip.open(response, 'rt', encoding='utf-8', errors='ignore') as f:
                    index_content = f.read()

            packages = {}
            current_package = {}

            for line in index_content.split('\n'):
                if line.startswith('P:'):
                    if current_package and 'name' in current_package:
                        packages[current_package['name']] = current_package.copy()
                    current_package = {'name': line[2:].strip()}

                elif line.startswith('V:'):
                    current_package['version'] = line[2:].strip()

                elif line.startswith('D:'):
                    dependencies = line[2:].strip()
                    if dependencies:
                        clean_deps = []
                        for dep in dependencies.split():
                            clean_dep = re.sub(r'[<=>!|~].*$', '', dep)
                            if clean_dep:
                                clean_deps.append(clean_dep)
                        current_package['dependencies'] = clean_deps
                    else:
                        current_package['dependencies'] = []

            if current_package and 'name' in current_package:
                packages[current_package['name']] = current_package

            self.packages_cache = packages
            return packages

        except urllib.error.URLError as e:
            raise APKParserError(f"Network error: {e}")
        except Exception as e:
            raise APKParserError(f"Index loading error: {e}")

    def get_package_dependencies(self, package_name: str) -> list:
        packages = self._load_packages_index()

        if package_name not in packages:
            available_packages = [pkg for pkg in packages.keys() if package_name.lower() in pkg.lower()]
            if available_packages:
                raise APKParserError(
                    f"Package '{package_name}' not found. Similar packages: {', '.join(available_packages[:5])}"
                )
            else:
                raise APKParserError(f"Package '{package_name}' not found in repository")

        package_info = packages[package_name]
        return package_info.get('dependencies', [])


class DependencyVisualizer:
    def __init__(self):
        self.config: Dict[str, Any] = {}

    def load_config(self, config_path: str = 'config.xml') -> None:
        try:
            if not os.path.exists(config_path):
                raise ConfigError(f"Config file '{config_path}' not found")

            tree = ET.parse(config_path)
            root = tree.getroot()

            config_params = {}

            required_params = ['package_name', 'repository_url', 'test_repository_mode',
                               'output_filename', 'ascii_tree_mode']

            for param in required_params:
                element = root.find(param)
                if element is None or not element.text:
                    raise ConfigError(f"Parameter '{param}' is required")

                value = element.text.strip()

                if param in ['test_repository_mode', 'ascii_tree_mode']:
                    if value.lower() not in ['true', 'false']:
                        raise ConfigError(f"Parameter '{param}' must be 'true' or 'false'")
                    config_params[param] = value.lower() == 'true'
                else:
                    config_params[param] = value

            optional_params = {
                'filter_substring': '',
                'architecture': 'x86_64',
                'test_repository_path': 'test_repository.txt',
                'max_depth': '10'
            }

            for param, default_value in optional_params.items():
                element = root.find(param)
                if element is not None and element.text is not None:
                    config_params[param] = element.text.strip()
                else:
                    config_params[param] = default_value

            try:
                config_params['max_depth'] = int(config_params['max_depth'])
            except ValueError:
                raise ConfigError("Parameter 'max_depth' must be a number")

            self.config = config_params

        except ET.ParseError as e:
            raise ConfigError(f"XML parsing error: {e}")
        except Exception as e:
            raise ConfigError(f"Config loading error: {e}")

    def print_config(self) -> None:
        print("=== Configuration Parameters ===")
        for key, value in self.config.items():
            print(f"{key}: {value}")
        print("================================")

    def get_dependencies_function(self) -> Callable[[str], list]:
        if self.config['test_repository_mode']:
            test_repo = TestRepositoryParser.parse_test_repository(
                self.config['test_repository_path']
            )

            def get_test_dependencies(package: str) -> list:
                return test_repo.get(package, [])

            return get_test_dependencies
        else:
            parser = AlpineDependencyParser(
                repository_url=self.config['repository_url'],
                architecture=self.config['architecture']
            )

            def get_real_dependencies(package: str) -> list:
                return parser.get_package_dependencies(package)

            return get_real_dependencies

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        try:
            get_dependencies_func = self.get_dependencies_function()

            builder = DependencyGraphBuilder(
                filter_substring=self.config['filter_substring'],
                max_depth=self.config['max_depth']
            )

            print(f"BUILDING DEPENDENCY GRAPH...")
            print(f"   Start package: {self.config['package_name']}")
            print(f"   Mode: {'TEST' if self.config['test_repository_mode'] else 'REAL'}")

            graph = builder.bfs_build_graph(
                self.config['package_name'],
                get_dependencies_func
            )

            if graph:
                builder.print_graph_statistics(graph)

                if self.config['ascii_tree_mode']:
                    builder.print_graph_structure(graph, self.config['package_name'])
            else:
                print("Graph is empty")

            return graph

        except CircularDependencyError as e:
            print(f"CIRCULAR DEPENDENCY DETECTED!")
            print(f"   {e}")
            return {}
        except GraphBuilderError as e:
            raise ConfigError(f"Graph building error: {e}")

    def run(self) -> None:
        try:
            config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.xml'
            print("Dependency Visualizer - Stage 3")
            print("===============================")

            self.load_config(config_path)
            self.print_config()

            graph = self.build_dependency_graph()

            print(f"Stage 3 completed successfully!")
            print(f"Package analyzed: {self.config['package_name']}")
            print(f"Graph size: {len(graph)} packages")

        except ConfigError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("Program interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)


def main():
    if len(sys.argv) > 2:
        print("Usage: python visualizer.py [config.xml]")
        print("  config.xml - path to config file (default: config.xml)")
        sys.exit(1)

    visualizer = DependencyVisualizer()
    visualizer.run()


if __name__ == "__main__":
    main()