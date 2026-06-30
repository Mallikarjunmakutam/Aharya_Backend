from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductImage, Review
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer, ProductImageSerializer, ReviewSerializer
)
from .cloudinary_utils import delete_cloudinary_image
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'category__name', 'is_featured', 'fabric']
    search_fields = ['name', 'description', 'item_code']
    ordering_fields = ['price', 'created_at', 'rating']
    
    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return Product.objects.all()
        return Product.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ProductDetailSerializer
        return ProductListSerializer

    def get_object(self):
        # Allow lookup by slug or UUID
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        try:
            return Product.objects.get(id=lookup_value)
        except Exception:
            return Product.objects.get(slug=lookup_value)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = self.queryset.filter(is_featured=True)[:8]
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
        serializer = self.get_serializer(latest_products, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        is_main = serializer.validated_data.get('is_main', False)
        product = serializer.validated_data.get('product')
        if is_main and product:
            ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)
        serializer.save()

    def perform_update(self, serializer):
        is_main = serializer.validated_data.get('is_main', False)
        product = serializer.validated_data.get('product')
        if is_main and product:
            ProductImage.objects.filter(product=product, is_main=True).update(is_main=False)
        serializer.save()

    def perform_destroy(self, instance):
        delete_cloudinary_image(instance.image)
        instance.delete()


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        review = serializer.save()
        product = review.product
        
        # Calculate new average rating & count
        reviews = product.reviews.all()
        total_reviews = reviews.count()
        avg_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0.0
        
        product.rating = round(avg_rating, 2)
        product.total_reviews = total_reviews
        product.save()

