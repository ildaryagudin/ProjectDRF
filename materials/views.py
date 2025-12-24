from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Subscription
from .serializers import SubscriptionSerializer
from .paginators import CoursePagination, LessonPagination


class SubscriptionAPIView(APIView):
    """
    API endpoint for managing course subscriptions.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Toggle subscription for a course.
        """
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if subscription exists
        subscription = Subscription.objects.filter(
            user=user,
            course=course
        ).first()

        if subscription:
            # Toggle subscription status
            subscription.is_active = not subscription.is_active
            subscription.save()

            if subscription.is_active:
                message = 'Subscription activated'
            else:
                message = 'Subscription deactivated'
        else:
            # Create new subscription
            subscription = Subscription.objects.create(
                user=user,
                course=course
            )
            message = 'Subscription created'

        serializer = SubscriptionSerializer(subscription)
        return Response(
            {
                "message": message,
                "subscription": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        """
        Remove subscription for a course.
        """
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = get_object_or_404(
            Subscription,
            user=user,
            course_id=course_id
        )

        subscription.delete()

        return Response(
            {"message": "Subscription removed"},
            status=status.HTTP_204_NO_CONTENT
        )

    def get(self, request, *args, **kwargs):
        """
        Get user's subscriptions.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user, is_active=True)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)


class CourseSubscriptionStatusAPIView(APIView):
    """
    API endpoint for checking subscription status for a course.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, *args, **kwargs):
        """
        Check if user is subscribed to a course.
        """
        user = request.user

        is_subscribed = Subscription.objects.filter(
            user=user,
            course_id=course_id,
            is_active=True
        ).exists()

        return Response({"is_subscribed": is_subscribed})


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course model with CRUD operations.
    """
    queryset = Course.objects.all()
    pagination_class = CoursePagination  # Добавляем пагинацию

class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic view for listing and creating lessons.
    """
    serializer_class = LessonSerializer
    pagination_class = LessonPagination  # Добавляем пагинацию

class SubscriptionAPIView(APIView):
    """
    API endpoint for managing course subscriptions.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Для GET запросов

    def get(self, request, *args, **kwargs):
        """
        Get user's subscriptions with pagination.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user, is_active=True)

        # Apply pagination
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)