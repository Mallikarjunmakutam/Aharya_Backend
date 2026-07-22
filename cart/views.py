from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Cart, CartItem, Wishlist
from .serializers import CartSerializer, CartItemSerializer, WishlistSerializer
from products.models import Product

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        cart = self.get_object()
        variant_id = request.data.get('variant_id')
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        from products.models import Product, ProductVariant
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id)
                product = variant.product
            except ProductVariant.DoesNotExist:
                return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
        elif product_id:
            try:
                product = Product.objects.get(id=product_id)
                variant = product.variants.first()
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Product or Variant ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        
        cart_item.save()
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='update-quantity')
    def update_quantity(self, request):
        cart = self.get_object()
        variant_id = request.data.get('variant_id')
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            if variant_id:
                cart_item = CartItem.objects.get(cart=cart, variant_id=variant_id)
            else:
                cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not in cart'}, status=status.HTTP_404_NOT_FOUND)

        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request):
        cart = self.get_object()
        variant_id = request.data.get('variant_id')
        product_id = request.data.get('product_id')
        
        if variant_id:
            CartItem.objects.filter(cart=cart, variant_id=variant_id).delete()
        else:
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
            
        return Response(CartSerializer(cart, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='clear')
    def clear_cart(self, request):
        cart = self.get_object()
        cart.items.all().delete()
        return Response(CartSerializer(cart, context={'request': request}).data)

class WishlistViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_object(self):
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_product(self, request):
        wishlist = self.get_object()
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if product in wishlist.products.all():
            wishlist.products.remove(product)
            message = "Removed from wishlist"
        else:
            wishlist.products.add(product)
            message = "Added to wishlist"

        return Response({'message': message, 'wishlist': WishlistSerializer(wishlist, context={'request': request}).data})
