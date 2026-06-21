from rest_framework import serializers
from .models import Category, Product, ProductImage, Review

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    image_file = serializers.ImageField(write_only=True, required=False, source='image')
    image_url = serializers.URLField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'image_file', 'image_url', 'is_main', 'alt_text']

    def get_image(self, obj):
        if not obj.image:
            return None
        img_val = str(obj.image)
        if img_val.startswith('http://') or img_val.startswith('https://'):
            return img_val
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def create(self, validated_data):
        image_url = validated_data.pop('image_url', None)
        if image_url:
            validated_data['image'] = image_url
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_url = validated_data.pop('image_url', None)
        if image_url:
            validated_data['image'] = image_url
        return super().update(instance, validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'price', 'discount_price', 
            'rating', 'total_reviews', 'is_featured', 'main_image', 'item_code'
        ]

    def get_main_image(self, obj):
        image = obj.images.filter(is_main=True).first()
        if not image:
            image = obj.images.first()
        if image:
            img_val = str(image.image)
            if img_val.startswith('http://') or img_val.startswith('https://'):
                return img_val
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
