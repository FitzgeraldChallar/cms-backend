from django.db import models
from django.utils.timezone import now
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings  # For accessing DEFAULT_FROM_EMAIL
from django.dispatch import receiver
from datetime import timedelta
from django.db.models.signals import post_save
from django.apps import apps
from django.contrib.auth.models import User
import uuid


class ServiceType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    fee = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Partner(models.Model):
     
    organization_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.organization_name
 
class Certificate(models.Model):
    partner = models.CharField(max_length=255)
    certificate_type = models.CharField(max_length=255)
    issued_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Valid', 'Valid'), ('Expired', 'Expired')], default='Valid')

    class Meta:
        verbose_name = "WCC, WC, WL - Certificates"
        verbose_name_plural = "WCC, WC, WL - Certficates"


    def __str__(self):
        return f'{self.partner} - {self.certificate_type}'

    @property
    def status(self):
        return "Valid" if self.expiry_date >= now().date() else "Expired"
    
def default_expiry_date():
    return timezone.now().date() + timedelta(days=365)

class CertificateApplication(models.Model):
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="wash_applications",
        null=True,
        blank=True,
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    partner = models.CharField(max_length=255)
    address = models.TextField()
    last_certificate_expiry_date = models.DateField()
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    compliance_approved = models.BooleanField(default=False)
    ed_approved = models.BooleanField(default=False)
    ceo_approved = models.BooleanField(default=False)
    principal_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    email_address = models.EmailField()

    faith_based_school = models.CharField(max_length=50, choices=[
        ('University', 'University'),
        ('College', 'College'),
        ('Technical/Vocational', 'Technical/Vocational'),
        ('Secondary', 'Secondary'),
        ('Primary', 'Primary'),
        ('Early Childhood', 'Early Childhood'),
    ], blank=True, null=True)

    non_faith_based_school = models.CharField(max_length=50, choices=[
        ('University', 'University'),
        ('College', 'College'),
        ('Technical/Vocational', 'Technical/Vocational'),
        ('Secondary', 'Secondary'),
        ('Primary', 'Primary'),
        ('Early Childhood', 'Early Childhood'),
    ], blank=True, null=True)

    type_of_business_registration = models.CharField(max_length=50, choices=[
        ('Sole Proprietorship', 'Sole Proprietorship'),
        ('Partnership', 'Partnership'),
        ('Corporation', 'Corporation'),
    ])

    ownership = models.CharField(max_length=50, choices=[
        ('government', 'Government'),
        ('private', 'Private'),
        ('non governmental', 'Non Governmental'),
    ])

    financial_strength = models.CharField(max_length=20, choices=[
        ('strong', 'Strong'),
        ('medium', 'Medium'),
        ('little', 'Little'),
    ], blank=True, null=True)

    BANK_CHOICES = [
        ('IB', 'IB'),
        ('EcoBank', 'EcoBank'),
        ('GT Bank', 'GT Bank'),
        ('Afriland First Bank', 'Afriland First Bank'),
        ('LBDI Bank', 'LBDI Bank'),
        ('SIB Bank', 'SIB Bank'),
        ('Bloom Bank', 'Bloom Bank'),
        ('UBA Bank', 'UBA Bank'),
    ]

    name_of_banks = models.CharField(max_length=50, choices=BANK_CHOICES, blank=True, null=True)

    # Administrative Staff Information
    admin_staff_1_name = models.CharField(max_length=255)
    admin_staff_1_nationality = models.CharField(max_length=100)
    admin_staff_1_position = models.CharField(max_length=100)
    admin_staff_1_education = models.CharField(max_length=50, choices=[
        ('High School Graduate', 'High School Graduate'),
        ('Undergraduate', 'Undergraduate'),
        ('Postgraduate', 'Postgraduate'),
        ('PhD', 'PhD'),
    ])
    admin_staff_1_years_of_experience = models.IntegerField(default=0)
    admin_staff_1_cv = models.FileField(upload_to='certificates/admin_staff_1/cv/', blank=True, null=True)
    admin_staff_1_work_permit = models.FileField(upload_to='certificates/admin_staff_1/work_permit/', blank=True, null=True)

    admin_staff_2_name = models.CharField(max_length=255, blank=True, null=True)
    admin_staff_2_nationality = models.CharField(max_length=100, blank=True, null=True)
    admin_staff_2_position = models.CharField(max_length=100, blank=True, null=True)
    admin_staff_2_education = models.CharField(max_length=50, choices=[
        ('High School Graduate', 'High School Graduate'),
        ('Undergraduate', 'Undergraduate'),
        ('Postgraduate', 'Postgraduate'),
        ('PhD', 'PhD'),
    ], blank=True, null=True)
    admin_staff_2_years_of_experience = models.IntegerField(default=0)
    admin_staff_2_cv = models.FileField(upload_to='certificates/admin_staff_2/cv/', blank=True, null=True)
    admin_staff_2_work_permit = models.FileField(upload_to='certificates/admin_staff_2/work_permit/', blank=True, null=True)

    admin_staff_3_name = models.CharField(max_length=255, blank=True, null=True)
    admin_staff_3_nationality = models.CharField(max_length=100, blank=True, null=True)
    admin_staff_3_position = models.CharField(max_length=100, blank=True, null=True)
    admin_staff_3_education = models.CharField(max_length=50, choices=[
        ('High School Graduate', 'High School Graduate'),
        ('Undergraduate', 'Undergraduate'),
        ('Postgraduate', 'Postgraduate'),
        ('PhD', 'PhD'),
    ], blank=True, null=True)
    admin_staff_3_years_of_experience = models.IntegerField(default=0)
    admin_staff_3_cv = models.FileField(upload_to='certificates/admin_staff_3/cv/', blank=True, null=True)
    admin_staff_3_work_permit = models.FileField(upload_to='certificates/admin_staff_3/work_permit/', blank=True, null=True)

    # Documents Upload
    permit_from_moe = models.FileField(upload_to='certificates/documents/permit_from_moe/')
    business_registration = models.FileField(upload_to='certificates/documents/business_registration/')
    article_of_incorporation = models.FileField(upload_to='certificates/documents/article_of_incorporation/', blank=True, null=True)
    tax_clearance = models.FileField(upload_to='certificates/documents/tax_clearance/')
    sanitation_policy = models.FileField(upload_to='certificates/documents/sanitation_policy/', blank=True, null=True)
    letter_of_application = models.FileField(upload_to='certificates/documents/letter_of_application/', blank=True, null=True)
    information_sheet = models.FileField(upload_to='certificates/documents/information_sheet/')
    certificate_payment_receipt = models.FileField(upload_to='certificates/documents/certificate_payment_receipt/')

    # Water, Sanitary and Hygiene Facilities
    number_of_handwashing_facilities = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('one', 'One'),
        ('two', 'Two'), 
        ('three', 'Three'),
        ('more than three', 'More than Three'),
    ])
    number_of_gender_sensitive_latrines = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('one', 'One'),
        ('two', 'Two'),
        ('three', 'Three'),
        ('more than three', 'More than Three'), 
    ])
    source_of_water = models.CharField(max_length=50, choices=[
        ('hand-dug well', 'Hand-dug Well'),
        ('borehole', 'Borehole'),
        ('LWSC', 'LWSC'),  
        ('creek', 'Creek'), 
        ('other', 'Other'),
    ])
    specify_other_source = models.CharField(max_length=255, blank=True, null=True)
    number_of_drinking_water_facilities = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('one', 'One'),
        ('two', 'Two'),
        ('three', 'Three'),
        ('more than three', 'More than Three'), 
    ])
    METHOD_OF_PAYMENT_CHOICES = [
    ("mobile_money", "Mobile Money"),
    ("debit_credit_card", "Debit/Credit Card"),
    ("bank_deposit", "Direct Bank Deposit"),
    ]

    method_of_payment = models.CharField(
    max_length=50,
    choices=METHOD_OF_PAYMENT_CHOICES,
    default="mobile_money",
    verbose_name="How do you intend to proceed with required payments for this application?"
    )


    attestation = models.BooleanField(default=False)
    date_approved = models.DateTimeField(null=True, blank=True)
    generated_certificate = models.FileField(upload_to='certificates/', null=True, blank=True)
    certificate_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tin_number = models.CharField(max_length=30, blank=True, null=True)


    def __str__(self):
        return f"WASH-in-School Certificate - {self.partner}"

    @property
    def is_fully_approved(self):
        return self.compliance_approved and self.ed_approved and self.ceo_approved

    def send_notification(self, role):
        if role != "CEO":
            print(f"ℹ️ No email sent for {role} approval. Email will only be sent after CEO approval.")
            return

        subject = f"Certificate Application {role} Approval Notification" 
        message = (
            f"Dear {self.partner},\n\n"
            f"We’re pleased to inform you that your certificate application "
            f"for 'WASH-in-School Certificate' has been approved by the {role}.\n\n"
            f"Thank you for partnering with us.\n\n"
            f"Best regards,\nNWASHC Compliance Department"
        )
        recipient = self.get_contact_email() 
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False
            )
            print(f"✅ Email sent to {recipient} after {role} approval")
        except Exception as e:
            print(f"❌ Failed to send email to {recipient} after {role} approval: {e}")

    def get_contact_email(self):
        partner = Partner.objects.filter(organization_name=self.partner).first()
        return partner.email if partner else 'nwashccompliance@gmail.com'
    
    class Meta:
        verbose_name = "WASH-in-School Applications"
        verbose_name_plural = "WASH-in-School Applications"
    

class LicenseApplication(models.Model):

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="license_applications",
        null=True,
        blank=True, 
    )

    partner = models.CharField(max_length=255)
    address = models.TextField()
    contact = models.CharField(max_length=50)
    email_address = models.EmailField()
    sub_office_location_1 = models.CharField(max_length=255, blank=True)
    sub_office_location_2 = models.CharField(max_length=255, blank=True)
    sub_office_location_3 = models.CharField(max_length=255, blank=True)
    year_of_establishment = models.DateField()
    application_date = models.DateField(default=timezone.now)
    business_registration_type = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, blank=True, null=True)


    owner_name = models.CharField(max_length=255)
    owner_address = models.TextField()
    owner_phone = models.CharField(max_length=50)
    owner_email = models.EmailField()

    water_production_site = models.CharField(max_length=100)
    source_of_water = models.CharField(max_length=100)
    type_of_water_production = models.CharField(max_length=100)
    other_water_site = models.CharField(max_length=255, blank=True, null=True)
    other_water_source = models.CharField(max_length=255, blank=True, null=True)
    other_production_type = models.CharField(max_length=255, blank=True, null=True)

    financial_capacity = models.CharField(max_length=100)
    banks = models.CharField(max_length=255, blank=True, null=True)

    staff_name_1 = models.CharField(max_length=255)
    staff_nationality_1 = models.CharField(max_length=100)
    staff_position_1 = models.CharField(max_length=100)
    staff_education_1 = models.CharField(max_length=100)
    staff_experience_years_1 = models.PositiveIntegerField()
    staff_cv_1 = models.FileField(upload_to='license/cv/')
    staff_work_permit_1 = models.FileField(upload_to='license/work_permits/')

    staff_name_2 = models.CharField(max_length=255, blank=True, null=True)
    staff_nationality_2 = models.CharField(max_length=100, blank=True, null=True)
    staff_position_2 = models.CharField(max_length=100, blank=True, null=True)
    staff_education_2 = models.CharField(max_length=100, blank=True, null=True)
    staff_experience_years_2 = models.PositiveIntegerField(blank=True, null=True)
    staff_cv_2 = models.FileField(upload_to='license/cv/', blank=True, null=True)
    staff_work_permit_2 = models.FileField(upload_to='license/work_permits/', blank=True, null=True)

    staff_name_3 = models.CharField(max_length=255, blank=True, null=True)
    staff_nationality_3 = models.CharField(max_length=100, blank=True, null=True)
    staff_position_3 = models.CharField(max_length=100, blank=True, null=True)
    staff_education_3 = models.CharField(max_length=100, blank=True, null=True)
    staff_experience_years_3 = models.PositiveIntegerField(blank=True, null=True)
    staff_cv_3 = models.FileField(upload_to='license/cv/', blank=True, null=True)
    staff_work_permit_3 = models.FileField(upload_to='license/work_permits/', blank=True, null=True)

    environmental_license = models.FileField(upload_to='license/supporting_docs/', blank=True, null=True)
    water_quality_report = models.FileField(upload_to='license/supporting_docs/')
    business_registration = models.FileField(upload_to='license/supporting_docs/',)
    tax_clearance = models.FileField(upload_to='license/supporting_docs/')
    article_of_incorporation = models.FileField(upload_to='license/supporting_docs/', blank=True, null=True)
    letter_of_application = models.FileField(upload_to='license/supporting_docs/')
    lwsc_receipts = models.FileField(upload_to='license/supporting_docs/', blank=True, null=True)
    license_payment_receipt = models.FileField(upload_to='license/supporting_docs/')

    light_duty_vehicles = models.PositiveIntegerField()
    heavy_duty_vehicles = models.PositiveIntegerField()
    number_of_machines = models.PositiveIntegerField()

    attestation = models.BooleanField(default=False)
    submitted_at = models.DateField(auto_now_add=True)

    is_approved_by_compliance = models.BooleanField(default=False)
    compliance_approved_at = models.DateField(null=True, blank=True)

    is_approved_by_ed = models.BooleanField(default=False)
    ed_approved_at = models.DateField(null=True, blank=True)

    is_approved_by_ceo = models.BooleanField(default=False)
    ceo_approved_at = models.DateField(null=True, blank=True)
    generated_license = models.FileField(upload_to='certificates/', null=True, blank=True)
    certificate_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tin_number = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = "License Applications"
        verbose_name_plural = "License Applications"

    def is_fully_approved(self):
        return self.is_approved_by_compliance and self.is_approved_by_ed and self.is_approved_by_ceo
    
    def __str__(self):
        return f"License Application - {self.partner}"
    
    def save(self, *args, **kwargs):
        # assign category before saving
        self.category = self.assign_category()
        super().save(*args, **kwargs)

    def assign_category(self):
        if self.amount_paid >= 650:
            return "Category A"
        elif 450 <= self.amount_paid <= 649:
            return "Category B"
        elif 350 <= self.amount_paid <= 449:
            return "Category C"
        elif 150 <= self.amount_paid <= 349:
            return "Category D"
        return "Uncategorized"


class ClearanceApplication(models.Model):

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="clearance_applications",
        null=True, 
        blank=True,
    )

    # General Information
    partner = models.CharField(max_length=255)
    head_office_address = models.TextField()
    sub_office_addresses = models.TextField(null=True, blank=True)
    executive_director_name = models.CharField(max_length=255)
    telephone_number = models.CharField(max_length=50)
    email = models.EmailField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, blank=True, null=True)


    # WATSAN Construction Experiences
    project1_name = models.CharField(max_length=255, blank=True, null=True,)
    project1_funding_source = models.CharField(max_length=255, blank=True, null=True)
    project1_implementation_period = models.CharField(max_length=100, blank=True, null=True)
    project1_status = models.CharField(max_length=100, blank=True, null=True)

    project2_name = models.CharField(max_length=255, blank=True, null=True)
    project2_funding_source = models.CharField(max_length=255, blank=True, null=True)
    project2_implementation_period = models.CharField(max_length=100, blank=True, null=True)
    project2_status = models.CharField(max_length=100, blank=True, null=True)

    project3_name = models.CharField(max_length=255, blank=True, null=True)
    project3_funding_source = models.CharField(max_length=255, blank=True, null=True)
    project3_implementation_period = models.CharField(max_length=100, blank=True, null=True)
    project3_status = models.CharField(max_length=100, blank=True, null=True)

    project4_name = models.CharField(max_length=255, blank=True, null=True)
    project4_funding_source = models.CharField(max_length=255, blank=True, null=True)
    project4_implementation_period = models.CharField(max_length=100, blank=True, null=True)
    project4_status = models.CharField(max_length=100, blank=True, null=True)

    # Lessons and Challenges
    lessons_and_difficulties = models.TextField()

    # Technical Staff
    staff1_name = models.CharField(max_length=255)
    staff1_nationality = models.CharField(max_length=100)
    staff1_position = models.CharField(max_length=100)
    staff1_education_experience = models.CharField(max_length=255)
    staff1_cv = models.FileField(upload_to='clearance/cv/')

    staff2_name = models.CharField(max_length=255)
    staff2_nationality = models.CharField(max_length=100)
    staff2_position = models.CharField(max_length=100)
    staff2_education_experience = models.CharField(max_length=255)
    staff2_cv = models.FileField(upload_to='clearance/cv/')

    # Supporting Documents
    approved_wash_workplan = models.FileField(upload_to='clearance/supporting_docs/', blank=True, null=True)
    letter_of_application = models.FileField(upload_to='clearance/supporting_docs/')
    business_registration_and_tax_clearance = models.FileField(upload_to='clearance/supporting_docs/')
    clearance_payment_receipt = models.FileField(upload_to='clearance/supporting_docs/')
    organization_profile = models.FileField(upload_to='clearance/supporting_docs/', blank=True, null=True)
    previous_year_activities_report = models.FileField(upload_to='clearance/supporting_docs/')

    # Equipment / Tools
    light_vehicles = models.PositiveIntegerField(null=True, blank=True)
    pickups_4wd = models.PositiveIntegerField(null=True, blank=True)
    rig_compressor = models.PositiveIntegerField(null=True, blank=True)
    tripod = models.PositiveIntegerField(null=True, blank=True)
    culvert_mould = models.PositiveIntegerField(null=True, blank=True)
    size_0_90m = models.PositiveIntegerField(null=True, blank=True)
    size_0_76m = models.PositiveIntegerField(null=True, blank=True)
    chain_block = models.PositiveIntegerField(null=True, blank=True)
    pulley = models.PositiveIntegerField(null=True, blank=True)
    casting_yard = models.PositiveIntegerField(null=True, blank=True)
    additional_equipment = models.TextField(null=True, blank=True)

    # Final Confirmation
    attestation = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    
    compliance_director_approved = models.BooleanField(default=False)
    ed_approved = models.BooleanField(default=False)
    ceo_approved = models.BooleanField(default=False)
    generated_clearance = models.FileField(upload_to='certificates/', null=True, blank=True)
    certificate_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tin_number = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = "Clearance Applications"
        verbose_name_plural = "Clearance Applications"
    
    def __str__(self):
        return f"Clearance Application - {self.partner}"
    
    def save(self, *args, **kwargs):
        # assign category before saving
        self.category = self.assign_category()
        super().save(*args, **kwargs)

    def assign_category(self):
        if self.amount_paid >= 650:
            return "Category A"
        elif 450 <= self.amount_paid <= 649:
            return "Category B"
        elif 350 <= self.amount_paid <= 449:
            return "Category C"
        elif 150 <= self.amount_paid <= 349:
            return "Category D"
        return "Uncategorized"
    
class BusinessCertificateApplication(models.Model):
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="business_certificate_applications",
        null=True,
        blank=True,
    )
    BUSINESS_TYPE_CHOICES = [
        ('Water Processing Company', 'Water Processing Company'),
        ('Eatery/Restaurant', 'Eatery/Restaurant'),
        ('Food Processing Plants', 'Food Processing Plants'),
        ('Chemical Store', 'Chemical Store'),
        ('Vector Control Institution', 'Vector Control Institution'),
        ('Health Care Waste Handling Company', 'Health Care Waste Handling Company'),
        ('Occupational Health and Safety Institution', 'Occupational Health and Safety Institution'),
        ('Banks and other financial Institutions', 'Banks and other financial Institutions'),
        ('Health Care Institutions', 'Health Care Institutions'),
        ('Cinema/Video Club', 'Cinema/Video Club'),
        ('Factory/Concession Area', 'Factory/Concession Area'),
        ('Shop', 'Shop'),
        ('Store', 'Store'),
        ('Supermarket', 'Supermarket'),
        ('Hotel', 'Hotel'),
        ('Motel', 'Motel'),
        ('Guest House', 'Guest House'),
        ('University/College', 'University/College'),
        ('Cold Storage', 'Cold Storage'),
        ('Other', 'Other'),
    ]

    partner = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=50)  
    email = models.EmailField()
    type_of_business = models.CharField(max_length=100, choices=BUSINESS_TYPE_CHOICES)
    other_business_type = models.CharField(max_length=255, blank=True, null=True)

    name_of_business_owner = models.CharField(max_length=255)
    address_of_business_owner = models.TextField()
    contact_no_of_business_owner = models.CharField(max_length=50)
    email_of_business_owner = models.EmailField()

    # TECHNICAL STAFF SECTION
    name_of_staff_1 = models.CharField(max_length=255)  
    nationality_of_staff_1 = models.CharField(max_length=100)
    position_of_staff_1 = models.CharField(max_length=100)  
    education_experience_of_staff_1 = models.TextField()
    cv_of_staff_1 = models.FileField(upload_to='business_certificates/cvs/', null=True, blank=True)   

    name_of_staff_2 = models.CharField(max_length=255, blank=True, null=True)
    nationality_of_staff_2 = models.CharField(max_length=100, blank=True, null=True)
    position_of_staff_2 = models.CharField(max_length=100, blank=True, null=True)
    education_experience_of_staff_2 = models.TextField(blank=True, null=True)
    cv_of_staff_2 = models.FileField(upload_to='business_certificates/cvs/', null=True, blank=True)

    name_of_staff_3 = models.CharField(max_length=255, blank=True, null=True)
    nationality_of_staff_3 = models.CharField(max_length=100, blank=True, null=True)
    position_of_staff_3 = models.CharField(max_length=100, blank=True, null=True)
    education_experience_of_staff_3 = models.TextField(blank=True, null=True)
    cv_of_staff_3 = models.FileField(upload_to='business_certificates/cvs/', null=True, blank=True)


    # SUPPORTING DOCUMENTS SECTION
    letter_of_application = models.FileField(upload_to='business_certificates/docs/', null=True, blank=True)
    business_registration_document = models.FileField(upload_to='business_certificates/docs/')
    article_of_incorporation = models.FileField(upload_to='business_certificates/docs/', null=True, blank=True)
    tax_clearance = models.FileField(upload_to='business_certificates/docs/')
    sanitation_waste_plan = models.FileField(upload_to='business_certificates/docs/', null=True, blank=True)
    b_certificate_payment_receipt = models.FileField(upload_to='business_certificates/docs/')

    # ATTESTATION
    attestation = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)
    certificate_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tin_number = models.CharField(max_length=30, blank=True, null=True)

    compliance_director_approved = models.BooleanField(default=False)
    ed_approved = models.BooleanField(default=False)
    ceo_approved = models.BooleanField(default=False)
    generated_business_certificate = models.FileField(upload_to='certificates/', null=True, blank=True)

    class Meta:
        verbose_name = "Business Certificate Applications"
        verbose_name_plural = "Business Certificate Applications"

    def __str__(self):
        return f"Business Certificate - {self.partner}"
    






    