from django.urls import path
from .views import InitializePaymentView

urlpatterns = [
    path("initialize/", InitializePaymentView.as_view(), name="initialize-payment"),
]
