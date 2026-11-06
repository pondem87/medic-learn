from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile, User


@admin.register(User)
class AccountAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "state", "is_staff")
    search_fields = ("email",)
    fieldsets = ((None, {"fields": ("email", "state", "is_staff", "is_superuser")}),)
    readonly_fields = ("email", "state", "is_staff", "is_superuser")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "validation")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
