import re
import os


def extract_fields_description(file_path='add_files/Fields_static.ts'):
    """
    Извлекает из файла Fields_static.ts все незакомментированные строки,
    а затем добавляет каждый элемент в словарь, преобразуя структуру
    export const name: field = ['name', 'Наименование товара'];
    в "name": "Наименование товара"
    
    Args:
        file_path: путь к файлу Fields_static.ts
        
    Returns:
        dict: словарь с полями в формате {"name": "Наименование товара", ...}
    """
    fields_dict = {}
    
    # Проверяем существование файла
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден")
        return fields_dict
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Удаляем многострочные комментарии перед обработкой
    content = ''.join(lines)
    # Удаляем многострочные комментарии /** ... */
    content = re.sub(r'/\*\*.*?\*/', '', content, flags=re.DOTALL)
    # Удаляем однострочные комментарии /* ... */
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Обрабатываем каждую строку
    for line in content.split('\n'):
        # Удаляем пробелы в начале и конце
        line = line.strip()
        
        # Пропускаем пустые строки
        if not line:
            continue
        
        # Пропускаем строки, которые закомментированы (начинаются с //)
        if line.startswith('//'):
            continue
        
        # Ищем паттерн: export const name: field = ['name', 'description'];
        # Паттерн поддерживает как одинарные, так и двойные кавычки
        pattern = r'export\s+const\s+(\w+)\s*:\s*field\s*=\s*\[["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']\s*\];?'
        
        match = re.search(pattern, line)
        if match:
            var_name = match.group(1)  # имя переменной (например, 'name')
            # первый элемент массива (например, 'name')
            first_element = match.group(2)
            description = match.group(3)  # описание (например, 'Наименование товара')
            
            # Используем имя переменной как ключ, описание как значение
            fields_dict[var_name] = description
    
    return fields_dict


if __name__ == "__main__":
    # Пример использования
    result = extract_fields_description()
    print("Извлеченные поля:")
    for key, value in result.items():
        print(f'  "{key}": "{value}"')
    
    # Сохраняем результат в JSON для удобства
    import json
    with open('fields_descriptions.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nРезультат сохранен в fields_descriptions.json")
    print(f"Всего извлечено полей: {len(result)}")

