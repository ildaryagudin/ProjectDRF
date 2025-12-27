import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from materials.models import Course
from payments.services import StripeService

User = get_user_model()


def create_test_payments():
    """Создание тестовых платежей"""

    print("Создаем тестовые платежи...")

    # Получаем пользователя и курс
    user = User.objects.filter(email__contains='test').first()
    if not user:
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Тестовый',
            last_name='Пользователь'
        )

    course = Course.objects.first()
    if not course:
        course = Course.objects.create(
            title='Тестовый курс по Python',
            description='Курс для тестирования оплаты',
            owner=user
        )

    print(f"Используем пользователя: {user.email}")
    print(f"Используем курс: {course.title}")

    # Создаем тестовый платеж
    try:
        print("\nСоздаем оплату курса...")
        result = StripeService.create_course_payment(
            course=course,
            user=user,
            amount=2990.00
        )
        print(f"✓ Оплата курса создана")
        print(f"  ID платежа: {result['payment_id']}")
        print(f"  Ссылка на оплату: {result['checkout_url'][:50]}...")

        print("\nТестовые платежи созданы!")
        print("\nДля тестирования используйте:")
        print("  - Номер карты: 4242 4242 4242 4242")
        print("  - Срок: 12/34")
        print("  - CVC: 123")
        print("  - Почтовый индекс: 12345")

    except Exception as e:
        print(f"✗ Ошибка создания платежа: {str(e)}")


if __name__ == '__main__':
    create_test_payments()