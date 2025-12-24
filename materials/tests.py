# materials/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status
from .models import Course, Lesson, Subscription

User = get_user_model()


class LessonCRUDTestCase(TestCase):
    """
    Test case for Lesson CRUD operations.
    """

    def setUp(self):
        """Set up test data."""
        # Create groups
        self.moderators_group, _ = Group.objects.get_or_create(name='moderators')
        self.users_group, _ = Group.objects.get_or_create(name='users')

        # Create test users
        self.moderator_user = User.objects.create_user(
            email='moderator@test.com',
            password='testpass123',
            first_name='Moderator',
            last_name='User'
        )
        self.moderator_user.groups.add(self.moderators_group)

        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            first_name='Regular',
            last_name='User'
        )
        self.regular_user.groups.add(self.users_group)

        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        self.other_user.groups.add(self.users_group)

        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course description',
            owner=self.regular_user
        )

        # Create test lesson
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            description='Test lesson description',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            course=self.course,
            owner=self.regular_user
        )

        # Create API clients
        self.moderator_client = APIClient()
        self.user_client = APIClient()
        self.other_client = APIClient()
        self.anonymous_client = APIClient()

        # Authenticate clients
        self.moderator_client.force_authenticate(user=self.moderator_user)
        self.user_client.force_authenticate(user=self.regular_user)
        self.other_client.force_authenticate(user=self.other_user)

    def test_lesson_list_authenticated(self):
        """Test that authenticated users can view lessons list."""
        response = self.user_client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_lesson_list_unauthenticated(self):
        """Test that unauthenticated users cannot view lessons list."""
        response = self.anonymous_client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_create_by_regular_user(self):
        """Test that regular user can create a lesson."""
        data = {
            'title': 'New Lesson',
            'description': 'New lesson description',
            'video_url': 'https://www.youtube.com/watch?v=test123',
            'course': self.course.id
        }
        response = self.user_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(Lesson.objects.last().owner, self.regular_user)

    def test_lesson_create_by_moderator(self):
        """Test that moderator cannot create a lesson."""
        data = {
            'title': 'New Lesson by Moderator',
            'description': 'New lesson description',
            'video_url': 'https://www.youtube.com/watch?v=test456',
            'course': self.course.id
        }
        response = self.moderator_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_retrieve_by_owner(self):
        """Test that lesson owner can retrieve lesson details."""
        url = f'/api/lessons/{self.lesson.id}/'
        response = self.user_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.lesson.title)

    def test_lesson_retrieve_by_moderator(self):
        """Test that moderator can retrieve any lesson details."""
        url = f'/api/lessons/{self.lesson.id}/'
        response = self.moderator_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lesson_update_by_owner(self):
        """Test that lesson owner can update lesson."""
        url = f'/api/lessons/{self.lesson.id}/'
        data = {'title': 'Updated Lesson Title'}
        response = self.user_client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Updated Lesson Title')

    def test_lesson_update_by_moderator(self):
        """Test that moderator can update any lesson."""
        url = f'/api/lessons/{self.lesson.id}/'
        data = {'description': 'Updated by moderator'}
        response = self.moderator_client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.description, 'Updated by moderator')

    def test_lesson_update_by_other_user(self):
        """Test that other user cannot update lesson."""
        url = f'/api/lessons/{self.lesson.id}/'
        data = {'title': 'Trying to update'}
        response = self.other_client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_delete_by_owner(self):
        """Test that lesson owner can delete lesson."""
        url = f'/api/lessons/{self.lesson.id}/'
        response = self.user_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_delete_by_moderator(self):
        """Test that moderator cannot delete lesson."""
        url = f'/api/lessons/{self.lesson.id}/'
        response = self.moderator_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_delete_by_other_user(self):
        """Test that other user cannot delete lesson."""
        url = f'/api/lessons/{self.lesson.id}/'
        response = self.other_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_validation_youtube_url(self):
        """Test YouTube URL validation."""
        data = {
            'title': 'Invalid URL Lesson',
            'description': 'Test description',
            'video_url': 'https://vimeo.com/123456',
            'course': self.course.id
        }
        response = self.user_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_url', response.data)

    def test_lesson_validation_external_links(self):
        """Test external links validation in description."""
        data = {
            'title': 'External Links Lesson',
            'description': 'Check out this site: https://example.com',
            'video_url': 'https://www.youtube.com/watch?v=test789',
            'course': self.course.id
        }
        response = self.user_client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)

    def test_lesson_pagination(self):
        """Test that lessons list is paginated."""
        # Create more lessons for pagination
        for i in range(15):
            Lesson.objects.create(
                title=f'Lesson {i}',
                description=f'Description {i}',
                video_url=f'https://www.youtube.com/watch?v=test{i}',
                course=self.course,
                owner=self.regular_user
            )

        response = self.user_client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('total_pages', response.data)
        self.assertIn('current_page', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 15)  # page_size from LessonPagination


class SubscriptionTestCase(TestCase):
    """
    Test case for subscription functionality.
    """

    def setUp(self):
        """Set up test data."""
        # Create groups
        self.moderators_group, _ = Group.objects.get_or_create(name='moderators')
        self.users_group, _ = Group.objects.get_or_create(name='users')

        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            first_name='User1',
            last_name='Test'
        )
        self.user1.groups.add(self.users_group)

        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            first_name='User2',
            last_name='Test'
        )
        self.user2.groups.add(self.users_group)

        # Create test courses
        self.course1 = Course.objects.create(
            title='Course 1',
            description='Course 1 description',
            owner=self.user1
        )

        self.course2 = Course.objects.create(
            title='Course 2',
            description='Course 2 description',
            owner=self.user2
        )

        # Create API clients
        self.client1 = APIClient()
        self.client2 = APIClient()

        # Authenticate clients
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_subscription_create(self):
        """Test creating a subscription."""
        data = {'course_id': self.course2.id}
        response = self.client1.post('/api/subscriptions/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Subscription created')

        # Check subscription was created
        subscription = Subscription.objects.filter(
            user=self.user1,
            course=self.course2
        ).first()
        self.assertIsNotNone(subscription)
        self.assertTrue(subscription.is_active)

    def test_subscription_toggle(self):
        """Test toggling subscription status."""
        # First, create subscription
        Subscription.objects.create(user=self.user1, course=self.course2)

        # Then toggle it
        data = {'course_id': self.course2.id}
        response = self.client1.post('/api/subscriptions/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Subscription deactivated')

        # Check subscription is deactivated
        subscription = Subscription.objects.get(
            user=self.user1,
            course=self.course2
        )
        self.assertFalse(subscription.is_active)

        # Toggle again to activate
        response = self.client1.post('/api/subscriptions/', data)
        self.assertEqual(response.data['message'], 'Subscription activated')
        subscription.refresh_from_db()
        self.assertTrue(subscription.is_active)

    def test_subscription_delete(self):
        """Test deleting a subscription."""
        # First, create subscription
        Subscription.objects.create(user=self.user1, course=self.course2)

        # Then delete it
        data = {'course_id': self.course2.id}
        response = self.client1.delete('/api/subscriptions/', data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check subscription was deleted
        subscription_exists = Subscription.objects.filter(
            user=self.user1,
            course=self.course2
        ).exists()
        self.assertFalse(subscription_exists)

    def test_subscription_list(self):
        """Test listing user's subscriptions."""
        # Create subscriptions
        Subscription.objects.create(user=self.user1, course=self.course2)
        Subscription.objects.create(user=self.user1, course=self.course1)

        response = self.client1.get('/api/subscriptions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_subscription_status_check(self):
        """Test checking subscription status for a course."""
        # Create subscription
        Subscription.objects.create(user=self.user1, course=self.course2)

        response = self.client1.get(f'/api/subscriptions/{self.course2.id}/status/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])

        # Check for course without subscription
        response = self.client1.get(f'/api/subscriptions/{self.course1.id}/status/')
        self.assertFalse(response.data['is_subscribed'])

    def test_course_with_subscription_status(self):
        """Test that course serializer includes subscription status."""
        # Create subscription
        Subscription.objects.create(user=self.user1, course=self.course2)

        response = self.client1.get(f'/api/courses/{self.course2.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_subscribed', response.data)
        self.assertTrue(response.data['is_subscribed'])

    def test_unique_subscription_constraint(self):
        """Test that user cannot subscribe twice to the same course."""
        # Create first subscription
        Subscription.objects.create(user=self.user1, course=self.course2)

        # Try to create second subscription (should reactivate existing one)
        data = {'course_id': self.course2.id}
        response = self.client1.post('/api/subscriptions/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Subscription deactivated')

        # Check only one subscription exists
        subscription_count = Subscription.objects.filter(
            user=self.user1,
            course=self.course2
        ).count()
        self.assertEqual(subscription_count, 1)

    def test_subscription_pagination(self):
        """Test that subscriptions list is paginated."""
        # Create many subscriptions
        for i in range(25):
            course = Course.objects.create(
                title=f'Course {i}',
                description=f'Description {i}',
                owner=self.user1
            )
            Subscription.objects.create(user=self.user1, course=course)

        response = self.client1.get('/api/subscriptions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('total_pages', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)  # Default page_size


class ValidatorTestCase(TestCase):
    """
    Test case for custom validators.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        self.course = Course.objects.create(
            title='Test Course',
            owner=self.user
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_youtube_url_validator_valid(self):
        """Test valid YouTube URLs."""
        valid_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ',
            'https://youtube.com/embed/dQw4w9WgXcQ',
            'http://www.youtube.com/watch?v=dQw4w9WgXcQ',
        ]

        for url in valid_urls:
            data = {
                'title': 'Test Lesson',
                'description': 'Test description',
                'video_url': url,
                'course': self.course.id
            }
            response = self.client.post('/api/lessons/', data)
            self.assertNotEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"URL {url} should be valid"
            )

    def test_youtube_url_validator_invalid(self):
        """Test invalid URLs (non-YouTube)."""
        invalid_urls = [
            'https://vimeo.com/123456',
            'https://example.com/video',
            'https://dailymotion.com/video',
            'ftp://youtube.com/video',  # Wrong protocol
        ]

        for url in invalid_urls:
            data = {
                'title': 'Test Lesson',
                'description': 'Test description',
                'video_url': url,
                'course': self.course.id
            }
            response = self.client.post('/api/lessons/', data)
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"URL {url} should be invalid"
            )
            self.assertIn('video_url', response.data)

    def test_external_links_validator(self):
        """Test external links validator in description."""
        test_cases = [
            {
                'description': 'Check out https://example.com',
                'should_fail': True
            },
            {
                'description': 'YouTube is okay: https://youtube.com/watch?v=test',
                'should_fail': False
            },
            {
                'description': 'Multiple links: https://example.com and https://youtube.com',
                'should_fail': True
            },
            {
                'description': 'No links here',
                'should_fail': False
            },
        ]

        for test_case in test_cases:
            data = {
                'title': 'Test Lesson',
                'description': test_case['description'],
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'course': self.course.id
            }
            response = self.client.post('/api/lessons/', data)

            if test_case['should_fail']:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('description', response.data)
            else:
                self.assertNotEqual(response.status_code, status.HTTP_400_BAD_REQUEST)