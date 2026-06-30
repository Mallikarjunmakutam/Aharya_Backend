from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart
import uuid

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        if self.request.user and self.request.user.is_staff:
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'detail': 'Only staff can update orders.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # This will be called after Razorpay order creation usually
        # or as a direct 'place order' if it's COD
        user = request.user
        
        # Check if this is a Buy Now flow
        buy_now_product_id = request.data.get('buy_now_product_id')
        buy_now_qty = request.data.get('buy_now_qty')

        if buy_now_product_id:
            from products.models import Product
            try:
                product = Product.objects.get(id=buy_now_product_id)
            except (ValueError, Product.DoesNotExist):
                # Try lookup by slug as well
                try:
                    product = Product.objects.get(slug=buy_now_product_id)
                except Product.DoesNotExist:
                    return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            
            qty = int(buy_now_qty or 1)
            price = product.discount_price if (product.discount_price and product.discount_price > 0) else product.price
            subtotal = price * qty
        else:
            cart, created = Cart.objects.get_or_create(user=user)
            if not cart.items.exists():
                return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
            subtotal = cart.total_price

        # Basic verification of shipping info
        shipping_data = request.data.get('shipping_info')
        if not shipping_data:
            return Response({'error': 'Shipping info required'}, status=status.HTTP_400_BAD_REQUEST)

        order_id = str(uuid.uuid4()) # Placeholder, usually updated with Razorpay ID later
        
        shipping_charge = 0 # Can be calculated
        tax = 0 # Can be calculated
        total_amount = subtotal + shipping_charge + tax

        order = Order.objects.create(
            id=order_id,
            user=user,
            shipping_full_name=shipping_data.get('full_name'),
            shipping_phone=shipping_data.get('phone'),
            shipping_address=shipping_data.get('address'),
            shipping_city=shipping_data.get('city'),
            shipping_state=shipping_data.get('state'),
            shipping_postal_code=shipping_data.get('postal_code'),
            subtotal=subtotal,
            shipping_charge=shipping_charge,
            tax=tax,
            total_amount=total_amount,
            payment_method=request.data.get('payment_method', 'Razorpay')
        )

        if buy_now_product_id:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                price=price,
                quantity=qty
            )
        else:
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.discount_price if (item.product.discount_price and item.product.discount_price > 0) else item.product.price,
                    quantity=item.quantity
                )

        # Clear cart after order creation (or wait for payment success?)
        # For now, let's clear it assuming we're initiating checkout
        # cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
