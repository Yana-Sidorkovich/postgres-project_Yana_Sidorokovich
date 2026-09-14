from typing import List, Tuple, Any, Dict
from .db_connector import DatabaseConnector
from .formatter import ResultFormatter


class QueryExecutor:
    """Выполнение SQL-запросов для отчётов"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector
        self.formatter = ResultFormatter()

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

        print("\n Добавляем индексы для оптимизации...")
        for idx_query in indexes:
            self.db.execute_query(idx_query)
            print("✓ Индекс создан")

    def execute_all_queries(self) -> Dict[str, Dict[str, Any]]:
        """Выполняет все запросы и возвращает результаты в виде словаря"""
        all_results = {}

        results = self.get_rooms_with_students_count()
        all_results['rooms_with_students_count'] = {
            'columns': ['id', 'name', 'students_count'],
            'data': results
        }

        results = self.get_5_rooms_youngest_students()
        all_results['5_rooms_youngest_students'] = {
            'columns': ['id', 'name', 'avg_age'],
            'data': results
        }

        results = self.get_5_rooms_largest_age_difference()
        all_results['5_rooms_largest_age_difference'] = {
            'columns': ['id', 'name', 'age_difference'],
            'data': results
        }

        results = self.get_rooms_with_different_sex_students()
        all_results['rooms_with_different_sex_students'] = {
            'columns': ['id', 'name', 'sex_count', 'sexes'],
            'data': results
        }

        return all_results

    @staticmethod
    def print_results_console(all_results: Dict[str, Dict[str, Any]]):
        """Выводит результаты в консоль в текстовом формате"""
        print("\n" + "=" * 60)
        print("ЗАПРОС 1: Комнаты и количество студентов")
        print("=" * 60)
        data = all_results['rooms_with_students_count']['data']
        print(f"{'ID':<5} {'Название':<20} {'Студентов':<10}")
        print("-" * 35)
        for row in data[:10]:
            print(f"{row[0]:<5} {row[1]:<20} {row[2]:<10}")
        if len(data) > 10:
            print(f"... и ещё {len(data) - 10} комнат")

        print("\n" + "=" * 60)
        print("ЗАПРОС 2: 5 комнат с наименьшим средним возрастом")
        print("=" * 60)
        data = all_results['5_rooms_youngest_students']['data']
        print(f"{'ID':<5} {'Название':<20} {'Средний возраст':<15}")
        print("-" * 40)
        for row in data:
            print(f"{row[0]:<5} {row[1]:<20} {float(row[2]):.1f}")

        print("\n" + "=" * 60)
        print("ЗАПРОС 3: 5 комнат с наибольшей разницей в возрасте")
        print("=" * 60)
        data = all_results['5_rooms_largest_age_difference']['data']
        print(f"{'ID':<5} {'Название':<20} {'Разница в возрасте':<20}")
        print("-" * 45)
        for row in data:
            print(f"{row[0]:<5} {row[1]:<20} {float(row[2]):.1f}")

        print("\n" + "=" * 60)
        print("ЗАПРОС 4: Комнаты с разными полами студентов")
        print("=" * 60)
        data = all_results['rooms_with_different_sex_students']['data']
        print(f"{'ID':<5} {'Название':<20} {'Полы':<10}")
        print("-" * 35)
        for row in data[:10]:
            print(f"{row[0]:<5} {row[1]:<20} {row[3]}")
        if len(data) > 10:
            print(f"... и ещё {len(data) - 10} комнат")

    def save_results_to_file(self, all_results: Dict[str, Dict[str, Any]],
                              output_format: str, output_file: str):
        """Сохраняет результаты в файл в указанном формате"""
        print("\n" + "=" * 60)
        print(f"СОХРАНЕНИЕ РЕЗУЛЬТАТОВ В ФАЙЛ: {output_file}")
        print("=" * 60)

        formatted = self.formatter.format_all_results(all_results, output_format)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted)

        print(f"✓ Результаты сохранены в {output_file}")

    def run_all_queries(self, output_format: str = 'text', output_file: str = None):
        """Главный метод — координирует выполнение всех запросов"""
        print("\n" + "=" * 60)
        print("ДОБАВЛЕНИЕ ИНДЕКСОВ ДЛЯ ОПТИМИЗАЦИИ")
        print("=" * 60)
        self.add_indexes()

        all_results = self.execute_all_queries()

        if output_format in ('json', 'xml'):
            for query_name, query_data in all_results.items():
                formatted = self.formatter.format_query_results(
                    query_name,
                    query_data['data'],
                    query_data['columns'],
                    output_format
                )
                print(formatted)
        else:
            self.print_results_console(all_results)

        if output_file:
            self.save_results_to_file(all_results, output_format, output_file)

        print("\n✅ Все запросы выполнены!")