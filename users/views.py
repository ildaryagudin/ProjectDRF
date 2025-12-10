from django_filters import rest_framework as filters
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Payment
from .serializers import (
    UserSerializer,
    UserProfileUpdateSerializer,
    PaymentSerializer,
    PaymentDetailSerializer,
    UserWithPaymentsSerializer
)
from .filters import PaymentFilter


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

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
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        return Response(
            {'detail': 'Authentication credentials were not provided.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=True, methods=['get'], url_path='payments')
    def user_payments(self, request, pk=None):
        """Get payments history for specific user."""
        user = self.get_object()
        payments = user.payments.all()

        # Применяем фильтрацию
        filtered_payments = PaymentFilter(request.GET, queryset=payments).qs

        page = self.paginate_queryset(filtered_payments)
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentSerializer(filtered_payments, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing payment instances.
    Supports filtering by date, course, lesson, and payment method.
    """
    queryset = Payment.objects.all()
    permission_classes = [permissions.AllowAny]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PaymentFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer

    def get_queryset(self):
        """Override to apply ordering by default."""
        queryset = super().get_queryset()
        # Сортировка по умолчанию: сначала новые платежи
        if not self.request.GET.get('ordering'):
            queryset = queryset.order_by('-payment_date')
        return queryset