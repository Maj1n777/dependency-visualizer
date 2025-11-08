#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys
import os


class DependencyVisualizer:
    def __init__(self):
        self.config = {}

    def load_config(self, config_path='config.xml'):
        """Загрузка конфигурации из XML файла"""
        try:
            if not os.path.exists(config_path):
                raise Exception(f"Файл '{config_path}' не найден!")

            tree = ET.parse(config_path)
            root = tree.getroot()

            # Извлекаем параметры
            self.config['package_name'] = root.find('package_name').text
            self.config['repository_url'] = root.find('repository_url').text
            self.config['test_repository_mode'] = root.find('test_repository_mode').text.lower() == 'true'
            self.config['output_filename'] = root.find('output_filename').text
            self.config['ascii_tree_mode'] = root.find('ascii_tree_mode').text.lower() == 'true'
            self.config['filter_substring'] = root.find('filter_substring').text

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)

    def print_config(self):
        """Вывод параметров конфигурации"""
        print("=== Параметры конфигурации ===")
        for key, value in self.config.items():
            print(f"{key}: {value}")
        print("==============================")

    def run(self):
        """Основной метод запуска"""
        config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.xml'
        self.load_config(config_path)
        self.print_config()
        print("✅ Конфигурация загружена успешно!")


if __name__ == "__main__":
    visualizer = DependencyVisualizer()
    visualizer.run()