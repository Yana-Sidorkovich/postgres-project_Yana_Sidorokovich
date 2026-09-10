from typing import List, Tuple, Any
from .db_connector import DatabaseConnector


class QueryExecutor:
    """Выполнение SQL-запросов для отчётов"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector

    def get_rooms_with_students_count(self) -> List[Tuple[Any, ...]]:
        """Запрос 1: Список комнат и количество студентов в каждой"""
        query = """
            SELECT 
                r.id,
                r.name,
                COUNT(s.id) as students_count
            FROM rooms r
            LEFT JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            ORDER BY r.id
        """
        return self.db.execute_query(query)

    def get_5_rooms_youngest_students(self) -> List[Tuple[Any, ...]]:
        """Запрос 2: 5 комнат с наименьшим средним возрастом студентов"""
        query = """
            SELECT 
                r.id,
                r.name,
                AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, s.birthday::DATE))) as avg_age
            FROM rooms r
            INNER JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            ORDER BY avg_age ASC
            LIMIT 5
        """
        return self.db.execute_query(query)

    def get_5_rooms_largest_age_difference(self) -> List[Tuple[Any, ...]]:
        """Запрос 3: 5 комнат с наибольшей разницей в возрасте студентов"""
        query = """
            SELECT 
                r.id,
                r.name,
                MAX(EXTRACT(YEAR FROM AGE(CURRENT_DATE, s.birthday::DATE))) - 
                MIN(EXTRACT(YEAR FROM AGE(CURRENT_DATE, s.birthday::DATE))) as age_difference
            FROM rooms r
            INNER JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            ORDER BY age_difference DESC
            LIMIT 5
        """
        return self.db.execute_query(query)

    def get_rooms_with_different_sex_students(self) -> List[Tuple[Any, ...]]:
        """Запрос 4: Список комнат, где живут студенты разного пола"""
        query = """
            SELECT 
                r.id,
                r.name,
                COUNT(DISTINCT s.sex) as sex_count,
                STRING_AGG(DISTINCT s.sex, ', ') as sexes
            FROM rooms r
            INNER JOIN students s ON r.id = s.room
            GROUP BY r.id, r.name
            HAVING COUNT(DISTINCT s.sex) > 1
            ORDER BY r.id
        """
        return self.db.execute_query(query)

    def add_indexes(self):
        """Запрос 5: Добавление индексов для оптимизации"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_students_room ON students(room)",
            "CREATE INDEX IF NOT EXISTS idx_students_birthday ON students(birthday)",
            "CREATE INDEX IF NOT EXISTS idx_students_sex ON students(sex)",
            "CREATE INDEX IF NOT EXISTS idx_students_room_sex ON students(room, sex)"
        ]

        print("\n📊 Добавляем индексы для оптимизации...")
        for idx_query in indexes:
            self.db.execute_query(idx_query)
            print("✓ Индекс создан")

    def run_all_queries(self, output_format: str = 'text', output_file: str = None):
        """Выполняет все запросы и выводит результаты в указанном формате"""
        from .formatter import ResultFormatter

        formatter = ResultFormatter()

        # Словарь для сбора всех результатов (для сохранения в файл)
        all_results = {}

        # ✅ Сначала создаём индексы
        print("\n" + "=" * 60)
        print("ДОБАВЛЕНИЕ ИНДЕКСОВ ДЛЯ ОПТИМИЗАЦИИ")
        print("=" * 60)
        self.add_indexes()

        # ==================== ЗАПРОС 1 ====================
        print("\n" + "=" * 60)
        print("ЗАПРОС 1: Комнаты и количество студентов")
        print("=" * 60)

        results = self.get_rooms_with_students_count()
        columns = ['id', 'name', 'students_count']
        all_results['rooms_with_students_count'] = {
            'columns': columns,
            'data': results
        }

        if output_format in ('json', 'xml'):
            formatted = formatter.format_query_results(
                "rooms_with_students_count", results, columns, output_format
            )
            print(formatted)
        else:
            print(f"{'ID':<5} {'Название':<20} {'Студентов':<10}")
            print("-" * 35)
            for row in results[:10]:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<10}")
            if len(results) > 10:
                print(f"... и ещё {len(results) - 10} комнат")

        # ==================== ЗАПРОС 2 ====================
        print("\n" + "=" * 60)
        print("ЗАПРОС 2: 5 комнат с наименьшим средним возрастом")
        print("=" * 60)

        results = self.get_5_rooms_youngest_students()
        columns = ['id', 'name', 'avg_age']
        all_results['5_rooms_youngest_students'] = {
            'columns': columns,
            'data': results
        }

        if output_format in ('json', 'xml'):
            formatted = formatter.format_query_results(
                "5_rooms_youngest_students", results, columns, output_format
            )
            print(formatted)
        else:
            print(f"{'ID':<5} {'Название':<20} {'Средний возраст':<15}")
            print("-" * 40)
            for row in results:
                print(f"{row[0]:<5} {row[1]:<20} {float(row[2]):.1f}")

        # ==================== ЗАПРОС 3 ====================
        print("\n" + "=" * 60)
        print("ЗАПРОС 3: 5 комнат с наибольшей разницей в возрасте")
        print("=" * 60)

        results = self.get_5_rooms_largest_age_difference()
        columns = ['id', 'name', 'age_difference']
        all_results['5_rooms_largest_age_difference'] = {
            'columns': columns,
            'data': results
        }

        if output_format in ('json', 'xml'):
            formatted = formatter.format_query_results(
                "5_rooms_largest_age_difference", results, columns, output_format
            )
            print(formatted)
        else:
            print(f"{'ID':<5} {'Название':<20} {'Разница в возрасте':<20}")
            print("-" * 45)
            for row in results:
                print(f"{row[0]:<5} {row[1]:<20} {float(row[2]):.1f}")

        # ==================== ЗАПРОС 4 ====================
        print("\n" + "=" * 60)
        print("ЗАПРОС 4: Комнаты с разными полами студентов")
        print("=" * 60)

        results = self.get_rooms_with_different_sex_students()
        columns = ['id', 'name', 'sex_count', 'sexes']
        all_results['rooms_with_different_sex_students'] = {
            'columns': columns,
            'data': results
        }

        if output_format in ('json', 'xml'):
            formatted = formatter.format_query_results(
                "rooms_with_different_sex_students", results, columns, output_format
            )
            print(formatted)
        else:
            print(f"{'ID':<5} {'Название':<20} {'Полы':<10}")
            print("-" * 35)
            for row in results[:10]:
                print(f"{row[0]:<5} {row[1]:<20} {row[3]}")
            if len(results) > 10:
                print(f"... и ещё {len(results) - 10} комнат")

        # ==================== СОХРАНЕНИЕ В ФАЙЛ ====================
        if output_file:
            print("\n" + "=" * 60)
            print(f"СОХРАНЕНИЕ РЕЗУЛЬТАТОВ В ФАЙЛ: {output_file}")
            print("=" * 60)

            if output_format == 'json':
                import json
                json_data = {}
                for query_name, query_data in all_results.items():
                    json_data[query_name] = {
                        'columns': query_data['columns'],
                        'data': []
                    }
                    for row in query_data['data']:
                        json_data[query_name]['data'].append([
                            round(float(val), 2) if hasattr(val, '__float__') else val
                            for val in row
                        ])

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)

            elif output_format == 'xml':
                import xml.etree.ElementTree as ET
                from xml.dom import minidom

                root = ET.Element("results")

                for query_name, query_data in all_results.items():
                    query_elem = ET.SubElement(root, "query", name=query_name)

                    columns_elem = ET.SubElement(query_elem, "columns")
                    for col in query_data['columns']:
                        ET.SubElement(columns_elem, "column").text = col

                    data_elem = ET.SubElement(query_elem, "data")
                    for row in query_data['data']:
                        row_elem = ET.SubElement(data_elem, "row")
                        for i, value in enumerate(row):
                            col_elem = ET.SubElement(row_elem, query_data['columns'][i])
                            if hasattr(value, '__float__'):
                                value = round(float(value), 2)
                            col_elem.text = str(value)

                xml_str = ET.tostring(root, encoding='unicode')
                dom = minidom.parseString(xml_str)
                pretty_xml = dom.toprettyxml(indent="  ")

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(pretty_xml)

            print(f"✓ Результаты сохранены в {output_file}")

        print("\n✅ Все запросы выполнены!")