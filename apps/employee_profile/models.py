from django.db import models

from apps.core.models import AbstractBaseModel


class EmployeeProfile(AbstractBaseModel):
    employee_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=20, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'employee_profile'
        ordering = ['last_name', 'first_name']
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'

    def __str__(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return ' '.join(part for part in parts if part).strip()
