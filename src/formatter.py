import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Tuple, Any, Dict


class ResultFormatter:
    """Форматирование результатов запросов в JSON или XML"""

    @staticmethod
    def to_json(data: List[Tuple[Any, ...]], columns: List[str]) -> str:
        """
        Преобразует результаты запроса в JSON

        Args:
            data: список кортежей с данными
            columns: список имён колонок
        """
        # Преобразуем каждый кортеж в словарь
        result = []
        for row in data:
            row_dict = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                # Преобразуем Decimal в float для JSON
                if hasattr(value, '__float__'):
                    value = float(value)
                row_dict[col_name] = value
            result.append(row_dict)

        # Сериализуем в JSON с красивым форматированием
        return json.dumps(result, indent=2, ensure_ascii=False)

    @staticmethod
    def to_xml(data: List[Tuple[Any, ...]], columns: List[str], root_name: str = "results") -> str:
        """
        Преобразует результаты запроса в XML

        Args:
            data: список кортежей с данными
            columns: список имён колонок
            root_name: имя корневого элемента
        """
        # Создаём корневой элемент
        root = ET.Element(root_name)

        # Добавляем строки
        for row in data:
            row_elem = ET.SubElement(root, "row")
            for i, col_name in enumerate(columns):
                col_elem = ET.SubElement(row_elem, col_name)
                value = row[i]
                # Преобразуем Decimal в float
                if hasattr(value, '__float__'):
                    value = float(value)
                col_elem.text = str(value)

        # Преобразуем в строку с красивым форматированием
        xml_str = ET.tostring(root, encoding='unicode')

        # Форматируем XML (добавляем отступы)
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Удаляем лишнюю строку с XML declaration
        lines = pretty_xml.split('\n')
        if lines[0].startswith('<?xml'):
            return '\n'.join(lines[1:])  # убираем первую строку
        return pretty_xml

    @staticmethod
    def format_query_results(
            query_name: str,
            data: List[Tuple[Any, ...]],
            columns: List[str],
            output_format: str = 'json'
    ) -> str:
        """
        Форматирует результаты запроса в указанный формат

        Args:
            query_name: название запроса
            data: данные
            columns: имена колонок
            output_format: 'json' или 'xml'
        """
        if output_format.lower() == 'json':
            json_data = {
                "query": query_name,
                "columns": columns,
                "data": data
            }
            # Преобразуем данные в формат для to_json
            return json.dumps(json_data, indent=2, ensure_ascii=False, default=str)

        elif output_format.lower() == 'xml':
            root = ET.Element("query", name=query_name)

            # Добавляем колонки
            columns_elem = ET.SubElement(root, "columns")
            for col in columns:
                ET.SubElement(columns_elem, "column").text = col

            # Добавляем данные
            data_elem = ET.SubElement(root, "data")
            for row in data:
                row_elem = ET.SubElement(data_elem, "row")
                for i, value in enumerate(row):
                    col_elem = ET.SubElement(row_elem, columns[i])
                    if hasattr(value, '__float__'):
                        value = float(value)
                    col_elem.text = str(value)

            # Форматируем XML
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            return dom.toprettyxml(indent="  ")

        else:
            raise ValueError(f"Неподдерживаемый формат: {output_format}")
