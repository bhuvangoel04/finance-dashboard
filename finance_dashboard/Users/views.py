"""
User management views — Admin only, except for self-profile read.
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdmin, IsActiveUser
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserPasswordChangeSerializer,
    UserUpdateSerializer,
)

# Create your views here

class LoginView(TokenObtainPairView):
    """POST /api/auth/login/  — returns access + refresh tokens with user info."""
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """GET /api/users/me/  — returns the authenticated user's own profile."""
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response({"success": True, "data": serializer.data})


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/users/       → Admin: list all users
    POST /api/users/       → Admin: create a new user
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdmin]
    queryset = User.objects.all().order_by('-date_joined')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserDetailSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": UserDetailSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/users/<id>/  → Admin: view any user's profile
    PATCH /api/users/<id>/  → Admin: update role, status, names
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({"success": True, "data": UserDetailSerializer(instance).data})

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": UserDetailSerializer(instance).data})


class UserPasswordChangeView(APIView):
    """
    POST /api/users/<id>/set-password/  → Admin: forcefully reset a user's password
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserPasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"success": True, "message": "Password updated successfully."})


class UserDeactivateView(APIView):
    """
    POST /api/users/<id>/deactivate/  → Admin: deactivate (soft-delete) a user
    POST /api/users/<id>/activate/    → Admin: reactivate a user
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdmin]

    def post(self, request, pk, action):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user == request.user:
            return Response(
                {"success": False, "error": {"code": "CONFLICT", "message": "You cannot change your own active status."}},
                status=status.HTTP_409_CONFLICT,
            )

        user.is_active = (action == 'activate')
        user.save()
        state = "activated" if user.is_active else "deactivated"
        return Response({"success": True, "message": f"User {state} successfully."})
