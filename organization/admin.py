from django.contrib import admin

from .forms import OfficeForm, OfficeVersionForm, OrganizationForm
from .models import Office, OfficeVersion, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationForm
    list_display = ('name', 'short_name', 'province_code', 'is_active')
    list_filter = ('is_active', 'province_code')
    search_fields = ('name', 'short_name', 'province_code')
    readonly_fields = ('id', 'created_at', 'modified_at')


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    form = OfficeForm
    list_display = (
        'name',
        'office_code',
        'office_type',
        'level_no',
        'parent_office',
        'organization',
        'office_head',
        'office_head_title',
        'is_active',
        'modified_at',
    )
    list_filter = ('office_type', 'is_active', 'organization')
    search_fields = ('name', 'office_code', 'organization__name')
    readonly_fields = ('id', 'created_at', 'modified_at')
    autocomplete_fields = ('organization', 'parent_office')


@admin.register(OfficeVersion)
class OfficeVersionAdmin(admin.ModelAdmin):
    form = OfficeVersionForm
    list_display = (
        'office_id',
        'version_no',
        'effective_start_date',
        'effective_end_date',
    )
    list_filter = ('effective_start_date', 'effective_end_date')
    search_fields = ('office_id__name', 'office_id__office_code', 'change_description')
    readonly_fields = ('id', 'created_at', 'modified_at')
    autocomplete_fields = ('office_id',)
