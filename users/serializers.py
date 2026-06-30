from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserAddress

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'name', 'phone', 'profile_image', 'created_at', 'is_staff', 'is_active']
        read_only_fields = ['id', 'created_at']

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        error_messages={
            'unique': 'Mail ID already exists'
        }
    )

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            phone=validated_data.get('phone', '')
        )
        return user

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'
        read_only_fields = ['user']


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth.models import update_last_login

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get(self.username_field)
        password = attrs.get('password')
        
        # Normalize email/username
        normalized_username = User.objects.normalize_email(username)
        
        # Check if user exists
        if not User.objects.filter(email__iexact=normalized_username).exists():
            raise serializers.ValidationError({
                "detail": "Account does not exist"
            }, code="authorization")
            
        # Try to authenticate the user
        user = authenticate(username=normalized_username, password=password)
        if user is None:
            raise serializers.ValidationError({
                "detail": "Invalid email ID or password"
            }, code="authorization")
            
        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "This account is inactive"
            }, code="authorization")
            
        data = {}
        refresh = self.get_token(user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)
            
        return data

