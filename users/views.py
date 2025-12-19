from django_filters import rest_framework as filters
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Payment
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    PaymentSerializer,
    PaymentDetailSerializer,
    UserWithPaymentsSerializer
)
from .filters import PaymentFilter
from .permissions import IsOwnerOrModerator, IsModerator, IsNotModerator


class UserRegistrationAPIView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    Open for everyone (no authentication required).
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserLogoutAPIView(APIView):
    """
    API endpoint for user logout (blacklist refresh token).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'update_profile':
            return UserProfileUpdateSerializer
        elif self.action == 'profile_with_payments':
            return UserWithPaymentsSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Registration should be open for everyone
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'retrieve']:
            # Anyone can view user list and details
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only owner or moderator can update/delete
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        else:
            # Default permission
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['put', 'patch'], url_path='update-profile')
    def update_profile(self, request, pk=None):
        """Update user profile."""
        user = self.get_object()
        serializer = UserProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='payments')
    def user_payments(self, request, pk=None):
        """Get payments history for specific user."""
        user = self.get_object()
        payments = user.payments.all()

        # Apply filtering
        filtered_payments = PaymentFilter(request.GET, queryset=payments).qs

        page = self.paginate_queryset(filtered_payments)
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentSerializer(filtered_payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='profile-with-payments')
    def profile_with_payments(self, request, pk=None):
        """Get user profile with payment history."""
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing payment instances.
    Supports filtering by date, course, lesson, and payment method.
    """
    queryset = Payment.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PaymentFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Override to apply ordering by default."""
        queryset = super().get_queryset()
        # Default ordering: newest payments first
        if not self.request.GET.get('ordering'):
            queryset = queryset.order_by('-payment_date')
        return queryset