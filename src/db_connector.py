import psycopg2
from psycopg2 import sql, Error
from typing import Optional, List, Tuple, Any
import os
from dotenv import load_dotenv


class DatabaseConnector:

    def __init__(self):
        # Загружаем переменные окружения из .env файла
        load_dotenv()

        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB')
        self.user = os.getenv('POSTGRES_USER')
        self.password = os.getenv('POSTGRES_PASSWORD')

        if not all([self.host, self.port, self.database, self.user, self.password]):
            raise ValueError("Не все переменные окружения загружены из .env файла!")

        self.connection: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None

    def connect(self) -> bool:
        """Подключается к базе данных"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            print(f"✓ Подключено к базе данных: {self.database}")
            return True
        except Error as e:
            print(f"✗ Ошибка подключения: {e}")
            return False

    def execute_query(self, query: str, params: tuple = None) -> List[Tuple[Any, ...]]:
        """Выполняет SQL запрос и возвращает результаты"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()

            # Если запрос возвращает данные (SELECT)
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            return []
        except Error as e:
            print(f"✗ Ошибка выполнения запроса: {e}")
            self.connection.rollback()
            return []

    def execute_many(self, query: str, params_list: List[tuple]) -> bool:
        """Выполняет множество однотипных запросов (для массовой вставки)"""
        try:
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return True
        except Error as e:
            print(f"✗ Ошибка массовой вставки: {e}")
            self.connection.rollback()
            return False

    def close(self):
        """Закрывает подключение"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✓ Подключение закрыто")
