# config/celery.py

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('lms')

# Используем строку настроек из Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач из всех приложений Django
app.autodiscover_tasks()

# Настройки Celery
app.conf.update(
    # Используем Redis как брокер и бэкенд результатов
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,

    # Настройки сериализации
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',

    # Временная зона
    timezone=settings.TIME_ZONE,
    enable_utc=False,

    # Настройки очередей
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'exchange_type': 'direct',
            'routing_key': 'default',
        },
        'emails': {
            'exchange': 'emails',
            'exchange_type': 'direct',
            'routing_key': 'emails',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'exchange_type': 'direct',
            'routing_key': 'maintenance',
        },
    },

    # Настройки расписания периодических задач
    beat_schedule={
        # Проверка неактивных пользователей (каждый день в 3:00)
        'check-inactive-users': {
            'task': 'users.tasks.check_inactive_users',
            'schedule': crontab(hour=3, minute=0),
            'options': {'queue': 'maintenance'},
        },

        # Очистка старых результатов задач (каждую неделю в воскресенье в 4:00)
        'cleanup-task-results': {
            'task': 'users.tasks.cleanup_old_task_results',
            'schedule': crontab(hour=4, minute=0, day_of_week=0),
            'options': {'queue': 'maintenance'},
        },

        # Отправка статистики по курсам (каждый понедельник в 10:00)
        'send-course-statistics': {
            'task': 'materials.tasks.send_course_statistics',
            'schedule': crontab(hour=10, minute=0, day_of_week=1),
            'options': {'queue': 'emails'},
        },
    },

    # Настройки retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,

    # Настройки для долгих задач
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=300000,  # 300MB

    beat_schedule={
        # Проверка неактивных пользователей (каждый день в 3:00)
        'check-inactive-users': {
            'task': 'users.tasks.check_inactive_users',
            'schedule': crontab(hour=3, minute=0),
            'options': {'queue': 'maintenance'},
        },

        # Предупреждение пользователям за 7 дней до блокировки (каждый день в 2:00)
        'send-inactive-user-warnings': {
            'task': 'users.tasks.send_inactive_user_warning',
            'schedule': crontab(hour=2, minute=0),
            'args': (7,),  # За 7 дней до блокировки
            'options': {'queue': 'emails'},
        },

        # Очистка старых результатов задач (каждое воскресенье в 4:00)
        'cleanup-task-results': {
            'task': 'users.tasks.cleanup_old_task_results',
            'schedule': crontab(hour=4, minute=0, day_of_week=0),
            'args': (30,),  # Удалять старше 30 дней
            'options': {'queue': 'maintenance'},
        },

        # Отправка статистики по курсам (каждый понедельник в 10:00)
        'send-course-statistics': {
            'task': 'materials.tasks.send_course_statistics',
            'schedule': crontab(hour=10, minute=0, day_of_week=1),
            'options': {'queue': 'emails'},
        },

        # Проверка и отправка напоминаний о платежах (каждый день в 9:00)
        'send-payment-reminders': {
            'task': 'payments.tasks.send_payment_reminders',
            'schedule': crontab(hour=9, minute=0),
            'options': {'queue': 'emails'},
        },
    },
)


# Добавляем глобальную обработку ошибок
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')