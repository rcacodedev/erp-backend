from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email","is_staff","is_active","date_joined")
    fieldsets = (
        (None, {"fields": ("email","password")}),
        ("Personal info", {"fields": ("first_name","last_name")}),
        ("Permissions", {"fields": ("is_active","is_staff","is_superuser","groups","user_permissions")}),
        ("Important dates", {"fields": ("last_login","date_joined")}),
    )
    add_fieldsets = ((None, {"fields": ("email","password1","password2")}),)
    search_fields = ("email",)
