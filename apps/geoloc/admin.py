from django.contrib import admin

from .models import LocationPing


@admin.register(LocationPing)
class LocationPingAdmin(admin.ModelAdmin):
    list_display = ("user", "latitude", "longitude", "recorded_at")
    list_filter = ("recorded_at",)
    search_fields = ("user__phone_number",)
