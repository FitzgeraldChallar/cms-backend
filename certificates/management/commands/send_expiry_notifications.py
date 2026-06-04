from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from certificates.models import Certificate

class Command(BaseCommand):
    help = 'Send email notifications for certificates expiring in 30 days'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        target_date = today + timedelta(days=30)

        certificates = Certificate.objects.filter(expiry_date=target_date)

        if not certificates.exists():
            self.stdout.write("No certificates expiring in 30 days.")
            return

        for cert in certificates:
            partner = cert.partner
            recipient_email = partner.email

            if recipient_email:
                subject = 'Your Certificate is Expiring Soon'
                message = (
                    f"Dear {partner.organization_name},\n\n"
                    f"Your certificate '{cert.certificate_type}' will expire on {cert.expiry_date}.\n"
                    "Please renew it soon to avoid service disruption.\n\n"
                    "Best,\nNWASHC Compliance Department"
                )
                send_mail(
                    subject,
                    message,
                    'no-reply@yourdomain.com',
                    [recipient_email],
                    fail_silently=False,
                )
                self.stdout.write(f"Notification sent to {recipient_email}")
            else:
                self.stdout.write(f"No email for partner {partner.organization_name}")

