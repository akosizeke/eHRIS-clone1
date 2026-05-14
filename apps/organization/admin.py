from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'province_code', 'is_active', 'modified_at')
    list_filter = ('is_active', 'province_code')
    search_fields = ('name', 'short_name', 'province_code')
    readonly_fields = ('id', 'created_at', 'modified_at')
