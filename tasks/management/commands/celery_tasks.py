# tasks/management/commands/celery_tasks.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.tasks import send_course_update_notification
from users.tasks import check_inactive_users, send_inactive_user_warning
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Команды для управления задачами Celery"""

    help = 'Управление задачами Celery'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['test_email', 'check_users', 'warn_users', 'list_tasks'],
            help='Действие: test_email, check_users, warn_users, list_tasks'
        )
        parser.add_argument(
            '--course-id',
            type=int,
            help='ID курса для тестирования email'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'test_email':
            self.test_email(options['course_id'])
        elif action == 'check_users':
            self.check_users()
        elif action == 'warn_users':
            self.warn_users()
        elif action == 'list_tasks':
            self.list_tasks()

    def test_email(self, course_id):
        """Тестирование отправки email уведомлений"""
        if not course_id:
            self.stdout.write(self.style.ERROR('Укажите --course-id для тестирования'))
            return

        self.stdout.write(f"Тестирование отправки уведомлений для курса {course_id}...")

        try:
            # Запускаем задачу синхронно для тестирования
            result = send_course_update_notification.apply(args=[course_id, 'course'])

            if result.successful():
                self.stdout.write(self.style.SUCCESS("Задача успешно выполнена"))
            else:
                self.stdout.write(self.style.ERROR("Ошибка выполнения задачи"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {str(e)}"))

    def check_users(self):
        """Проверка неактивных пользователей"""
        self.stdout.write("Запуск проверки неактивных пользователей...")

        try:
            result = check_inactive_users.apply()

            if result.successful():
                self.stdout.write(self.style.SUCCESS("Проверка пользователей завершена"))
                self.stdout.write(f"Результат: {result.result}")
            else:
                self.stdout.write(self.style.ERROR("Ошибка проверки пользователей"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {str(e)}"))

    def warn_users(self):
        """Отправка предупреждений пользователям"""
        self.stdout.write("Отправка предупреждений пользователям...")

        try:
            result = send_inactive_user_warning.apply(args=[7])

            if result.successful():
                self.stdout.write(self.style.SUCCESS("Предупреждения отправлены"))
            else:
                self.stdout.write(self.style.ERROR("Ошибка отправки предупреждений"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {str(e)}"))

    def list_tasks(self):
        """Список зарегистрированных задач"""
        from celery import current_app

        self.stdout.write("Зарегистрированные задачи Celery:")

        tasks = sorted(current_app.tasks.keys())
        for task in tasks:
            if not task.startswith('celery.'):
                self.stdout.write(f"  - {task}")