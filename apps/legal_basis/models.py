from django.db import models
from apps.core.models import AbstractBaseModel


# Stores ordinances, resolutions, memoranda, laws, and files used by office/plantilla history.
class LegalBasis(AbstractBaseModel):
    # Allowed document categories shown in legal basis filters and forms.
    REFERENCE_TYPE_CHOICES = [
        ('resolution', 'Resolution'),
        ('EO',         'Executive Order'),
        ('memo',       'Memorandum'),
        ('law',        'Republic Act'),
    ]

    reference_type   = models.CharField(max_length=20, choices=REFERENCE_TYPE_CHOICES)
    reference_number = models.CharField(max_length=100)
    approval_date    = models.DateField(null=True, blank=True)
    effectivity_date = models.DateField()
    document_path    = models.FileField(upload_to='legal_basis/', blank=True, null=True)

    class Meta:
        # Shows the newest effective legal basis first in lists.
        ordering = ['-effectivity_date']
        verbose_name = 'Legal Basis'
        verbose_name_plural = 'Legal Bases'

    # Human-readable label used in templates, admin, and foreign key dropdowns.
    def __str__(self):
        return f"{self.get_reference_type_display()} {self.reference_number}"
