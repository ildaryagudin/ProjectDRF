# users/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(queue='maintenance')
def check_inactive_users():
    """
    Проверка и блокировка пользователей, которые не заходили более месяца

    Задача выполняется каждый день в 3:00
    """
    try:
        logger.info("Начинаем проверку неактивных пользователей...")

        # Вычисляем дату месяц назад
        month_ago = timezone.now() - timedelta(days=30)

        # Находим пользователей, которые не заходили более месяца и активны
        inactive_users = User.objects.filter(
            last_login__lt=month_ago,
            is_active=True
        ).exclude(
            is_superuser=True  # Не блокируем суперпользователей
        )

        user_count = inactive_users.count()

        if user_count == 0:
            logger.info("Неактивных пользователей для блокировки не найдено")
            return

        logger.info(f"Найдено {user_count} неактивных пользователей для блокировки")

        # Блокируем пользователей
        for user in inactive_users:
            try:
                old_status = user.is_active
                user.is_active = False
                user.save(update_fields=['is_active'])

                logger.info(f"Пользователь {user.email} заблокирован "
                            f"(последний вход: {user.last_login})")

                # Можно также отправить уведомление пользователю
                # send_user_blocked_notification.delay(user.id)

            except Exception as e:
                logger.error(f"Ошибка при блокировке пользователя {user.email}: {str(e)}")

        logger.info(f"Завершена блокировка {user_count} неактивных пользователей")

    except Exception as e:
        logger.error(f"Ошибка при проверке неактивных пользователей: {str(e)}")
        raise


@shared_task(queue='maintenance')
def cleanup_old_task_results(days_old=30):
    """
    Очистка старых результатов задач Celery

    Args:
        days_old: Удалять результаты старше N дней (по умолчанию 30)
    """
    try:
        from django_celery_results.models import TaskResult

        cutoff_date = timezone.now() - timedelta(days=days_old)

        # Удаляем старые результаты задач
        deleted_count, _ = TaskResult.objects.filter(
            date_done__lt=cutoff_date
        ).delete()

        logger.info(f"Удалено {deleted_count} старых результатов задач (старше {days_old} дней)")

    except Exception as e:
        logger.error(f"Ошибка при очистке результатов задач: {str(e)}")


@shared_task(queue='maintenance')
def send_inactive_user_warning(days_before=7):
    """
    Отправка предупреждения пользователям, которые скоро будут заблокированы

    Args:
        days_before: За сколько дней до блокировки отправлять предупреждение
    """
    try:
        from tasks.tasks import send_user_warning_email

        # Вычисляем даты
        warning_date = timezone.now() + timedelta(days=days_before)
        last_login_threshold = warning_date - timedelta(days=30)

        # Находим пользователей, которые не заходили более (30 - days_before) дней
        users_to_warn = User.objects.filter(
            last_login__lt=last_login_threshold,
            is_active=True,
            email__isnull=False
        ).exclude(email='')

        logger.info(f"Найдено {users_to_warn.count()} пользователей для отправки предупреждения")

        for user in users_to_warn:
            try:
                # Отправляем предупреждение
                send_user_warning_email.delay(
                    user_id=user.id,
                    days_left=days_before
                )
                logger.info(f"Предупреждение отправлено пользователю {user.email}")

            except Exception as e:
                logger.error(f"Ошибка отправки предупреждения пользователю {user.email}: {str(e)}")

    except Exception as e:
        logger.error(f"Ошибка при отправке предупреждений: {str(e)}")