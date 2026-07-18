from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import MotardProfile, OwnerProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("phone_number",)
    list_display = ("phone_number", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_verified")
    search_fields = ("phone_number", "first_name", "last_name", "email")
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "email", "role")}),
        (
            "Statut",
            {"fields": ("is_active", "is_verified", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(MotardProfile)
class MotardProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "application_status", "subscription_status", "is_available", "rating_average")
    list_filter = ("application_status", "subscription_status", "is_available")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name")


@admin.register(OwnerProfile)
class OwnerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name")
    search_fields = ("user__phone_number", "company_name")
