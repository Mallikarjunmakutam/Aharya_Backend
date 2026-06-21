from django.contrib import admin
from .models import User, UserAddress

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'phone', 'is_staff', 'is_active', 'created_at']
    search_fields = ['email', 'full_name', 'phone']
    list_filter = ['is_staff', 'is_active', 'created_at']
    ordering = ['-created_at']

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'state', 'is_default']
    search_fields = ['user__email', 'full_name', 'city']
    list_filter = ['state', 'is_default']
