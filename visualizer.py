#!/usr/bin/env python3
"""
Визуализатор графа зависимостей пакетов - Этап 2
Основное приложение с выводом прямых зависимостей
"""

import xml.etree.ElementTree as ET
import sys
import os
from typing import Dict, Any
import urllib.request
import urllib.error
import gzip
import re


class ConfigError(Exception):
    """Исключение для ошибок конфигурации"""
    pass


class APKParserError(Exception):
    """Исключение для ошибок парсинга APK"""
    pass


class AlpineDependencyParser:
    def __init__(self, repository_url: str, architecture: str = "x86_64"):
        self.repository_url = repository_url.rstrip('/')
        self.architecture = architecture

    def get_package_dependencies(self, package_name: str) -> list:
        """
        Получение прямых зависимостей для указанного пакета из Alpine репозитория
        """
        try:
            print(f"Поиск пакета '{package_name}' в репозитории...")

            # Загрузка индекса пакетов
            index_url = f"{self.repository_url}/{self.architecture}/APKINDEX.tar.gz"

            with urllib.request.urlopen(index_url) as response:
                if response.status != 200:
                    raise APKParserError(f"Ошибка загрузки индекса: HTTP {response.status}")

                # Распаковка и чтение gzip архива
                with gzip.open(response, 'rt', encoding='utf-8', errors='ignore') as f:
                    index_content = f.read()

            # Парсинг индекса и поиск пакета
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
                            # Удаляем условия версий и логические операторы
                            clean_dep = re.sub(r'[<=>!|~].*$', '', dep)
                            if clean_dep:
                                clean_deps.append(clean_dep)
                        current_package['dependencies'] = clean_deps
                    else:
                        current_package['dependencies'] = []

            # Добавляем последний пакет
            if current_package and 'name' in current_package:
                packages[current_package['name']] = current_package

            # Поиск запрошенного пакета
            if package_name not in packages:
                available_packages = [pkg for pkg in packages.keys() if package_name.lower() in pkg.lower()]
                if available_packages:
                    raise APKParserError(
                        f"Пакет '{package_name}' не найден. Возможно вы имели в виду: {', '.join(available_packages[:5])}"
                    )
                else:
                    raise APKParserError(f"Пакет '{package_name}' не найден в репозитории")

            package_info = packages[package_name]
            dependencies = package_info.get('dependencies', [])

            print(f"Пакет '{package_name}' найден (версия: {package_info.get('version', 'неизвестна')})")
            return dependencies

        except urllib.error.URLError as e:
            raise APKParserError(f"Ошибка сети: {e}")
        except Exception as e:
            raise APKParserError(f"Ошибка получения зависимостей: {e}")


class DependencyVisualizer:
    def __init__(self):
        self.config: Dict[str, Any] = {}

    def load_config(self, config_path: str = 'config.xml') -> None:
        """
        Загрузка конфигурации из XML файла
        """
        try:
            if not os.path.exists(config_path):
                raise ConfigError(f"Конфигурационный файл '{config_path}' не найден")

            tree = ET.parse(config_path)
            root = tree.getroot()

            # Парсинг всех параметров конфигурации
            config_params = {}

            # Обязательные параметры
            required_params = ['package_name', 'repository_url', 'test_repository_mode',
                               'output_filename', 'ascii_tree_mode']

            for param in required_params:
                element = root.find(param)
                if element is None or not element.text:
                    raise ConfigError(f"Параметр '{param}' обязателен в конфигурации")

                value = element.text.strip()

                # Обработка булевых значений
                if param in ['test_repository_mode', 'ascii_tree_mode']:
                    if value.lower() not in ['true', 'false']:
                        raise ConfigError(f"Параметр '{param}' должен быть 'true' или 'false'")
                    config_params[param] = value.lower() == 'true'
                else:
                    config_params[param] = value

            # Необязательные параметры
            optional_params = {
                'filter_substring': '',
                'architecture': 'x86_64'
            }

            for param, default_value in optional_params.items():
                element = root.find(param)
                if element is not None and element.text is not None:
                    config_params[param] = element.text.strip()
                else:
                    config_params[param] = default_value

            self.config = config_params

        except ET.ParseError as e:
            raise ConfigError(f"Ошибка парсинга XML: {e}")
        except Exception as e:
            raise ConfigError(f"Ошибка загрузки конфигурации: {e}")

    def print_config(self) -> None:
        """
        Вывод всех параметров конфигурации в формате ключ-значение
        """
        print("=== Параметры конфигурации ===")
        for key, value in self.config.items():
            print(f"{key}: {value}")
        print("==============================")

    def get_real_dependencies(self) -> list:
        """
        Получение реальных зависимостей из Alpine репозитория
        """
        try:
            parser = AlpineDependencyParser(
                repository_url=self.config['repository_url'],
                architecture=self.config['architecture']
            )

            dependencies = parser.get_package_dependencies(self.config['package_name'])

            # Применение фильтра если указан
            if self.config['filter_substring']:
                filtered_deps = [dep for dep in dependencies if self.config['filter_substring'] in dep]
                print(f"Применен фильтр: '{self.config['filter_substring']}'")
                print(f"Зависимостей до фильтрации: {len(dependencies)}, после: {len(filtered_deps)}")
                return filtered_deps

            return dependencies

        except APKParserError as e:
            raise ConfigError(f"Ошибка получения зависимостей: {e}")

    def print_dependencies(self, dependencies: list) -> None:
        """
        Вывод прямых зависимостей на экран (требование этапа 2)
        """
        print(f"\n ПРЯМЫЕ ЗАВИСИМОСТИ ПАКЕТА '{self.config['package_name']}':")
        print("=" * 60)

        if dependencies:
            for i, dep in enumerate(dependencies, 1):
                print(f"{i:2d}. {dep}")
        else:
            print("Пакет не имеет прямых зависимостей")

        print(f"\n Итого: {len(dependencies)} зависимостей")
        print("=" * 60)

    def run(self) -> None:
        """
        Основной метод запуска приложения
        """
        try:
            # Загрузка конфигурации
            config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.xml'
            print("Запуск Dependency Visualizer - Этап 2")
            print("=========================================")

            self.load_config(config_path)

            # Вывод параметров конфигурации
            self.print_config()

            # Получение реальных зависимостей
            print(f"\n Получение зависимостей для пакета '{self.config['package_name']}'...")
            dependencies = self.get_real_dependencies()

            # Вывод прямых зависимостей (требование этапа 2)
            self.print_dependencies(dependencies)

            print(f"\n Этап 2 завершен успешно!")
            print(f"Проанализирован пакет: {self.config['package_name']}")
            print(f"Репозиторий: {self.config['repository_url']}")
            print(f"Архитектура: {self.config['architecture']}")

        except ConfigError as e:
            print(f"Ошибка конфигурации: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n Программа прервана пользователем")
            sys.exit(1)
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            sys.exit(1)


def main():
    """
    Точка входа в приложение
    """
    if len(sys.argv) > 2:
        print("Использование: python visualizer.py [config.xml]")
        print("  config.xml - путь к конфигурационному файлу (по умолчанию: config.xml)")
        sys.exit(1)

    visualizer = DependencyVisualizer()
    visualizer.run()


if __name__ == "__main__":
    main()