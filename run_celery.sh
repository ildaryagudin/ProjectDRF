#!/bin/bash
# run_celery.sh

echo "=== Запуск системы Celery ==="

# Активация виртуального окружения (если нужно)
if [ -d "venv" ]; then
    echo "Активируем виртуальное окружение..."
    source venv/bin/activate
fi

# Проверка Redis
echo "Проверяем Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ВНИМАНИЕ: Redis не запущен!"
    echo "Запустите Redis одним из способов:"
    echo "1. redis-server (в отдельном терминале)"
    echo "2. docker-compose up redis"
    echo "3. sudo systemctl start redis"
    read -p "Запустить Redis сейчас? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Запускаем Redis в фоновом режиме..."
        redis-server --daemonize yes
        sleep 3
        if redis-cli ping > /dev/null 2>&1; then
            echo "✓ Redis запущен"
        else
            echo "✗ Не удалось запустить Redis"
            exit 1
        fi
    else
        echo "Продолжаем без Redis..."
    fi
else
    echo "✓ Redis работает"
fi

# Применение миграций для Celery Beat
echo "Проверяем миграции Celery Beat..."
python manage.py migrate django_celery_beat

# Запуск Celery Worker
echo "Запускаем Celery Worker..."
celery -A config worker \
    --loglevel=info \
    --queues=default,emails,maintenance \
    --concurrency=4 \
    --hostname=worker1@%h \
    --detach  # Запуск в фоне
echo "✓ Worker запущен (PID: $!)"

# Запуск Celery Beat
echo "Запускаем Celery Beat..."
celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --detach  # Запуск в фоне
echo "✓ Beat запущен (PID: $!)"

# Запуск Flower (опционально)
echo "Запускаем Flower (мониторинг)..."
celery -A config flower \
    --port=5555 \
    --broker_api=http://localhost:6379/ \
    --detach  # Запуск в фоне
echo "✓ Flower запущен на http://localhost:5555"

echo ""
echo "========================================"
echo "✅ Celery успешно запущен!"
echo ""
echo "Доступные компоненты:"
echo "  • Worker:   Обрабатывает задачи"
echo "  • Beat:     Планирует периодические задачи"
echo "  • Flower:   http://localhost:5555 (мониторинг)"
echo ""
echo "Для остановки выполните:"
echo "  ./stop_celery.sh  или  pkill -f celery"
echo "========================================"