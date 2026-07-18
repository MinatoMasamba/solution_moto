from django.contrib import admin

from .models import Payment, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("motard", "amount", "status", "period_start", "period_end")
    list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "provider", "amount", "status", "created_at")
    list_filter = ("purpose", "provider", "status")
    search_fields = ("user__phone_number", "provider_transaction_id")
