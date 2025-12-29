# manage_celery.py

import subprocess
import sys
import os
import signal
import time


def start_celery():
    """Запуск Celery"""
    print("Запуск Celery...")

    # Запуск worker
    worker_cmd = [
        'celery', '-A', 'config', 'worker',
        '--loglevel=info',
        '--queues=default,emails,maintenance',
        '--concurrency=4',
        '--hostname=worker1@%h'
    ]

    # Запуск beat
    beat_cmd = [
        'celery', '-A', 'config', 'beat',
        '--loglevel=info',
        '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'
    ]

    # Запуск flower
    flower_cmd = [
        'celery', '-A', 'config', 'flower',
        '--port=5555'
    ]

    processes = []

    try:
        print("Запускаем Celery Worker...")
        worker_process = subprocess.Popen(worker_cmd)
        processes.append(worker_process)
        time.sleep(2)

        print("Запускаем Celery Beat...")
        beat_process = subprocess.Popen(beat_cmd)
        processes.append(beat_process)
        time.sleep(2)

        print("Запускаем Flower...")
        flower_process = subprocess.Popen(flower_cmd)
        processes.append(flower_process)

        print("\nCelery успешно запущен!")
        print("Worker: обрабатывает задачи")
        print("Beat: планирует периодические задачи")
        print("Flower: доступен по адресу http://localhost:5555")

        # Ожидаем завершения
        try:
            for process in processes:
                process.wait()
        except KeyboardInterrupt:
            print("\nОстанавливаем Celery...")
            for process in processes:
                process.terminate()
            sys.exit(0)

    except Exception as e:
        print(f"Ошибка запуска Celery: {e}")
        for process in processes:
            if process.poll() is None:
                process.terminate()
        sys.exit(1)


def stop_celery():
    """Остановка Celery"""
    print("Остановка Celery...")

    # Ищем процессы Celery
    try:
        subprocess.run(['pkill', '-f', 'celery'], check=False)
        print("Процессы Celery остановлены")
    except Exception as e:
        print(f"Ошибка остановки Celery: {e}")


def restart_celery():
    """Перезапуск Celery"""
    stop_celery()
    time.sleep(2)
    start_celery()


def check_status():
    """Проверка статуса Celery"""
    print("Проверка статуса Celery...")

    try:
        # Проверяем worker
        result = subprocess.run(
            ['celery', '-A', 'config', 'status'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("Celery worker работает")
            print(result.stdout)
        else:
            print("Celery worker не работает")

        # Проверяем beat
        beat_result = subprocess.run(
            ['pgrep', '-f', 'celery beat'],
            capture_output=True,
            text=True
        )

        if beat_result.returncode == 0:
            print("Celery beat работает")
        else:
            print("Celery beat не работает")

    except Exception as e:
        print(f"Ошибка проверки статуса: {e}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python manage_celery.py [start|stop|restart|status]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'start':
        start_celery()
    elif command == 'stop':
        stop_celery()
    elif command == 'restart':
        restart_celery()
    elif command == 'status':
        check_status()
    else:
        print(f"Неизвестная команда: {command}")
        print("Доступные команды: start, stop, restart, status")