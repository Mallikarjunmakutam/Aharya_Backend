import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from orders.models import Order
from cart.models import Cart

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class CreateRazorpayOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        # Amount in paise (1 INR = 100 paise)
        amount = int(order.total_amount * 100)
        
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": order.id,
        }

        try:
            razorpay_order = client.order.create(data=data)
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            
            response_data = dict(razorpay_order)
            response_data['key_id'] = settings.RAZORPAY_KEY_ID
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order_id = request.data.get('order_id')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            # Verify signature (allow mock verification in DEBUG mode)
            if settings.DEBUG and razorpay_signature and str(razorpay_signature).startswith('sig_mock_'):
                pass
            else:
                client.utility.verify_payment_signature(params_dict)
            
            # Update order
            order = None
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    pass
            
            if not order:
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)

            order.payment_status = 'Paid'
            order.razorpay_payment_id = razorpay_payment_id
            if not order.razorpay_order_id:
                order.razorpay_order_id = razorpay_order_id
            order.order_status = 'Paid'
            order.save()
            
            # Clear user cart on success
            clear_cart = request.data.get('clear_cart', True)
            if clear_cart:
                Cart.objects.filter(user=order.user).first().items.all().delete()

            return Response({'message': 'Payment successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
