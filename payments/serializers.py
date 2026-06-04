from rest_framework import serializers
from .models import Payment
from certificates.models import ServiceType


class PaymentInitSerializer(serializers.Serializer):
    service_type_code = serializers.CharField()
    application_id = serializers.IntegerField()
    application_model = serializers.CharField(max_length=100)

    def validate_service_type_code(self, value):
        try:
            return ServiceType.objects.get(code=value)
        except ServiceType.DoesNotExist:
            raise serializers.ValidationError("Invalid service type code")

    def create(self, validated_data):
        service_type = validated_data["service_type_code"]

        payment = Payment.objects.create(
            service_type=service_type,
            application_id=validated_data["application_id"],
            application_model=validated_data["application_model"],
            amount=service_type.fee,
            status="PENDING",
        )

        return payment
