# certificates/serializers.py
from rest_framework import serializers
from .models import Partner, Certificate, CertificateApplication, LicenseApplication
from .models import ClearanceApplication
from .models import BusinessCertificateApplication

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'


class CertificateSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.organization_name', read_only=True)
    status = serializers.ReadOnlyField()

    class Meta:
        model = Certificate
        fields = ['id', 'partner', 'partner_name', 'certificate_type', 'issued_date', 'expiry_date', 'status']


class CertificateApplicationSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    class Meta:
        model = CertificateApplication
        fields = '__all__'

class LicenseApplicationSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True) 
    application_date = serializers.SerializerMethodField()

    def get_application_date(self, obj):
        return obj.application_date if obj.application_date else None
    
    class Meta:
        model = LicenseApplication
        fields = '__all__'

class ClearanceApplicationSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    class Meta:
        model = ClearanceApplication
        fields = '__all__'

class BusinessCertificateApplicationSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)
    class Meta:
        model = BusinessCertificateApplication
        fields = '__all__'