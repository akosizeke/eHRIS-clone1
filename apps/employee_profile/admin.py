from django.contrib import admin

from .models import EmployeeProfile


# Admin screen for maintaining employees used by office head selections.
@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'last_name', 'first_name', 'is_active', 'modified_at')
    list_filter = ('is_active',)
    search_fields = ('employee_number', 'first_name', 'middle_name', 'last_name')
    readonly_fields = ('id', 'created_at', 'modified_at')
