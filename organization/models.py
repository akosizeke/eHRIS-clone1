# organization/models.py

import uuid
from django.db import models


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
    OFFICE_TYPE_DEPARTMENT = 'Department'
    OFFICE_TYPE_DIVISION = 'Division'
    OFFICE_TYPE_UNIT = 'Unit'

    OFFICE_TYPE_CHOICES = [
        (OFFICE_TYPE_DEPARTMENT, 'Department'),
        (OFFICE_TYPE_DIVISION, 'Division'),
        (OFFICE_TYPE_UNIT, 'Unit'),
    ]

    HEAD_TITLE_DEPARTMENT_HEAD = 'DH'
    HEAD_TITLE_OFFICER_IN_CHARGE = 'OIC'

    OFFICE_HEAD_TITLE_CHOICES = [
        (HEAD_TITLE_DEPARTMENT_HEAD, 'Department Head'),
        (HEAD_TITLE_OFFICER_IN_CHARGE, 'Officer In Charge'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='offices',
        db_column='organization_id',
    )
    parent_office_id = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_offices',
        db_column='parent_office_id',
    )
    name = models.CharField(max_length=255)
    office_code = models.CharField(max_length=100)
    office_type = models.CharField(max_length=100, choices=OFFICE_TYPE_CHOICES)
    level_no = models.IntegerField()
    # Replace with a ForeignKey once the employee_profile app/model is available.
    office_head = models.UUIDField(null=True, blank=True)
    office_head_title = models.CharField(max_length=100, choices=OFFICE_HEAD_TITLE_CHOICES)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_office'
        ordering = ['level_no', 'name']

    def __str__(self):
        return self.name


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
