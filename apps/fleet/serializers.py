from rest_framework import serializers

from .models import Agreement, FleetRemittance, MotardTrial, Motorcycle, TrialDailyLog


class MotorcycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motorcycle
        fields = [
            "id", "owner", "fleet_manager", "ownership_type", "plate_number", "device_id",
            "brand", "model_style", "acquisition_date", "chassis_number", "color",
            "general_condition", "status", "assigned_motard", "commission_rate", "created_at",
        ]
        read_only_fields = ["id", "status", "assigned_motard", "fleet_manager", "created_at"]


class FleetRemittanceSerializer(serializers.ModelSerializer):
    plate_number = serializers.CharField(source="motorcycle.plate_number", read_only=True)
    motard_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = FleetRemittance
        fields = [
            "id", "motorcycle", "plate_number", "motard_name", "owner_name",
            "period_start", "period_end",
            "gross_revenue", "commission_amount", "net_amount", "created_at",
        ]
        read_only_fields = ["id", "commission_amount", "net_amount", "created_at"]

    def get_motard_name(self, obj):
        m = obj.motorcycle.assigned_motard
        return (m.get_full_name() or m.phone_number) if m else None

    def get_owner_name(self, obj):
        o = obj.motorcycle.owner
        return (o.get_full_name() or o.phone_number) if o else None


class MotardTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotardTrial
        fields = [
            "id", "motard", "motorcycle", "start_date", "end_date",
            "min_rides_required", "min_rating_required", "result", "final_notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TrialDailyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrialDailyLog
        fields = [
            "id", "trial", "date", "return_time", "amount_paid", "is_payment_complete",
            "motard_explanation", "bike_condition_score", "manager_notes",
        ]
        read_only_fields = ["id"]


class AgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agreement
        fields = [
            "id", "motard", "motorcycle", "agreement_type", "frequency", "periodic_amount",
            "target_total_amount", "amount_already_paid", "start_date", "end_date",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "amount_already_paid", "created_at"]
