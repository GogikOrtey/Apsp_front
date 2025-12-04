#!/bin/bash

# Скрипт для запуска Flask сервиса (работает на Linux и Windows через Git Bash/WSL)

# Определяем путь к директории скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Проверяем наличие Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Ошибка: Python не найден. Установите Python 3.6 или выше."
    exit 1
fi

# Проверяем версию Python
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Найден Python версии: $PYTHON_VERSION"

# Создаем виртуальное окружение, если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    $PYTHON_CMD -m venv venv
fi

# Активируем виртуальное окружение
if [ -f "venv/bin/activate" ]; then
    # Linux/Mac/WSL
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
else
    echo "Ошибка: не удалось найти скрипт активации виртуального окружения"
    exit 1
fi

# Обновляем pip
echo "Обновление pip..."
pip install --upgrade pip --quiet

# Устанавливаем зависимости
echo "Установка зависимостей..."
pip install -r requirements.txt --quiet

# Запускаем Flask приложение
echo "Запуск Flask сервиса..."
echo "Сервис будет доступен по адресу: http://127.0.0.1:5000"
echo "Для остановки нажмите Ctrl+C"
echo ""

$PYTHON_CMD app.py

