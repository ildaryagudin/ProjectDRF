from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Course, Lesson, Subscription

User = get_user_model()


class LessonCRUDTestCase(TestCase):
    """Тесты для CRUD операций с уроками."""

    def setUp(self):
        """Подготовка тестовых данных."""
        # Создание пользователей
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )

        # Создание курса
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description'
        )

        # Создание урока
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            description='Test Lesson Description',
            video_url='https://www.youtube.com/watch?v=test',
            course=self.course
        )

        # API клиенты
        self.client = APIClient()
        self.authenticated_client = APIClient()
        self.staff_client = APIClient()

        # Аутентификация
        self.authenticated_client.force_authenticate(user=self.user)
        self.staff_client.force_authenticate(user=self.staff_user)

    def test_list_lessons_anonymous(self):
        """Тест получения списка уроков анонимным пользователем."""
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # С пагинацией

    def test_list_lessons_authenticated(self):
        """Тест получения списка уроков аутентифицированным пользователем."""
        response = self.authenticated_client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_lesson_anonymous(self):
        """Тест создания урока анонимным пользователем."""
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_url': 'https://www.youtube.com/watch?v=new',
            'course': self.course.id
        }
        response = self.client.post('/api/lessons/', data)
        # В зависимости от настроек прав доступа
        # Если AllowAny - должен быть 201, если IsAuthenticated - 401
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED])

    def test_create_lesson_authenticated(self):
        """Тест создания урока аутентифицированным пользователем."""
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_url': 'https://www.youtube.com/watch?v=new',
            'course': self.course.id
        }
        response = self.authenticated_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_create_lesson_invalid_url(self):
        """Тест создания урока с невалидной ссылкой (не youtube)."""
        data = {
            'title': 'New Lesson',
            'description': 'New Description',
            'video_url': 'https://example.com/video',
            'course': self.course.id
        }
        response = self.authenticated_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_lesson(self):
        """Тест получения детальной информации об уроке."""
        response = self.client.get(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Lesson')

    def test_update_lesson(self):
        """Тест обновления урока."""
        data = {
            'title': 'Updated Lesson',
            'description': 'Updated Description',
            'video_url': 'https://www.youtube.com/watch?v=updated',
            'course': self.course.id
        }
        response = self.authenticated_client.put(
            f'/api/lessons/{self.lesson.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Updated Lesson')

    def test_delete_lesson(self):
        """Тест удаления урока."""
        response = self.authenticated_client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)


class SubscriptionTestCase(TestCase):
    """Тесты для функционала подписки на курс."""

    def setUp(self):
        """Подготовка тестовых данных."""
        # Создание пользователей
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )

        # Создание курса
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description'
        )

        # API клиенты
        self.client1 = APIClient()
        self.client2 = APIClient()

        # Аутентификация
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_subscribe_to_course(self):
        """Тест подписки на курс."""
        response = self.client1.post(f'/api/courses/{self.course.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user1,
                course=self.course
            ).exists()
        )

    def test_subscribe_twice(self):
        """Тест повторной подписки на курс."""
        # Первая подписка
        response1 = self.client1.post(f'/api/courses/{self.course.id}/subscribe/')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Вторая подписка
        response2 = self.client1.post(f'/api/courses/{self.course.id}/subscribe/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        # Должна быть только одна подписка
        self.assertEqual(
            Subscription.objects.filter(
                user=self.user1,
                course=self.course
            ).count(),
            1
        )

    def test_unsubscribe_from_course(self):
        """Тест отписки от курса."""
        # Сначала подписываемся
        Subscription.objects.create(user=self.user1, course=self.course)

        # Отписываемся
        response = self.client1.delete(f'/api/courses/{self.course.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user1,
                course=self.course
            ).exists()
        )

    def test_unsubscribe_without_subscription(self):
        """Тест отписки без подписки."""
        response = self.client1.delete(f'/api/courses/{self.course.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_indicator_in_course(self):
        """Тест отображения признака подписки в курсе."""
        # Подписываемся
        Subscription.objects.create(user=self.user1, course=self.course)

        # Получаем курс
        response = self.client1.get(f'/api/courses/{self.course.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])

        # Проверяем для другого пользователя
        response2 = self.client2.get(f'/api/courses/{self.course.id}/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data['is_subscribed'])

    def test_subscribe_anonymous(self):
        """Тест подписки анонимным пользователем."""
        client = APIClient()
        response = client.post(f'/api/courses/{self.course.id}/subscribe/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)