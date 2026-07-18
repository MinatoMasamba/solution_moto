from django.contrib import admin

from .models import Agreement, FleetRemittance, MotardTrial, Motorcycle, TrialDailyLog


@admin.register(Motorcycle)
class MotorcycleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "ownership_type", "status", "owner", "fleet_manager", "assigned_motard")
    list_filter = ("ownership_type", "status")
    search_fields = (
        "plate_number", "owner__phone_number", "fleet_manager__phone_number", "assigned_motard__phone_number",
    )


@admin.register(FleetRemittance)
class FleetRemittanceAdmin(admin.ModelAdmin):
    list_display = ("motorcycle", "period_start", "period_end", "gross_revenue", "net_amount")


class TrialDailyLogInline(admin.TabularInline):
    model = TrialDailyLog
    extra = 0


@admin.register(MotardTrial)
class MotardTrialAdmin(admin.ModelAdmin):
    list_display = ("motard", "motorcycle", "start_date", "end_date", "result")
    list_filter = ("result",)
    search_fields = ("motard__phone_number", "motorcycle__plate_number")
    inlines = [TrialDailyLogInline]


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = (
        "motard", "motorcycle", "agreement_type", "frequency", "periodic_amount", "is_active",
    )
    list_filter = ("agreement_type", "frequency", "is_active")
    search_fields = ("motard__phone_number", "motorcycle__plate_number")
