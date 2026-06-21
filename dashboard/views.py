from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order
from django.db.models import Sum

User = get_user_model()

class AdminDashboardStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'total_products': Product.objects.count(),
            'total_orders': Order.objects.count(),
            'total_sales': Order.objects.filter(payment_status='Paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'pending_orders': Order.objects.filter(order_status='Pending').count(),
            'low_stock_products': Product.objects.filter(stock__lt=5).count(),
        }
        return Response(stats)
