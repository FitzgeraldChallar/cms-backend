# certificates/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ClearanceApplication
from .serializers import ClearanceApplicationSerializer
from .models import BusinessCertificateApplication
from .serializers import BusinessCertificateApplicationSerializer
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication

from .models import Partner, Certificate, CertificateApplication, LicenseApplication
from .serializers import (
    PartnerSerializer,
    CertificateSerializer,
    CertificateApplicationSerializer,
    LicenseApplicationSerializer
)


class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer

    def create(self, request, *args, **kwargs):
        required_fields = ['organization_name', 'contact_person', 'email', 'phone', 'address']
        missing_fields = [field for field in required_fields if field not in request.data]

        if missing_fields:
            return Response(
                {"error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Registration successful!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer


class CertificateApplicationViewSet(viewsets.ModelViewSet):
    queryset = CertificateApplication.objects.all()
    serializer_class = CertificateApplicationSerializer
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save()


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_data = {
            "compliance_approved": instance.compliance_approved,
            "ed_approved": instance.ed_approved,
            "ceo_approved": instance.ceo_approved,
        }

        response = super().update(request, *args, **kwargs)
        instance.refresh_from_db()

        if not old_data["compliance_approved"] and instance.compliance_approved:
            instance.send_notification("Compliance Director")
        if not old_data["ed_approved"] and instance.ed_approved:
            instance.send_notification("Executive Director")
        if not old_data["ceo_approved"] and instance.ceo_approved:
            instance.send_notification("CEO")

        if instance.compliance_approved and instance.ed_approved and instance.ceo_approved:
            instance.status = 'Approved'
            instance.save()

        return response
    


class LicenseApplicationViewSet(viewsets.ModelViewSet):
    queryset = LicenseApplication.objects.all()
    serializer_class = LicenseApplicationSerializer
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
           print("Validation Errors:", serializer.errors)
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

class ClearanceApplicationViewSet(viewsets.ModelViewSet):
    queryset = ClearanceApplication.objects.all().order_by('-submitted_at')
    serializer_class = ClearanceApplicationSerializer
    parser_classes = [MultiPartParser, FormParser]
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Validation Errors:", serializer.errors)  
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BusinessCertificateApplicationViewSet(viewsets.ModelViewSet):
    queryset = BusinessCertificateApplication.objects.all()
    serializer_class = BusinessCertificateApplicationSerializer

    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    

