from django.db import models
from apps.core.models import AbstractBaseModel


class Organization(AbstractBaseModel):
    name         = models.CharField(max_length=255)
    short_name   = models.CharField(max_length=50)
    province_code = models.CharField(max_length=20, blank=True)
    address      = models.TextField(blank=True)
    seal_path    = models.ImageField(upload_to='seals/', blank=True, null=True)
    is_active    = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.short_name


class Office(AbstractBaseModel):
    OFFICE_TYPE_CHOICES = [
        ('department', 'Department'),
        ('division',   'Division'),
        ('unit',       'Unit'),
    ]

    HEAD_TITLE_CHOICES = [
        ('DH',  'Department Head'),
        ('OIC', 'Officer-in-Charge'),
    ]

    organization    = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='offices')
    parent_office   = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    name            = models.CharField(max_length=255)
    office_code     = models.CharField(max_length=50, blank=True)
    office_type     = models.CharField(max_length=20, choices=OFFICE_TYPE_CHOICES)
    level_no        = models.PositiveIntegerField(default=1)
    office_head     = models.CharField(max_length=255, blank=True)
    office_head_title = models.CharField(max_length=10, choices=HEAD_TITLE_CHOICES, blank=True)
    is_active       = models.BooleanField(default=True)

    class Meta:
        ordering = ['level_no', 'name']
        verbose_name = 'Office'
        verbose_name_plural = 'Offices'

    def __str__(self):
        return self.name

    def has_selected_descendant(self, selected_pk):
        if self.children.filter(pk=selected_pk).exists():
            return True
        return any(child.has_selected_descendant(selected_pk) for child in self.children.all())


class OfficeVersion(AbstractBaseModel):
    office               = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='versions')
    version_no           = models.PositiveIntegerField()
    effective_start_date = models.DateField()
    effective_end_date   = models.DateField(null=True, blank=True)
    legal_basis          = models.ForeignKey('legal_basis.LegalBasis', on_delete=models.SET_NULL, null=True, blank=True)
    change_description   = models.TextField(blank=True)

    class Meta:
        ordering = ['-version_no']
        verbose_name = 'Office Version'
        verbose_name_plural = 'Office Versions'

    def __str__(self):
        return f"{self.office} — v{self.version_no}"