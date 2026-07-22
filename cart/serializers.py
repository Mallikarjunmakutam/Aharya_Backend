from rest_framework import serializers
from .models import Cart, CartItem, Wishlist
from products.serializers import ProductListSerializer, ProductVariantSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 'quantity', 'total_price']

    def validate(self, attrs):
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')
        if not product_id and not variant_id:
            raise serializers.ValidationError("Either product_id or variant_id must be provided")
        return attrs

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'updated_at']
        read_only_fields = ['user']

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'created_at']
        read_only_fields = ['user']

