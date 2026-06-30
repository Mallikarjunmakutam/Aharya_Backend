from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, GoogleLoginView, AddressViewSet, AdminUserViewSet, CustomTokenObtainPairView

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'admin-users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('google-auth/', GoogleLoginView.as_view(), name='google_auth'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('', include(router.urls)),
]
