from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Важно для работы сессий

@app.route('/')
def index():
    """Главная страница - перенаправление на первый шаг"""
    session.clear()  # Очищаем сессию при начале новой формы
    return redirect(url_for('step1'))

@app.route('/step1', methods=['GET', 'POST'])
def step1():
    """Шаг 1: Личная информация"""
    if request.method == 'POST':
        # Сохраняем данные в сессию
        session['name'] = request.form.get('name', '')
        session['email'] = request.form.get('email', '')
        session['phone'] = request.form.get('phone', '')
        
        # Переходим на следующий шаг
        return redirect(url_for('step2'))
    
    # Отображаем форму с сохраненными данными (если есть)
    return render_template('step1.html', 
                         name=session.get('name', ''),
                         email=session.get('email', ''),
                         phone=session.get('phone', ''))

@app.route('/step2', methods=['GET', 'POST'])
def step2():
    """Шаг 2: Дополнительная информация"""
    # Проверяем, что пользователь прошел первый шаг
    if 'name' not in session:
        return redirect(url_for('step1'))
    
    if request.method == 'POST':
        # Сохраняем данные в сессию
        session['age'] = request.form.get('age', '')
        session['city'] = request.form.get('city', '')
        session['gender'] = request.form.get('gender', '')
        
        # Переходим на следующий шаг
        return redirect(url_for('step3'))
    
    # Отображаем форму с сохраненными данными
    return render_template('step2.html',
                         age=session.get('age', ''),
                         city=session.get('city', ''),
                         gender=session.get('gender', ''))

@app.route('/step3', methods=['GET', 'POST'])
def step3():
    """Шаг 3: Выбор опций"""
    # Проверяем, что пользователь прошел предыдущие шаги
    if 'name' not in session or 'age' not in session:
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
    if 'name' not in session or 'age' not in session or 'interests' not in session:
        return redirect(url_for('step1'))
    
    if request.method == 'POST':
        if request.form.get('confirm') == 'yes':
            # Здесь можно сохранить данные в БД или отправить на обработку
            # Для примера просто очищаем сессию и показываем сообщение
            session['submitted'] = True
            return redirect(url_for('success'))
        else:
            # Возвращаемся на предыдущий шаг
            return redirect(url_for('step3'))
    
    # Собираем все данные для отображения
    form_data = {
        'name': session.get('name', ''),
        'email': session.get('email', ''),
        'phone': session.get('phone', ''),
        'age': session.get('age', ''),
        'city': session.get('city', ''),
        'gender': session.get('gender', ''),
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
    return redirect(url_for('step1'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

