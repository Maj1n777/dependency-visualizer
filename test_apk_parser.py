#!/usr/bin/env python3
"""
Тестирование парсера APK зависимостей
Позволяет быстро проверить работу с разными пакетами
"""

import sys
from visualizer import AlpineDependencyParser, APKParserError


def test_single_package(package_name: str):
    """Тестирование одного пакета"""
    print(f"\n{'=' * 60}")
    print(f"ТЕСТИРУЕМ ПАКЕТ: {package_name}")
    print('=' * 60)

    try:
        parser = AlpineDependencyParser(
            repository_url="https://dl-cdn.alpinelinux.org/alpine/v3.18/main",
            architecture="x86_64"
        )

        dependencies = parser.get_package_dependencies(package_name)

        print(f" Прямые зависимости пакета '{package_name}':")
        if dependencies:
            for i, dep in enumerate(dependencies, 1):
                print(f"  {i:2d}. {dep}")
            print(f"\n Всего зависимостей: {len(dependencies)}")
        else:
            print("  Пакет не имеет зависимостей")

    except APKParserError as e:
        print(f"  Ошибка: {e}")


def main():
    """Основная функция тестирования"""
    if len(sys.argv) > 1:
        # Тестирование пакета из аргументов командной строки
        package_name = sys.argv[1]
        test_single_package(package_name)
    else:
        # Тестирование популярных пакетов
        popular_packages = [
            "nginx",
            "python3",
            "postgresql",
            "nodejs",
            "redis",
            "busybox",
            "musl",
            "apk-tools"
        ]

        print("ТЕСТИРОВАНИЕ APK ПАРСЕРА")
        print("Тестируем популярные пакеты Alpine Linux\n")

        for package in popular_packages:
            test_single_package(package)

        print(f"\n{'=' * 60}")
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print('=' * 60)


if __name__ == "__main__":
    main()