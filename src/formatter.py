import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Tuple, Any, Dict


class ResultFormatter:
    """Форматирование результатов запросов в JSON или XML"""

    @staticmethod
    def _convert_value(value: Any) -> Any:
        """Преобразует значение для сериализации"""
        if hasattr(value, '__float__'):
            return round(float(value), 2)
        return value

    @staticmethod
    def to_json(data: List[Tuple[Any, ...]], columns: List[str]) -> str:
        """
        Преобразует результаты запроса в JSON

        Args:
            data: список кортежей с данными
            columns: список имён колонок
        """
        result = []
        for row in data:
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = ResultFormatter._convert_value(row[i])
            result.append(row_dict)

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
        root = ET.Element(root_name)

        for row in data:
            row_elem = ET.SubElement(root, "row")
            for i, col_name in enumerate(columns):
                col_elem = ET.SubElement(row_elem, col_name)
                value = ResultFormatter._convert_value(row[i])
                col_elem.text = str(value)

        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        lines = pretty_xml.split('\n')
        if lines[0].startswith('<?xml'):
            return '\n'.join(lines[1:])
        return pretty_xml

    @staticmethod
    def format_query_results(
            query_name: str,
            data: List[Tuple[Any, ...]],
            columns: List[str],
            output_format: str = 'json'
    ) -> str:
        """
        Форматирует результаты одного запроса в указанный формат

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
                "data": [
                    {col: ResultFormatter._convert_value(row[i])
                     for i, col in enumerate(columns)}
                    for row in data
                ]
            }
            return json.dumps(json_data, indent=2, ensure_ascii=False)

        elif output_format.lower() == 'xml':
            root = ET.Element("query", name=query_name)

            columns_elem = ET.SubElement(root, "columns")
            for col in columns:
                ET.SubElement(columns_elem, "column").text = col

            data_elem = ET.SubElement(root, "data")
            for row in data:
                row_elem = ET.SubElement(data_elem, "row")
                for i, value in enumerate(row):
                    col_elem = ET.SubElement(row_elem, columns[i])
                    col_elem.text = str(ResultFormatter._convert_value(value))

            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            return dom.toprettyxml(indent="  ")

        else:
            raise ValueError(f"Неподдерживаемый формат: {output_format}")

    @staticmethod
    def format_all_results(
            all_results: Dict[str, Dict[str, Any]],
            output_format: str = 'json'
    ) -> str:
        """
        Форматирует все результаты запросов в указанный формат

        Args:
            all_results: словарь с результатами всех запросов
            output_format: 'json' или 'xml'
        """
        if output_format.lower() == 'json':
            json_data = {}
            for query_name, query_data in all_results.items():
                json_data[query_name] = {
                    "columns": query_data['columns'],
                    "data": [
                        {col: ResultFormatter._convert_value(row[i])
                         for i, col in enumerate(query_data['columns'])}
                        for row in query_data['data']
                    ]
                }
            return json.dumps(json_data, indent=2, ensure_ascii=False)

        elif output_format.lower() == 'xml':
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
                        col_elem.text = str(ResultFormatter._convert_value(value))

            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            return dom.toprettyxml(indent="  ")

        else:
            raise ValueError(f"Неподдерживаемый формат: {output_format}")