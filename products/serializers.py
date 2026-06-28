from rest_framework import serializers
from .models import Category, Product, ProductImage, Review
from .cloudinary_utils import upload_product_image, delete_cloudinary_image


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'is_main', 'alt_text']
        read_only_fields = ['image']

    def create(self, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if not image_file:
            raise serializers.ValidationError({'image': 'An image file is required.'})

        product = validated_data['product']
        try:
            validated_data['image'] = upload_product_image(image_file, str(product.id))
        except ValueError as exc:
            raise serializers.ValidationError({'image': str(exc)}) from exc

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if image_file:
            delete_cloudinary_image(instance.image)
            try:
                validated_data['image'] = upload_product_image(
                    image_file, str(instance.product_id)
                )
            except ValueError as exc:
                raise serializers.ValidationError({'image': str(exc)}) from exc

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
        return image.image if image else None


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
