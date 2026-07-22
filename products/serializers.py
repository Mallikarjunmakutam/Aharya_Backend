from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductImage, Review
from .cloudinary_utils import upload_product_image, delete_cloudinary_image


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'variant', 'product', 'image', 'is_main', 'alt_text']
        read_only_fields = ['image']

    def create(self, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if not image_file:
            raise serializers.ValidationError({'image': 'An image file is required.'})

        variant = validated_data.get('variant')
        product = validated_data.get('product')
        product_id = variant.product.id if variant else (product.id if product else 'default')
        
        try:
            validated_data['image'] = upload_product_image(image_file, str(product_id))
        except ValueError as exc:
            raise serializers.ValidationError({'image': str(exc)}) from exc

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        image_file = request.FILES.get('image') if request else None
        if image_file:
            delete_cloudinary_image(instance.image)
            variant = validated_data.get('variant') or instance.variant
            product_id = variant.product_id if variant else (instance.product_id or 'default')
            try:
                validated_data['image'] = upload_product_image(image_file, str(product_id))
            except ValueError as exc:
                raise serializers.ValidationError({'image': str(exc)}) from exc

        return super().update(instance, validated_data)


class ProductVariantSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'color_name', 'color_code', 'price', 'discount_price', 'stock', 'sku', 'images', 'created_at', 'updated_at']
        read_only_fields = ['product']


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
            'rating', 'total_reviews', 'is_featured', 'main_image', 'item_code',
            'fabric', 'stock', 'is_active'
        ]

    def get_main_image(self, obj):
        image = ProductImage.objects.filter(variant__product=obj, is_main=True).first()
        if not image:
            image = ProductImage.objects.filter(variant__product=obj).first()
        return image.image if image else None


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )
    variants = ProductVariantSerializer(many=True, required=False)
    images = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    has_purchased = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_images(self, obj):
        images = ProductImage.objects.filter(variant__product=obj)
        return ProductImageSerializer(images, many=True, context=self.context).data

    def get_has_purchased(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            order__user=request.user,
            product=obj
        ).exclude(order__order_status='Cancelled').exists()

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data)
        for var_data in variants_data:
            ProductVariant.objects.create(product=product, **var_data)
        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        keep_variants = []
        for var_data in variants_data:
            var_id = var_data.get('id')
            if var_id:
                try:
                    variant = ProductVariant.objects.get(id=var_id, product=instance)
                    for attr, value in var_data.items():
                        if attr != 'id':
                            setattr(variant, attr, value)
                    variant.save()
                    keep_variants.append(variant.id)
                except ProductVariant.DoesNotExist:
                    pass
            else:
                variant = ProductVariant.objects.create(product=instance, **var_data)
                keep_variants.append(variant.id)
                
        if variants_data:
            instance.variants.exclude(id__in=keep_variants).delete()

        return instance

