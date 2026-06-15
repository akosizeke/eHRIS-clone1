from django.contrib import admin

from .models import (
    History,
    Item,
    NonPlantillaEmployee,
    SalaryGrade,
    SalaryGradeStep,
    SalarySchedule,
)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'item_number',
        'employee_name',
        'position_title',
        'office',
        'appointment_type',
        'salary_grade',
        'position_status',
    )
    list_filter = ('employment_type', 'appointment_type', 'position_status', 'salary_grade', 'office')
    search_fields = ('item_number', 'employee_name', 'position_title', 'office__name')
    readonly_fields = ('id', 'created_at', 'modified_at')


@admin.register(NonPlantillaEmployee)
class NonPlantillaEmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'employee_type',
        'office',
        'position_title',
        'reference_number',
        'duration_value',
        'duration_unit',
        'start_date',
        'end_date',
    )
    list_filter = ('employee_type', 'office')
    search_fields = ('name', 'office__name')
    readonly_fields = ('id', 'created_at', 'modified_at')


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('plantilla_item', 'change_type', 'effective_date')
    list_filter = ('change_type', 'effective_date')
    search_fields = ('plantilla_item__item_number', 'plantilla_item__position_title')
    readonly_fields = ('id', 'created_at', 'modified_at')


@admin.register(SalarySchedule)
class SalaryScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'effective_date', 'is_active')
    list_filter = ('is_active', 'effective_date')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(SalaryGrade)
class SalaryGradeAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'grade_number', 'is_active')
    list_filter = ('schedule', 'is_active')
    search_fields = ('schedule__name', 'grade_number')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(SalaryGradeStep)
class SalaryGradeStepAdmin(admin.ModelAdmin):
    list_display = ('salary_grade', 'step_number', 'amount', 'source', 'is_editable')
    list_filter = ('source', 'is_editable', 'salary_grade__schedule')
    search_fields = ('salary_grade__schedule__name', 'salary_grade__grade_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
