from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import json
import os
from datetime import datetime
from result_processer import process_results

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Важно для работы сессий

# Создаем папку data, если её нет
os.makedirs('data', exist_ok=True)

# Путь к JSON файлу
JSON_FILE = 'data/submissions.json'
FIELDS_DESCRIPTIONS_FILE = 'fields_descriptions.json'

def load_fields_descriptions():
    """Загрузка описаний полей из JSON файла"""
    if os.path.exists(FIELDS_DESCRIPTIONS_FILE):
        with open(FIELDS_DESCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('fields', {})
    return {}

def save_to_json(data):
    """Сохранение данных в JSON файл"""
    # Загружаем существующие данные
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                submissions = json.load(f)
            except json.JSONDecodeError:
                submissions = []
    else:
        submissions = []
    
    # Добавляем новую запись с временной меткой
    submission = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **data
    }
    submissions.append(submission)
    
    # Сохраняем обратно в файл
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """Главная страница - перенаправление на нулевой шаг"""
    session.clear()  # Очищаем сессию при начале новой формы
    return redirect(url_for('step0'))

@app.route('/step0')
def step0():
    """Нулевой шаг: Приветственное сообщение"""
    return render_template('step0.html')

@app.route('/step1', methods=['GET', 'POST'])
def step1():
    """Шаг 1: Выбор полей"""
    # Загружаем описания полей
    fields = load_fields_descriptions()
    
    if request.method == 'POST':
        # Сохраняем выбранные поля в сессию
        selected_fields = request.form.getlist('selected_fields')
        
        # Сортируем выбранные поля в том же порядке, как они расположены на странице
        # (в порядке, как они идут в fields)
        fields_order = list(fields.keys())
        selected_fields_sorted = [field for field in fields_order if field in selected_fields]
        
        # Удаляем "timestamp" из выбранных полей
        if 'timestamp' in selected_fields_sorted:
            selected_fields_sorted.remove('timestamp')
        
        # Удаляем "stock" из выбранных полей и заменяем на триггеры
        if 'stock' in selected_fields_sorted:
            selected_fields_sorted.remove('stock')
            # Добавляем триггеры вместо stock
            if 'InStock_trigger' not in selected_fields_sorted:
                selected_fields_sorted.append('InStock_trigger')
            if 'OutOfStock_trigger' not in selected_fields_sorted:
                selected_fields_sorted.append('OutOfStock_trigger')
        
        session['selected_fields'] = selected_fields_sorted
        
        # Переходим на следующий шаг
        return redirect(url_for('step2'))
    
    # Отображаем форму с сохраненными данными (если есть)
    # На первом шаге показываем только "stock", а не триггеры
    # Фильтруем поля для отображения: убираем триггеры, оставляем stock
    fields_for_display = {k: v for k, v in fields.items() 
                         if k not in ['InStock_trigger', 'OutOfStock_trigger']}
    
    # Восстанавливаем selected_fields для отображения: если есть триггеры, заменяем их на stock
    selected_fields = session.get('selected_fields', [])
    selected_fields_for_display = []
    has_triggers = False
    for field in selected_fields:
        if field in ['InStock_trigger', 'OutOfStock_trigger']:
            has_triggers = True
        else:
            selected_fields_for_display.append(field)
    
    # Если были триггеры, добавляем stock в selected_fields_for_display
    if has_triggers and 'stock' not in selected_fields_for_display:
        selected_fields_for_display.append('stock')
    
    return render_template('step1.html', 
                         fields=fields_for_display,
                         selected_fields=selected_fields_for_display)

@app.route('/step2', methods=['GET', 'POST'])
def step2():
    """Шаг 2: Заполнение полей примерами"""
    # Проверяем, что пользователь прошел первый шаг
    if 'selected_fields' not in session:
        return redirect(url_for('step1'))
    
    # Загружаем описания полей
    fields = load_fields_descriptions()
    selected_fields = session.get('selected_fields', [])
    
    # Выводим выбранные поля в консоль сервера при переходе на шаг 2
    if request.method == 'GET':
        print('\n=== Выбранные поля (переход на шаг 2) ===')
        print(f'Количество выбранных полей: {len(selected_fields)}')
        print('Выбранные поля:')
        for field in selected_fields:
            print(f'  - {field}')
        print('=' * 30 + '\n')
    
    if request.method == 'POST':
        # Собираем данные примеров из формы
        # Формат полей: example_{номер}_{field_key}
        examples_data = {}
        
        # Определяем количество примеров по форме
        example_numbers = set()
        for key in request.form.keys():
            if key.startswith('example_'):
                parts = key.split('_', 2)
                if len(parts) >= 3:
                    example_numbers.add(parts[1])
        
        # Сортируем номера примеров
        sorted_example_numbers = sorted([int(num) for num in example_numbers])
        
        # Формируем список примеров
        examples_list = []
        for example_num in sorted_example_numbers:
            example_dict = {}
            for field_key in selected_fields:
                field_name = f'example_{example_num}_{field_key}'
                field_value = request.form.get(field_name, '')
                # Добавляем все поля, даже с пустыми значениями
                example_dict[field_key] = field_value
            
            # Добавляем все примеры, даже если все поля пустые
            examples_list.append(example_dict)
        
        # Формируем итоговый JSON
        result_json = {
            "simple": examples_list
        }
        
        # Выводим результат в консоль
        print('\n=== Результаты заполнения полей (шаг 2) ===')
        print(json.dumps(result_json, ensure_ascii=False, indent=2))
        print('=' * 30 + '\n')
        
        # Сохраняем данные примеров в сессию
        session['examples_data'] = result_json
        
        # Переходим на следующий шаг
        return redirect(url_for('step3'))
    
    # Отображаем форму с сохраненными данными
    # Создаем словарь описаний только для выбранных полей
    fields_descriptions = {field_key: fields.get(field_key, field_key) 
                          for field_key in selected_fields}
    
    return render_template('step2.html',
                         selected_fields=selected_fields,
                         fields_descriptions=fields_descriptions)

@app.route('/step3', methods=['GET', 'POST'])
def step3():
    """Шаг 3: Вставьте данные для parsePage"""
    # Проверяем, что пользователь прошел предыдущие шаги
    if 'selected_fields' not in session or 'examples_data' not in session:
        return redirect(url_for('step1'))
    
    if request.method == 'POST':
        # Собираем данные из формы
        query = request.form.get('query', '')
        url_search_query_page_2 = request.form.get('url_search_query_page_2', '')
        count_of_page_on_pagination = request.form.get('count_of_page_on_pagination', '')
        total_count_of_results = request.form.get('total_count_of_results', '')
        
        # Собираем все поля links_items (links_items_0, links_items_1, и т.д.)
        links_items = []
        for key in sorted(request.form.keys()):
            if key.startswith('links_items_'):
                value = request.form.get(key, '').strip()
                # Добавляем только непустые значения
                if value:
                    links_items.append(value)
        
        # Формируем объект поискового запроса
        search_request = {
            "query": query,
            "url_search_query_page_2": url_search_query_page_2,
            "count_of_page_on_pagination": count_of_page_on_pagination,
            "total_count_of_results": total_count_of_results,
            "links_items": links_items
        }
        
        # Формируем итоговый JSON
        result_json = {
            "search_requests": [search_request]
        }
        
        # Выводим результат в консоль
        print('\n=== Результаты заполнения полей (шаг 3) ===')
        print(json.dumps(result_json, ensure_ascii=False, indent=2))
        print('=' * 30 + '\n')
        
        # Сохраняем данные в сессию
        session['search_requests_data'] = result_json
        
        # Обрабатываем и валидируем данные из шагов 2 и 3
        examples_data = session.get('examples_data', {})
        process_results(examples_data, result_json)
        
        # Удаляем редактированный JSON из сессии, чтобы он был собран заново из данных шагов 2 и 3
        if 'result_json' in session:
            del session['result_json']
        
        # Переходим на следующий шаг (step4 - бывший summary)
        return redirect(url_for('step4'))
    
    # Отображаем форму с сохраненными данными
    # Восстанавливаем данные из сессии, если есть
    search_requests_data = session.get('search_requests_data', {})
    saved_data = {}
    if search_requests_data and 'search_requests' in search_requests_data and len(search_requests_data['search_requests']) > 0:
        saved_data = search_requests_data['search_requests'][0]
    
    return render_template('step3.html',
                         saved_data=saved_data)

@app.route('/step4', methods=['GET', 'POST'])
def step4():
    """Шаг 4: Подтверждение и итог"""
    # Проверяем, что пользователь прошел все шаги
    if 'selected_fields' not in session or 'examples_data' not in session or 'search_requests_data' not in session:
        return redirect(url_for('step1'))
    
    # Загружаем описания полей для отображения
    fields = load_fields_descriptions()
    
    if request.method == 'POST':
        # Получаем отредактированный JSON из формы
        edited_json_str = request.form.get('edited_json', '')
        
        if edited_json_str.strip():
            try:
                # Парсим и сохраняем отредактированный JSON в сессию
                edited_json = json.loads(edited_json_str)
                session['result_json'] = edited_json
                
                # Выводим отредактированный JSON в консоль сервера
                print('\n=== Отредактированный JSON (шаг 4) ===')
                print(json.dumps(edited_json, ensure_ascii=False, indent=2))
                print('=' * 30 + '\n')
            except json.JSONDecodeError:
                # Если JSON невалидный (хотя валидация должна была пройти на клиенте),
                # все равно пробуем перейти, но используем данные из сессии
                print('\n=== ОШИБКА: JSON невалидный ===')
                print('Используются данные из сессии\n')
        
        # Переходим на следующий шаг
        return redirect(url_for('step5'))
    
    # Проверяем, есть ли уже сохраненный отредактированный JSON
    # (если пользователь вернулся с шага 5, показываем его отредактированный JSON)
    result_json = session.get('result_json')
    
    if result_json is None:
        # Если сохраненного JSON нет, формируем новый из шагов 2 и 3
        # (пользователь пришел с шага 3)
        examples_data = session.get('examples_data', {})
        search_requests_data = session.get('search_requests_data', {})
        result_json = process_results(examples_data, search_requests_data)
        
        # Сохраняем результат в сессию для последующего использования
        session['result_json'] = result_json
    
    # Сериализуем JSON в строку с сохранением порядка ключей (sort_keys=False по умолчанию)
    # и передаем строку в шаблон, чтобы избежать сортировки ключей фильтром tojson
    result_json_str = json.dumps(result_json, ensure_ascii=False, indent=2, sort_keys=False)
    
    return render_template('step4.html', result_json_str=result_json_str)

@app.route('/step5', methods=['GET', 'POST'])
def step5():
    """Шаг 5: Генерация кода"""
    # Проверяем, что пользователь прошел все предыдущие шаги
    if 'selected_fields' not in session or 'examples_data' not in session or 'search_requests_data' not in session:
        return redirect(url_for('step1'))
    
    # Загружаем описания полей для отображения
    fields = load_fields_descriptions()
    
    if request.method == 'POST':
        # Получаем код из формы
        code = request.form.get('code', '')
        
        # Сохраняем код в сессию
        session['code'] = code
        
        # Проверяем, был ли отредактирован JSON на шаге 4
        result_json = session.get('result_json', {})
        
        # Формируем итоговые данные для сохранения
        selected_fields = session.get('selected_fields', [])
        selected_fields_data = {}
        for field_key in selected_fields:
            if field_key in fields:
                selected_fields_data[field_key] = fields[field_key]
        
        form_data = {
            'selected_fields': selected_fields_data,
            'examples_data': session.get('examples_data', {}),
            'search_requests_data': session.get('search_requests_data', {}),
            'code': code
        }
        
        # Сохраняем данные в JSON
        save_to_json(form_data)
        
        session['submitted'] = True
        return redirect(url_for('success'))
    
    # Отображаем форму с сохраненными данными
    saved_data = {'code': session.get('code', '')}
    
    return render_template('step5.html', saved_data=saved_data)


@app.route('/success')
def success():
    """Страница успешной отправки"""
    if not session.get('submitted'):
        return redirect(url_for('step1'))
    
    # Очищаем сессию после успешной отправки
    session.clear()
    return render_template('success.html')

@app.route('/reset')
def reset():
    """Сброс формы - возврат к началу"""
    session.clear()
    return redirect(url_for('step0'))

@app.route('/content/<path:filename>')
def content(filename):
    """Обслуживание статических файлов из папки content"""
    return send_from_directory('content', filename)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

