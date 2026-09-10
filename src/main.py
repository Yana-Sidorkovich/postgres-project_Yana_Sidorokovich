import argparse
import os
from src.db_connector import DatabaseConnector
from src.loader import DataLoader
from src.queries import QueryExecutor


def main():
    parser = argparse.ArgumentParser(
        description='Загрузка данных и выполнение запросов к БД'
    )
    parser.add_argument(
        '--students',
        type=str,
        default=None,
        help='Путь к файлу students.json'
    )
    parser.add_argument(
        '--rooms',
        type=str,
        default=None,
        help='Путь к файлу rooms.json'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'xml', 'text'],
        default='text',
        help='Формат вывода результатов (json, xml или text)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Путь к файлу для сохранения результатов (например, results.json)'
    )
    parser.add_argument(
        '--load',
        action='store_true',
        help='Загрузить данные из JSON файлов'
    )

    args = parser.parse_args()

    # Определяем формат
    output_format = args.format
    if args.output and args.format == 'text':
        if args.output.lower().endswith('.json'):
            output_format = 'json'
        elif args.output.lower().endswith('.xml'):
            output_format = 'xml'

    # Пути к файлам по умолчанию
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rooms_file = args.rooms or os.path.join(project_dir, "data", "rooms.json")
    students_file = args.students or os.path.join(project_dir, "data", "students.json")

    # Подключаемся к БД
    db = DatabaseConnector()
    if not db.connect():
        print("Не удалось подключиться к базе данных")
        return

    try:
        # Загрузка данных
        if args.load:
            loader = DataLoader(db)
            loader.load_all(rooms_file, students_file)

        # Выполнение запросов
        executor = QueryExecutor(db)
        executor.run_all_queries(output_format=output_format, output_file=args.output)

    finally:
        db.close()


if __name__ == "__main__":
    main()