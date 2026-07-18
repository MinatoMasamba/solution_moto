from django.contrib import admin

from .models import Ride, RideRating


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "motard", "status", "requested_at")
    list_filter = ("status",)
    search_fields = ("client__phone_number", "motard__phone_number", "pickup_address", "dropoff_address")


@admin.register(RideRating)
class RideRatingAdmin(admin.ModelAdmin):
    list_display = ("ride", "rated_by", "score", "created_at")
