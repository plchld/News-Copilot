from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_premium', 'analysis_count', 'is_staff']
    list_filter = ['is_premium', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Premium Status', {'fields': ('is_premium', 'analysis_count')}),
    )
    search_fields = ['username', 'email']