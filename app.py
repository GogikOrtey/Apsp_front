from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import json
import os
from datetime import datetime

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
    """Шаг 3: Выбор опций"""
    # Проверяем, что пользователь прошел предыдущие шаги
    if 'selected_fields' not in session or 'examples_data' not in session:
        return redirect(url_for('step1'))
    
    if request.method == 'POST':
        # Сохраняем данные в сессию
        session['interests'] = request.form.getlist('interests')  # Множественный выбор
        session['newsletter'] = request.form.get('newsletter', 'no')
        session['comments'] = request.form.get('comments', '')
        
        # Переходим на финальный шаг
        return redirect(url_for('summary'))
    
    # Отображаем форму с сохраненными данными
    return render_template('step3.html',
                         interests=session.get('interests', []),
                         newsletter=session.get('newsletter', 'no'),
                         comments=session.get('comments', ''))

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    """Финальная страница: Подтверждение и итог"""
    # Проверяем, что пользователь прошел все шаги
    if 'selected_fields' not in session or 'examples_data' not in session or 'interests' not in session:
        return redirect(url_for('step1'))
    
    # Загружаем описания полей для отображения
    fields = load_fields_descriptions()
    
    if request.method == 'POST':
        if request.form.get('confirm') == 'yes':
            # Собираем все данные из сессии
            selected_fields = session.get('selected_fields', [])
            # Создаем словарь с выбранными полями и их описаниями
            selected_fields_data = {}
            for field_key in selected_fields:
                if field_key in fields:
                    selected_fields_data[field_key] = fields[field_key]
            
            form_data = {
                'selected_fields': selected_fields_data,
                'examples_data': session.get('examples_data', {}),
                'interests': session.get('interests', []),
                'newsletter': session.get('newsletter', 'no'),
                'comments': session.get('comments', '')
            }
            
            # Сохраняем данные в JSON
            save_to_json(form_data)
            
            session['submitted'] = True
            return redirect(url_for('success'))
        else:
            # Возвращаемся на предыдущий шаг
            return redirect(url_for('step3'))
    
    # Собираем все данные для отображения
    selected_fields = session.get('selected_fields', [])
    selected_fields_data = {}
    for field_key in selected_fields:
        if field_key in fields:
            selected_fields_data[field_key] = fields[field_key]
    
    form_data = {
        'selected_fields': selected_fields_data,
        'examples_data': session.get('examples_data', {}),
        'interests': session.get('interests', []),
        'newsletter': session.get('newsletter', 'no'),
        'comments': session.get('comments', '')
    }
    
    return render_template('summary.html', data=form_data)

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

