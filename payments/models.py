from django.db import models
import uuid
from certificates.models import ServiceType

class Payment(models.Model):
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)

    application_id = models.PositiveIntegerField()
    application_model = models.CharField(max_length=100)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
        ],
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_type.name} - {self.reference}"
