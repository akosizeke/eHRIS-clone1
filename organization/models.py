# organization/models.py

import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


# =========================================================
# ORGANIZATION MODEL
# =========================================================
# Main government agency or institution
# Example:
# - DENR
# - Department of Agriculture
# - Bulacan Polytechnic College
# =========================================================

class Organization(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)
    province_code = models.CharField(max_length=100)
    address = models.TextField()

    seal_path = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization'

    def __str__(self):
        return self.name


# =========================================================
# OFFICE MODEL
# =========================================================
# Organizational hierarchy structure
#
# Examples:
# - Department
# - Division
# - Unit
#
# This model is SELF-REFERENCING.
#
# Example hierarchy:
#
# College of Engineering
#    └── IT Department
#           └── Web Development Unit
#
# parent_office_id handles the hierarchy.
# =========================================================

class Office(models.Model):
    class OfficeType(models.TextChoices):
        DEPARTMENT = 'Department', 'Department'
        DIVISION = 'Division', 'Division'
        UNIT = 'Unit', 'Unit'

    HEAD_TITLE_DEPARTMENT_HEAD = 'DH'
    HEAD_TITLE_OFFICER_IN_CHARGE = 'OIC'

    OFFICE_HEAD_TITLE_CHOICES = [
        (HEAD_TITLE_DEPARTMENT_HEAD, 'Department Head'),
        (HEAD_TITLE_OFFICER_IN_CHARGE, 'Officer In Charge'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='offices',
        db_column='organization_id',
    )
    parent_office = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        db_column='parent_office_id',
    )
    name = models.CharField(max_length=255)
    office_code = models.CharField(max_length=100, blank=True, default='')
    office_type = models.CharField(max_length=100, choices=OfficeType.choices)
    level_no = models.PositiveIntegerField(default=1)
    # Replace with a ForeignKey once the employee_profile app/model is available.
    office_head = models.UUIDField(null=True, blank=True)
    office_head_title = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_office'
        ordering = ['level_no', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'office_code'],
                condition=~Q(office_code=''),
                name='uniq_office_code_per_org',
            ),
        ]

    def __str__(self):
        code = f' ({self.office_code})' if self.office_code else ''
        return f'{self.name}{code}'

    @property
    def office_head_display(self):
        return self.office_head or ''

    def _set_level_no_from_parent(self):
        self.level_no = self.parent_office.level_no + 1 if self.parent_office_id else 1

    def clean(self):
        super().clean()
        errors = {}

        if self.parent_office_id:
            self._set_level_no_from_parent()
        else:
            self.level_no = 1

        if self.parent_office_id and self.pk and self.parent_office_id == self.pk:
            errors['parent_office'] = ['Office cannot be its own parent.']

        if self.parent_office_id and self.organization_id != self.parent_office.organization_id:
            errors['parent_office'] = errors.get('parent_office', []) + [
                'Parent office must belong to the same organization.'
            ]

        if not self.parent_office_id and self.office_type != self.OfficeType.DEPARTMENT:
            errors['parent_office'] = errors.get('parent_office', []) + [
                'Only a Department can be created without a parent office.'
            ]

        if self.parent_office_id and self.office_type == self.OfficeType.DEPARTMENT:
            errors['office_type'] = ['A Department cannot have a parent office.']

        if self.parent_office_id:
            valid_child_types = {
                self.OfficeType.DEPARTMENT: self.OfficeType.DIVISION,
                self.OfficeType.DIVISION: self.OfficeType.UNIT,
            }
            expected_type = valid_child_types.get(self.parent_office.office_type)
            if expected_type is None:
                errors['parent_office'] = errors.get('parent_office', []) + [
                    'A Unit cannot have child offices.'
                ]
            elif self.office_type != expected_type:
                errors['office_type'] = [
                    f'An office under a {self.parent_office.office_type} must be a {expected_type}.'
                ]

        if self.pk and self.parent_office_id:
            ancestor = self.parent_office
            visited = set()
            while ancestor:
                if ancestor.pk == self.pk:
                    errors['parent_office'] = errors.get('parent_office', []) + [
                        'Circular office hierarchy is not allowed.'
                    ]
                    break
                if ancestor.pk in visited:
                    break
                visited.add(ancestor.pk)
                ancestor = ancestor.parent_office

        if self.office_code and self.organization_id:
            duplicate_code = Office.objects.filter(
                organization_id=self.organization_id,
                office_code__iexact=self.office_code,
            )
            if self.pk:
                duplicate_code = duplicate_code.exclude(pk=self.pk)
            if duplicate_code.exists():
                errors['office_code'] = [
                    'Office code already exists in this organization.'
                ]

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


# =========================================================
# OFFICE VERSION MODEL
# =========================================================
# Tracks office reorganizations and history
#
# Purpose:
# - Preserve historical integrity
# - Track structural changes
# - Track reorganizations
# - Keep office history records
#
# Example:
#
# Version 1:
# MIS Office
#
# Version 2:
# Information Technology Office
#
# Old records remain preserved.
# =========================================================

class OfficeVersion(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    office_id = models.ForeignKey(
        Office,
        on_delete=models.CASCADE,
        related_name='versions',
        db_column='office_id',
    )
    version_no = models.IntegerField()
    effective_start_date = models.DateField()
    effective_end_date = models.DateField(null=True, blank=True)
    legal_basis = models.UUIDField()
    change_description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_office_version'

    def __str__(self):
        return f"{self.office_id.name} - Version {self.version_no}"
