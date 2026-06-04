from django import forms
from .models import CertificateApplication

class CertificateApplicationForm(forms.ModelForm):
    class Meta:
        model = CertificateApplication
        fields = '__all__'
