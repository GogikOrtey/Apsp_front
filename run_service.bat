@echo off
REM Скрипт для запуска Flask сервиса на Windows

cd /d "%~dp0"

REM Проверяем наличие Python
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo Ошибка: Python не найден. Установите Python 3.6 или выше.
        pause
        exit /b 1
    )
)

echo Найден Python
%PYTHON_CMD% --version

REM Создаем виртуальное окружение, если его нет
if not exist "venv" (
    echo Создание виртуального окружения...
    %PYTHON_CMD% -m venv venv
)

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Ошибка: не удалось активировать виртуальное окружение
    pause
    exit /b 1
)

REM Обновляем pip
echo Обновление pip...
python -m pip install --upgrade pip --quiet

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements.txt --quiet

REM Запускаем Flask приложение
echo.
echo Запуск Flask сервиса...
echo Сервис будет доступен по адресу: http://127.0.0.1:5000
echo Для остановки нажмите Ctrl+C
echo.

python app.py

pause

