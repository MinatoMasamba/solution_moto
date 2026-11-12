from django.contrib import admin

from .models import Payment, Subscription, WalletTransaction


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "amount", "status", "provider", "created_at")
    list_filter = ("kind", "status", "provider")
    search_fields = ("user__phone_number", "provider_reference", "label")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("motard", "amount", "status", "period_start", "period_end")
    list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "purpose", "provider", "amount", "status", "created_at")
    list_filter = ("purpose", "provider", "status")
    search_fields = ("user__phone_number", "provider_transaction_id")
