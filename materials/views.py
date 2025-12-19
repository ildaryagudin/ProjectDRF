from rest_framework import viewsets, generics, permissions, filters
from rest_framework.response import Response
from .models import Course, Lesson
from .serializers import CourseSerializer, CourseListSerializer, LessonSerializer
from users.permissions import IsOwnerOrModerator, IsModerator, IsNotModerator


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course model with CRUD operations.
    """
    queryset = Course.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list':
            # Anyone can view course list
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'retrieve':
            # Anyone can view course details
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            # Only non-moderators can create courses
            permission_classes = [permissions.IsAuthenticated, IsNotModerator]
        elif self.action in ['update', 'partial_update']:
            # Only owner or moderator can update
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        elif self.action == 'destroy':
            # Only owner can delete (moderators cannot delete)
            permission_classes = [permissions.IsAuthenticated, ~IsModerator, IsOwnerOrModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Automatically set the owner to the current user when creating a course."""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user

        # If user is moderator, show all courses
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()

        # Otherwise, show only user's own courses
        return Course.objects.filter(owner=user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic view for listing and creating lessons.
    """
    serializer_class = LessonSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'GET':
            permission_classes = [permissions.IsAuthenticated]
        elif self.request.method == 'POST':
            # Only non-moderators can create lessons
            permission_classes = [permissions.IsAuthenticated, IsNotModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user

        # If user is moderator, show all lessons
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()

        # Otherwise, show only user's own lessons
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        """Automatically set the owner to the current user when creating a lesson."""
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic view for retrieving, updating and deleting a lesson.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'GET':
            permission_classes = [permissions.IsAuthenticated]
        elif self.request.method in ['PUT', 'PATCH']:
            # Only owner or moderator can update
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        elif self.request.method == 'DELETE':
            # Only owner can delete (moderators cannot delete)
            permission_classes = [permissions.IsAuthenticated, ~IsModerator, IsOwnerOrModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user

        # If user is moderator, show all lessons
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()

        # Otherwise, show only user's own lessons
        return Lesson.objects.filter(owner=user)