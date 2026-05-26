from django.db import models
from apps.core.models import AbstractBaseModel


# Plantilla position item linked to an office and optional legal basis.
class Item(AbstractBaseModel):

    # Employment category choices shown in plantilla forms and filters.
    EMPLOYMENT_TYPE_CHOICES = [
        ('permanent', 'Permanent'),
        ('casual',    'Casual'),
        ('contractual', 'Contractual'),
        ('coterminous', 'Job Order/Coterminous'),
    ]

    # Funding source choices stored per plantilla position.
    FUNDING_SOURCE_CHOICES = [
        ('PS',   'PS'),
        ('MOOE', 'MOOE'),
        ('CO',   'CO'),
    ]

    # Current lifecycle status for each plantilla item.
    POSITION_STATUS_CHOICES = [
        ('filled',    'Filled'),
        ('vacant',    'Vacant'),
        ('abolished', 'Abolished'),
    ]

    item_number     = models.CharField(max_length=50, unique=True)
    position_title  = models.CharField(max_length=255)
    salary_grade    = models.PositiveIntegerField()
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    funding_source  = models.CharField(max_length=10, choices=FUNDING_SOURCE_CHOICES)
    position_status = models.CharField(max_length=20, choices=POSITION_STATUS_CHOICES, default='vacant')

    office          = models.ForeignKey('organization.Office',    on_delete=models.PROTECT, related_name='plantilla_items')
    legalbasis      = models.ForeignKey('legal_basis.LegalBasis', on_delete=models.PROTECT, related_name='plantilla_items', null=True, blank=True)

    class Meta:
        # Orders plantilla records by item number for list and admin views.
        ordering = ['item_number']
        verbose_name = 'Plantilla Item'
        verbose_name_plural = 'Plantilla Items'

    def __str__(self):
        return f"{self.item_number} — {self.position_title}"


# Tracks plantilla item changes such as reassignment, status, and salary grade updates.
class History(AbstractBaseModel):

    # Allowed change categories for plantilla history records.
    CHANGE_TYPE_CHOICES = [
        ('salary_grade', 'Salary Grade Change'),
        ('office',       'Office Reassignment'),
        ('status',       'Status Change'),
    ]

    plantilla_item   = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='history')
    old_salary_grade = models.PositiveIntegerField(null=True, blank=True)
    new_salary_grade = models.PositiveIntegerField(null=True, blank=True)
    old_office       = models.ForeignKey('organization.Office', on_delete=models.SET_NULL, null=True, blank=True, related_name='old_office_history')
    new_office       = models.ForeignKey('organization.Office', on_delete=models.SET_NULL, null=True, blank=True, related_name='new_office_history')
    change_type      = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    effective_date   = models.DateField()
    legalbasis       = models.ForeignKey('legal_basis.LegalBasis', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        # Shows the most recent plantilla history entry first.
        ordering = ['-effective_date']
        verbose_name = 'History'
        verbose_name_plural = 'Histories'

    def __str__(self):
        return f"{self.plantilla_item} — {self.get_change_type_display()}"
