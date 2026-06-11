import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db.models.functions import Lower
from apps.core.models import AbstractBaseModel
from django.conf import settings


item_number_validator = RegexValidator(
    regex=r'^[A-Za-z0-9-]+$',
    message='Item number may contain letters, numbers, and hyphens only.',
)


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

    item_number     = models.CharField(max_length=50, unique=True, validators=[item_number_validator])
    employee_name   = models.CharField(max_length=255, blank=True, default='')
    position_title  = models.CharField(max_length=255)
    salary_grade    = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(33)])
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    funding_source  = models.CharField(max_length=10, choices=FUNDING_SOURCE_CHOICES)
    position_status = models.CharField(max_length=20, choices=POSITION_STATUS_CHOICES, default='vacant')
    duties_responsibilities = models.TextField(blank=True, default='')

    office          = models.ForeignKey('organization.Office',    on_delete=models.PROTECT, related_name='plantilla_items')
    legalbasis      = models.ForeignKey('legal_basis.LegalBasis', on_delete=models.PROTECT, related_name='plantilla_items', null=True, blank=True)

    class Meta:
        # Orders plantilla records by item number for list and admin views.
        ordering = ['item_number']
        verbose_name = 'Plantilla Item'
        verbose_name_plural = 'Plantilla Items'
        constraints = [
            models.UniqueConstraint(
                Lower('position_title'),
                models.F('office'),
                name='uniq_plantilla_position_title_per_office_ci',
            ),
            models.CheckConstraint(
                condition=models.Q(salary_grade__gte=1, salary_grade__lte=33),
                name='plantilla_salary_grade_1_33',
            ),
            models.CheckConstraint(
                condition=models.Q(item_number__regex=r'^[A-Z0-9-]+$'),
                name='plantilla_item_number_format',
            ),
        ]

    def __str__(self):
        return f"{self.item_number} — {self.position_title}"

    def clean(self):
        super().clean()
        errors = {}

        self.item_number = self.item_number.strip().upper() if self.item_number else self.item_number
        self.employee_name = self.employee_name.strip() if self.employee_name else ''
        self.position_title = self.position_title.strip() if self.position_title else self.position_title
        self.duties_responsibilities = (
            self.duties_responsibilities.strip()
            if self.duties_responsibilities
            else ''
        )

        if self.position_status in {'vacant', 'abolished'}:
            self.employee_name = ''

        if self.position_title and self.office_id:
            duplicate_position = Item.objects.filter(
                office_id=self.office_id,
                position_title__iexact=self.position_title,
            )
            if self.pk:
                duplicate_position = duplicate_position.exclude(pk=self.pk)
            if duplicate_position.exists():
                errors['position_title'] = [
                    'Position title already exists for this office.'
                ]

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.item_number = self.item_number.strip().upper() if self.item_number else self.item_number
        self.full_clean()
        return super().save(*args, **kwargs)


# Non-plantilla employees such as Job Order and Casual personnel.
class NonPlantillaEmployee(AbstractBaseModel):

    EMPLOYEE_TYPE_CHOICES = [
        ('JO', 'Job Order'),
        ('casual', 'Casual'),
    ]

    DURATION_UNIT_CHOICES = [
        ('months', 'Months'),
        ('years', 'Years'),
    ]

    name           = models.CharField(max_length=255)
    employee_type  = models.CharField(max_length=20, choices=EMPLOYEE_TYPE_CHOICES)
    office         = models.ForeignKey('organization.Office', on_delete=models.PROTECT, related_name='non_plantilla_employees')
    duration_value = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    duration_unit  = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='months')
    start_date     = models.DateField()
    end_date       = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Non-Plantilla Employee'
        verbose_name_plural = 'Non-Plantilla Employees'
        indexes = [
            models.Index(fields=['employee_type']),
            models.Index(fields=['office']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_employee_type_display()}"

    @property
    def duration_display(self):
        unit = 'month' if self.duration_value == 1 and self.duration_unit == 'months' else self.duration_unit
        if self.duration_value == 1 and self.duration_unit == 'years':
            unit = 'year'
        return f'{self.duration_value} {unit}'

    @property
    def service_months(self):
        if self.duration_unit == 'years':
            return self.duration_value * 12
        return self.duration_value

    @property
    def eligible_for_permanent(self):
        return self.service_months >= 24

    def clean(self):
        super().clean()
        errors = {}

        self.name = self.name.strip() if self.name else self.name

        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors['end_date'] = ['End date cannot be earlier than start date.']

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


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

# Salary schedule is the version/container for one complete salary table.
class SalarySchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_salary_schedules",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_salary_schedules",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "salary_schedule"
        ordering = ["-effective_date", "name"]
        verbose_name = "Salary Schedule"
        verbose_name_plural = "Salary Schedules"

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Salary schedule name is required."})


class SalaryGrade(models.Model):
    """
    Stores the salary grade number under a specific salary schedule.
    Example: Salary Grade 1, Salary Grade 2, Salary Grade 33, Salary Grade 34, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(
        SalarySchedule,
        on_delete=models.PROTECT,
        related_name="salary_grades",
    )
    grade_number = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_salary_grades",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_salary_grades",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "salary_grade"
        ordering = ["schedule", "grade_number"]
        verbose_name = "Salary Grade"
        verbose_name_plural = "Salary Grades"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "grade_number"],
                name="unique_salary_grade_per_schedule",
            )
        ]

    def __str__(self):
        return f"{self.schedule.name} - Salary Grade {self.grade_number}"

    def clean(self):
        if self.grade_number < 1:
            raise ValidationError({
                "grade_number": "Salary grade number must be greater than zero."
            })


class SalaryGradeStep(models.Model):
    """
    Stores each salary step amount.
    Each salary grade has Step 1 to Step 8.
    Each step has its own amount, source, and edit status.
    """

    class SourceType(models.TextChoices):
        MANUAL = "manual", "Manual"
        IMPORTED = "imported", "Imported"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salary_grade = models.ForeignKey(SalaryGrade, on_delete=models.PROTECT, related_name="steps")
    step_number = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField()
    source = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    is_editable = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_salary_grade_steps",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_salary_grade_steps",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "salary_grade_step"
        ordering = ["salary_grade__grade_number", "step_number"]
        verbose_name = "Salary Grade Step"
        verbose_name_plural = "Salary Grade Steps"
        constraints = [
            models.UniqueConstraint(
                fields=["salary_grade", "step_number"],
                name="unique_step_per_salary_grade"
            )
        ]

    def __str__(self):
        return (
            f"Salary Grade {self.salary_grade.grade_number} "
            f"- Step {self.step_number} - {self.amount}"
        )

    @property
    def is_locked(self):
        return not self.is_editable

    def clean(self):
        if self.step_number < 1 or self.step_number > 8:
            raise ValidationError({
                "step_number": "Step number must be from 1 to 8 only."
            })

        if self.amount is None or self.amount < 1:
            raise ValidationError({
                "amount": "Salary amount must be greater than zero."
            })

        self.is_editable = self.source == self.SourceType.MANUAL

    def save(self, *args, **kwargs):
        self.full_clean()
        update_fields = kwargs.get("update_fields")
        if update_fields and "source" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"is_editable"}
        super().save(*args, **kwargs)
