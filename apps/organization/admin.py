from django.contrib import admin

from .models import Office, OfficeVersion, Organization


# Admin screen for maintaining organization master records.
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'province_code', 'is_active', 'modified_at')
    list_filter = ('is_active', 'province_code')
    search_fields = ('name', 'short_name', 'province_code')
    readonly_fields = ('id', 'created_at', 'modified_at')


# Admin screen for maintaining offices under each organization.
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'office_type', 'parent_office', 'office_head', 'is_active')
    list_filter = ('office_type', 'is_active', 'organization')
    search_fields = ('name', 'office_code', 'organization__name')
    readonly_fields = ('id', 'created_at', 'modified_at')


# Admin screen for tracking office version history and legal basis links.
@admin.register(OfficeVersion)
class OfficeVersionAdmin(admin.ModelAdmin):
    list_display = ('office_id', 'version_no', 'legal_basis', 'effective_start_date', 'effective_end_date')
    list_filter = ('effective_start_date', 'effective_end_date')
    search_fields = ('office_id__name', 'legal_basis__reference_number', 'change_description')
    readonly_fields = ('id', 'created_at', 'modified_at')
