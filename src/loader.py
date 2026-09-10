import json
from typing import List, Dict, Any
from .models import Room, Student
from .db_connector import DatabaseConnector


class DataLoader:
    """Загрузка данных из JSON файлов в базу данных"""

    def __init__(self, db_connector: DatabaseConnector):
        self.db = db_connector

    def load_rooms(self, json_path: str) -> int:
        """
        Загружает комнаты из JSON файла и создаёт таблицу rooms
        Возвращает количество загруженных записей
        """
        # Читаем JSON файл
        with open(json_path, 'r', encoding='utf-8') as f:
            rooms_data: List[Dict[str, Any]] = json.load(f)

        # Создаём таблицу rooms
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS rooms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """)

        # Очищаем таблицу rooms И все зависимые таблицы (students) через CASCADE
        self.db.execute_query("TRUNCATE TABLE rooms RESTART IDENTITY CASCADE")

        # Подготавливаем данные для массовой вставки
        rooms_to_insert = [(room['id'], room['name']) for room in rooms_data]

        # Вставляем данные
        self.db.execute_many(
            "INSERT INTO rooms (id, name) VALUES (%s, %s)",
            rooms_to_insert
        )

        print(f"✓ Загружено {len(rooms_data)} комнат")
        return len(rooms_data)

    def load_students(self, json_path: str) -> int:
        """
        Загружает студентов из JSON файла и создаёт таблицу students
        Возвращает количество загруженных записей
        """
        # Читаем JSON файл
        with open(json_path, 'r', encoding='utf-8') as f:
            students_data: List[Dict[str, Any]] = json.load(f)

        # Создаём таблицу students
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                birthday DATE NOT NULL,
                sex CHAR(1) NOT NULL,
                room INT REFERENCES rooms(id)
            )
        """)

        # Очищаем таблицу students (rooms уже очищены через CASCADE выше)
        self.db.execute_query("TRUNCATE TABLE students RESTART IDENTITY")

        # Подготавливаем данные для массовой вставки
        # Обрезаем время из birthday (оставляем только дату)
        students_to_insert = [
            (
                student['id'],
                student['name'],
                student['birthday'].split('T')[0],  # "2011-08-22T00:00:00" → "2011-08-22"
                student['sex'],
                student['room']  # foreign key к rooms.id
            )
            for student in students_data
        ]

        # Вставляем данные
        self.db.execute_many(
            "INSERT INTO students (id, name, birthday, sex, room) VALUES (%s, %s, %s, %s, %s)",
            students_to_insert
        )

        print(f"✓ Загружено {len(students_data)} студентов")
        return len(students_data)

    def load_all(self, rooms_path: str, students_path: str):
        """Загружает все данные (комнаты и студенты)"""
        print("\nНачинаем загрузку данных...")

        rooms_count = self.load_rooms(rooms_path)
        students_count = self.load_students(students_path)

        print(f"\nЗагрузка завершена!")
        print(f"   Комнат: {rooms_count}")
        print(f"   Студентов: {students_count}\n")
