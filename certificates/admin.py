from django.contrib import admin, messages
from django import forms
from .forms import CertificateApplicationForm
from .models import Partner, Certificate, CertificateApplication, LicenseApplication
from django.utils import timezone
from .models import ClearanceApplication, ServiceType
from .models import BusinessCertificateApplication
from django.utils.html import format_html
from .certificate_generator import generate_certificate
from .license_generator import generate_license
from .clearance_generator import generate_clearance
from .business_cert_generator import generate_business_cert


admin.site.site_url = 'https://certificate-cms-frontend.onrender.com/'
admin.site.site_header = "NWASHC CMS Administration"
admin.site.site_title = "NWASHC CMS Admin Interfaces"
admin.site.index_title = "Welcome to NWASHC Certificate Management System"

# Register ServiceType so it shows in admin
@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'fee')
    search_fields = ('code', 'name')


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization_name', 'contact_person', 'email', 'phone', 'address', 'date_created')
    ordering = ('-date_created',)
    search_fields = ('organization_name', 'contact_person', 'email')
    list_filter = ('date_created',)
    readonly_fields = ('date_created',)

    fieldsets = (
        (None, {
            'fields': ('organization_name', 'contact_person', 'email', 'phone', 'address')
        }),
    )

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['id', 'partner', 'certificate_type', 'issued_date', 'expiry_date']
    search_fields = ('partner','certificate_type')

@admin.register(LicenseApplication)
class LicenseApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'partner', 'contact', 'email_address','application_date',
        'is_approved_by_compliance', 'is_approved_by_ed', 'is_approved_by_ceo','license_link',
    )

    read_fields = ('entity_name', 'email_address', 'submitted_at')
    search_fields = ('partner', 'email_address')

    def license_link(self, obj):
        if obj.generated_license:
            return format_html(
                '<a href="{}" target="_blank">View License</a>', obj.generated_license.url
            )
        return "Link not available"
    license_link.short_description = "License"
    
    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name='CEO').exists():
            return [(None, {'fields': ['is_approved_by_ceo']})]
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.groups.filter(name='CEO').exists():
            return self.readonly_fields + ['is_approved_by_ceo']
        return self.readonly_fields

    def get_readonly_fields(self, request, obj=None):
        readonly = ['entity_name', 'email_address', 'submitted_at']
        user_groups = request.user.groups.values_list('name', flat=True)

        if 'Compliance Director' not in user_groups:
            readonly.append('is_approved_by_compliance')
        if 'Executive Director' not in user_groups or not (obj and obj.is_approved_by_compliance):
            readonly.append('is_approved_by_ed')
        if 'CEO' not in user_groups or not (obj and obj.is_approved_by_ed):
            readonly.append('is_approved_by_ceo')

        return readonly

    def get_fields(self, request, obj=None):
        # Get all model fields excluding 'id'
        fields = [
            field.name for field in self.model._meta.fields
            if field.name != 'id'
        ]

        # Add M2M fields if any
        fields += [f.name for f in self.model._meta.many_to_many]

        # Add approval fields only if user is allowed
        user_groups = request.user.groups.values_list('name', flat=True)

        if 'Compliance Director' not in user_groups and 'is_approved_by_compliance' in fields:
            fields.remove('is_approved_by_compliance')
        if ('Executive Director' not in user_groups or not (obj and obj.is_approved_by_compliance)) and 'is_approved_by_ed' in fields:
            fields.remove('is_approved_by_ed')
        if ('CEO' not in user_groups or not (obj and obj.is_approved_by_ed)) and 'is_approved_by_ceo' in fields:
            fields.remove('is_approved_by_ceo')

        return fields

    def approve_by_compliance(self, request, queryset):
        for obj in queryset:
            obj.is_approved_by_compliance = True
            obj.compliance_approved_at = timezone.now()
            obj.save()
        self.message_user(request, "Selected applications approved by Compliance.")

    def approve_by_ed(self, request, queryset):
        for obj in queryset:
            if obj.is_approved_by_compliance:
                obj.is_approved_by_ed = True
                obj.ed_approved_at = timezone.now()
                obj.save()
            else:
                self.message_user(
                    request,
                    f"ED cannot approve '{obj.entity_name}' because Compliance has not approved.",
                    level=messages.WARNING
                )

    def approve_by_ceo(self, request, queryset):
        for obj in queryset:
            if obj.is_approved_by_ed:
                obj.is_approved_by_ceo = True
                obj.ceo_approved_at = timezone.now()
                obj.save()

            try:
                obj.send_ceo_approval_notification()
                self.message_user(
                    request,
                    f"'{obj.entity_name}' approved by CEO and email sent.",
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"CEO approved '{obj.entity_name}', but email failed: {e}",
                    level=messages.ERROR
                )
        else:
            self.message_user(
                request,
                f"CEO cannot approve '{obj.entity_name}' because ED has not approved.",
                level=messages.WARNING
            )

    def save_model(self, request, obj, form, change):
        user_groups = list(request.user.groups.values_list('name', flat=True))
        changed_fields = form.changed_data

         # Generate certificate only once
        if obj.is_approved_by_ceo and not obj.generated_license:
           from certificates.license_generator import generate_license
           generate_license(obj)

        super().save_model(request, obj, form, change)


    approve_by_compliance.short_description = "Approve selected by Compliance"
    approve_by_ed.short_description = "Approve selected by Executive Director"
    approve_by_ceo.short_description = "Approve selected by CEO"

    
@admin.register(CertificateApplication)
class CertificateApplicationAdmin(admin.ModelAdmin):
    form = CertificateApplicationForm

    list_display = ['id', 'partner', 'application_date', 
                    'compliance_approved', 'ed_approved', 'ceo_approved', 'status','certificate_link']
    list_filter = ['status']
    readonly_fields = ['application_date','partner']
    search_fields = ('partner', 'application_date')

    def certificate_link(self, obj):
        if obj.generated_certificate:
            return format_html(
                '<a href="{}" target="_blank">View Certificate</a>', obj.generated_certificate.url
            )
        return "Link not available"
    certificate_link.short_description = "Certificate"

    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name='CEO').exists():
            return [(None, {'fields': ['ceo_approved']})]
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.groups.filter(name='CEO').exists():
            return self.readonly_fields + ['ceo_approved']
        return self.readonly_fields

    def get_fields(self, request, obj=None): 
        base_fields = [
            'service_type', 'partner', 'address','tin_number', 'last_certificate_expiry_date', 'application_date',
             'principal_name', 'contact_number', 'email_address',
            'faith_based_school', 'non_faith_based_school',
            'type_of_business_registration', 'ownership', 'financial_strength', 'name_of_banks',

            'admin_staff_1_name', 'admin_staff_1_nationality', 'admin_staff_1_position',
            'admin_staff_1_education', 'admin_staff_1_years_of_experience', 'admin_staff_1_cv',
            'admin_staff_1_work_permit', 'admin_staff_2_name', 'admin_staff_2_nationality', 'admin_staff_2_position',
            'admin_staff_2_education', 'admin_staff_2_years_of_experience', 'admin_staff_2_cv',
            'admin_staff_2_work_permit', 'admin_staff_3_name', 'admin_staff_3_nationality', 'admin_staff_3_position',
            'admin_staff_3_education', 'admin_staff_3_years_of_experience', 'admin_staff_3_cv',
            'admin_staff_3_work_permit',

            'permit_from_moe', 'letter_of_application', 'business_registration', 'article_of_incorporation',
            'tax_clearance', 'sanitation_policy', 'information_sheet', 'certificate_payment_receipt',

            'number_of_handwashing_facilities', 'number_of_gender_sensitive_latrines',
            'source_of_water', 'specify_other_source', 'number_of_drinking_water_facilities','method_of_payment',

            'attestation'
        ]

        user_groups = list(request.user.groups.values_list('name', flat=True))

        if request.user.is_superuser:
            return base_fields + ['compliance_approved', 'ed_approved', 'ceo_approved', 'status']

        if 'Compliance Director' in user_groups:
            return base_fields + ['compliance_approved']
        elif 'Executive Director' in user_groups:
            if obj and obj.compliance_approved:
                return base_fields + ['compliance_approved', 'ed_approved']
            return base_fields
        elif 'CEO' in user_groups:
            if obj and obj.ed_approved:
                return base_fields + ['compliance_approved', 'ed_approved', 'ceo_approved']
            return base_fields

        return base_fields + ['compliance_approved', 'ed_approved', 'ceo_approved', 'status']

    
    def save_model(self, request, obj, form, change):
        user_groups = list(request.user.groups.values_list('name', flat=True))
        changed_fields = form.changed_data

        if 'compliance_approved' in changed_fields and obj.compliance_approved:
            obj.send_notification('Compliance Director')

        if 'ed_approved' in changed_fields and obj.ed_approved:
            obj.send_notification('Executive Director')

        if 'ceo_approved' in changed_fields and obj.ceo_approved:
            obj.send_notification('CEO')

        # Update status if all approvals are complete
        if obj.compliance_approved and obj.ed_approved and obj.ceo_approved:
            obj.status = 'Approved'

        # Generate certificate only once
        if obj.ceo_approved and not obj.generated_certificate:
           from certificates.certificate_generator import generate_certificate
           generate_certificate(obj)

        super().save_model(request, obj, form, change)


@admin.register(ClearanceApplication)
class ClearanceApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'partner', 'executive_director_name','compliance_director_approved', 'ed_approved', 'ceo_approved', 'email', 'clearance_link')
    search_fields = ('partner', 'executive_director_name', 'email')
    readonly_fields = ['submitted_at']

    def clearance_link(self, obj):
        if obj.generated_clearance:
            return format_html(
                '<a href="{}" target="_blank">View Clearance</a>', obj.generated_clearance.url
            )
        return "Link not available"
    clearance_link.short_description = "Clearance"

    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name='CEO').exists():
            return [(None, {'fields': ['ceo_approved']})]
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.groups.filter(name='CEO').exists():
            return self.readonly_fields + ['ceo_approved']
        return self.readonly_fields

    fieldsets = (
        ('General Information', {
            'fields': (
                'service_type', 'partner', 'head_office_address', 'sub_office_addresses',
                'executive_director_name',
                'telephone_number', 'email','amount_paid',
            )
        }),
        ('WATSAN Construction Experiences', {
            'fields': (
                'project1_name', 'project1_funding_source', 'project1_implementation_period', 'project1_status',
                'project2_name', 'project2_funding_source', 'project2_implementation_period', 'project2_status',
                'project3_name', 'project3_funding_source', 'project3_implementation_period', 'project3_status',
                'project4_name', 'project4_funding_source', 'project4_implementation_period', 'project4_status',
            )
        }),
        ('Difficulties and Lessons Learned', {
            'fields': ('lessons_and_difficulties',)
        }),
        ('Technical Staff', {
            'fields': (
                'staff1_name', 'staff1_nationality', 'staff1_position', 'staff1_education_experience', 'staff1_cv',
                'staff2_name', 'staff2_nationality', 'staff2_position', 'staff2_education_experience', 'staff2_cv',
            )
        }),
        ('Supporting Documents', {
            'fields': (
                'approved_wash_workplan',
                'letter_of_application',
                'business_registration_and_tax_clearance',
                'organization_profile',
                'previous_year_activities_report',
                'clearance_payment_receipt',
            )
        }),
        ('Equipment and Tools', {
            'fields': (
                'light_vehicles', 'pickups_4wd', 'rig_compressor', 'tripod',
                'culvert_mould', 'size_0_90m', 'size_0_76m', 'chain_block',
                'pulley', 'casting_yard', 'additional_equipment',
            )
        }),
        ('Attestation', {
            'fields': ('attestation',)
        }),
        ('Approval', {
            'fields': ('compliance_director_approved', 'ed_approved','ceo_approved',)

            }
        )
       
    )

    def save_model(self, request, obj, form, change):
        user_groups = list(request.user.groups.values_list('name', flat=True))
        changed_fields = form.changed_data

         # Generate certificate only once
        if obj.ceo_approved and not obj.generated_clearance:
           from certificates.clearance_generator import generate_clearance
           generate_clearance(obj)

        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        user = request.user
        readonly = ['submitted_at']

        if 'Compliance Director' in str(user.groups.all()):
            readonly += ['ed_approved', 'ceo_approved']

        elif 'Executive Director' in str(user.groups.all()):
            if not obj or not obj.compliance_director_approved:
                readonly += ['compliance_director_approved', 'ed_approved', 'ceo_approved']
            else:
                readonly += ['compliance_director_approved', 'ceo_approved']

        elif 'CEO' in str(user.groups.all()):
            if not obj or not obj.ed_approved:
                readonly += ['compliance_director_approved', 'ed_approved', 'ceo_approved']
            else:
                readonly += ['compliance_director_approved', 'ed_approved']

        else:
            # All read-only for other users
            readonly += ['compliance_director_approved', 'ed_approved', 'ceo_approved']

        return readonly
    
@admin.register(BusinessCertificateApplication)
class BusinessCertificateApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'partner', 'type_of_business', 'compliance_director_approved', 'ed_approved', 'ceo_approved', 'submitted_at','business_cert_link')
    readonly_fields = ('submitted_at',)
    search_fields = ('partner', 'type_of_business', 'name_of_business_owner')
    list_filter = ('type_of_business',)
    fields = ['service_type', 'partner', 'address', 'contact_number','email','type_of_business','other_business_type','name_of_business_owner','address_of_business_owner','contact_no_of_business_owner','email_of_business_owner','name_of_staff_1','nationality_of_staff_1','position_of_staff_1',
              'education_experience_of_staff_1','cv_of_staff_1','name_of_staff_2','nationality_of_staff_2',
               'position_of_staff_2','education_experience_of_staff_2','cv_of_staff_2', 'name_of_staff_3','nationality_of_staff_3',
               'position_of_staff_3','education_experience_of_staff_3','cv_of_staff_3',
                'letter_of_application','business_registration_document','article_of_incorporation',
                 'tax_clearance','sanitation_waste_plan','b_certificate_payment_receipt','attestation',
                  'submitted_at', 'compliance_director_approved', 'ed_approved', 'ceo_approved']
    
    def business_cert_link(self, obj):
        if obj.generated_business_certificate:
            return format_html(
                '<a href="{}" target="_blank">View Certificate</a>', obj.generated_business_certificate.url
            )
        return "Link not available"
    business_cert_link.short_description = "Business Certificate"

    def get_fieldsets(self, request, obj=None):
        if request.user.groups.filter(name='CEO').exists():
            return [(None, {'fields': ['ceo_approved']})]
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.groups.filter(name='CEO').exists():
            return self.readonly_fields + ['ceo_approved']
        return self.readonly_fields

    def get_readonly_fields(self, request, obj=None):
        user = request.user
        readonly = ['submitted_at']

        if 'Compliance Director' in str(user.groups.all()):
            readonly += ['ed_approved', 'ceo_approved']

        elif 'Executive Director' in str(user.groups.all()):
            if not obj or not obj.compliance_director_approved:
                readonly += ['compliance_director_approved', 'ed_approved', 'ceo_approved']
            else:
                readonly += ['compliance_director_approved', 'ceo_approved']

        elif 'CEO' in str(user.groups.all()):
            if not obj or not obj.ed_approved:
                readonly += ['compliance_director_approved', 'ed_approved', 'ceo_approved']
            else: 
                readonly += ['compliance_director_approved', 'ed_approved']

        else:
            # All read-only for other users
            readonly += ['compliance_director_approved', 'ed_approved', 'ceo_approved']

        return readonly
    
    def save_model(self, request, obj, form, change):
        user_groups = list(request.user.groups.values_list('name', flat=True))
        changed_fields = form.changed_data

         # Generate certificate only once
        if obj.ceo_approved and not obj.generated_business_certificate:
           from certificates.business_cert_generator import generate_business_cert
           generate_business_cert(obj)

        super().save_model(request, obj, form, change)