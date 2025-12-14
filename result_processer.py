"""
Модуль для обработки данных из шагов 2 и 3
Собирает данные в единый JSON формат data_input_table
"""
import json


def process_results(examples_data, search_requests_data):
    """
    Собирает данные из шагов 2 и 3 в единый JSON формат
    
    Args:
        examples_data: Данные из шага 2 (содержит "simple")
        search_requests_data: Данные из шага 3 (содержит "search_requests")
    
    Returns:
        dict: Собранный JSON в формате data_input_table
    """
    # Инициализируем структуру результата
    data_input_table = {
        "host": "",
        "fields_str": "",
        "links": {
            "simple": examples_data.get("simple", []) if examples_data else []
        },
        "search_requests": search_requests_data.get("search_requests", []) if search_requests_data else []
    }
    
    # Выводим результат в консоль
    print('\n' + '=' * 30)
    print('ОБРАБОТКА РЕЗУЛЬТАТОВ (data_input_table)')
    print('=' * 30)
    print('\nИтоговый JSON (data_input_table):')
    print(json.dumps(data_input_table, ensure_ascii=False, indent=2))
    print('\n' + '=' * 30 + '\n')
    
    return data_input_table

