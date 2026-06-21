from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'price', 'quantity']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'payment_status', 'order_status', 'created_at']
    list_filter = ['payment_status', 'order_status', 'created_at', 'payment_method']
    search_fields = ['id', 'user__email', 'shipping_full_name']
    readonly_fields = ['id', 'user', 'subtotal', 'shipping_charge', 'tax', 'total_amount', 'razorpay_order_id', 'razorpay_payment_id']
    inlines = [OrderItemInline]
    list_editable = ['order_status']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('id', 'user', 'order_status', 'created_at')
        }),
        ('Payment Info', {
            'fields': ('payment_status', 'payment_method', 'razorpay_order_id', 'razorpay_payment_id', 'subtotal', 'shipping_charge', 'tax', 'total_amount')
        }),
        ('Shipping Address', {
            'fields': ('shipping_full_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code')
        }),
    )
