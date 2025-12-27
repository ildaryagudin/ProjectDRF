from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from materials.models import Course
from payments.services import StripeService

User = get_user_model()


class Command(BaseCommand):
    """Тестирование интеграции со Stripe"""

    help = 'Тестирование функционала оплаты через Stripe'

    def handle(self, *args, **kwargs):
        self.stdout.write("Начинаем тестирование интеграции со Stripe...")

        # Получаем тестовые данные
        try:
            user = User.objects.first()
            course = Course.objects.first()

            if not user or not course:
                self.stdout.write(
                    self.style.ERROR('Сначала создайте тестового пользователя и курс')
                )
                return

            self.stdout.write(f"Используем пользователя: {user.email}")
            self.stdout.write(f"Тестируем курс: {course.title}")

            # Тестируем создание продукта
            self.stdout.write("\n1. Тестируем создание продукта в Stripe...")
            try:
                product = StripeService.create_product(
                    name=f"Тестовый продукт: {course.title}",
                    description="Это тестовый продукт для интеграции",
                    metadata={'test': 'true', 'course_id': str(course.id)}
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Продукт создан: {product.id}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Ошибка создания продукта: {str(e)}")
                )
                return

            # Тестируем создание цены
            self.stdout.write("\n2. Тестируем создание цены в Stripe...")
            try:
                price = StripeService.create_price(
                    product_id=product.id,
                    unit_amount=99900,  # $999.00
                    currency='usd'
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Цена создана: {price.id}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Ошибка создания цены: {str(e)}")
                )
                return

            # Тестируем создание сессии оплаты
            self.stdout.write("\n3. Тестируем создание сессии оплаты...")
            try:
                session = StripeService.create_checkout_session(
                    price_id=price.id,
                    success_url='https://example.com/success',
                    cancel_url='https://example.com/cancel',
                    metadata={'test': 'true'},
                    customer_email=user.email
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Сессия создана: {session.id}")
                )
                self.stdout.write(f"   Ссылка на оплату: {session.url}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Ошибка создания сессии: {str(e)}")
                )
                return

            # Тестируем полный процесс оплаты курса
            self.stdout.write("\n4. Тестируем полный процесс оплаты курса...")
            try:
                result = StripeService.create_course_payment(
                    course=course,
                    user=user,
                    amount=2990.00
                )
                self.stdout.write(
                    self.style.SUCCESS("✓ Процесс оплаты курса тестирован успешно")
                )
                self.stdout.write(f"   ID платежа: {result['payment_id']}")
                self.stdout.write(f"   Ссылка на оплату: {result['checkout_url']}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Ошибка процесса оплаты: {str(e)}")
                )

            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("Тестирование Stripe завершено!"))
            self.stdout.write("\nТестовые данные для оплаты:")
            self.stdout.write("  - Номер карты: 4242 4242 4242 4242")
            self.stdout.write("  - Срок действия: любая будущая дата")
            self.stdout.write("  - CVC: любые 3 цифры")
            self.stdout.write("  - Почтовый индекс: любые 5 цифр")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка тестирования: {str(e)}"))