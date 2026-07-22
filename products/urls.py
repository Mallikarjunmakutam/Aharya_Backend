from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductImageViewSet, ReviewViewSet, ProductVariantViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'variants', ProductVariantViewSet, basename='product-variant')
router.register(r'images', ProductImageViewSet, basename='product-image')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
