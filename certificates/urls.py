# certificates/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    PartnerViewSet,
    CertificateViewSet,
    CertificateApplicationViewSet,
    LicenseApplicationViewSet,
    ClearanceApplicationViewSet,
    BusinessCertificateApplicationViewSet
)

router = DefaultRouter()
router.register(r'partners', PartnerViewSet)
router.register(r'certificates', CertificateViewSet)
router.register(r'applications', CertificateApplicationViewSet)  # maps to /api/applications/
router.register(r'license-applications', LicenseApplicationViewSet)  # maps to /api/license-applications/
router.register(r'clearance-applications', ClearanceApplicationViewSet)
router.register(r'business-certificate-applications', BusinessCertificateApplicationViewSet, basename='business-certificate-applications')


urlpatterns = [
    path('', include(router.urls)),
]



