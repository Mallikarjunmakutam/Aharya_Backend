from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import UserAddress
from .serializers import UserSerializer, UserRegisterSerializer, UserAddressSerializer

import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = get_user_model()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data
        return Response({
            'user': user_data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token with Google
            # Note: For production, you might want to strictly verify the audience using settings.GOOGLE_CLIENT_ID
            CLIENT_ID = settings.GOOGLE_CLIENT_ID
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)

            email = idinfo['email']
            full_name = idinfo.get('name', '')
            profile_image = idinfo.get('picture', '')

            # Check if user exists
            user, created = User.objects.get_or_create(email=email, defaults={
                'full_name': full_name,
                'is_active': True
            })
            
            # If user exists but has no full name, we might want to update it
            if not created and not user.full_name and full_name:
                user.full_name = full_name
                user.save()

            tokens = get_tokens_for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'is_new': created
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)


class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # If this is the default address, unset default on others
        is_default = serializer.validated_data.get('is_default', False)
        if is_default:
            UserAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        is_default = serializer.validated_data.get('is_default', False)
        if is_default:
            UserAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save()


class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

