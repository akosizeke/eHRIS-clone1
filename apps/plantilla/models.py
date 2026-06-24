from django.db import models
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db.models.functions import Lower
from django.utils import timezone
from apps.core.models import AbstractBaseModel
from django.conf import settings


item_number_validator = RegexValidator(
    regex=r'^[A-Za-z0-9-]+$',
    message='Item number may contain letters, numbers, and hyphens only.',
)


# Plantilla position item linked to an office and optional legal basis.
class Item(AbstractBaseModel):
    class AppointmentType(models.TextChoices):
        PERMANENT = 'PERMANENT', 'Permanent'
        COTERMINOUS_ELECTIVE = 'COTERMINOUS_ELECTIVE', 'Coterminous / Elective Official'

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
    appointment_type = models.CharField(
        max_length=30,
        choices=AppointmentType.choices,
        default=AppointmentType.PERMANENT,
    )
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
        return f"{self.item_number} - {self.position_title}"

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
    class EmployeeType(models.TextChoices):
        JOB_ORDER = 'JOB_ORDER', 'Job Order'
        CONTRACT_OF_SERVICE = 'CONTRACT_OF_SERVICE', 'Contract of Service'
        CASUAL = 'CASUAL', 'Casual'
        CONTRACTUAL = 'CONTRACTUAL', 'Contractual'
        PROJECT_BASED = 'PROJECT_BASED', 'Project-Based'
        TEMPORARY = 'TEMPORARY', 'Temporary'
        EMERGENCY_WORKER = 'EMERGENCY_WORKER', 'Emergency Worker'
        SUBSTITUTE = 'SUBSTITUTE', 'Substitute'
        OUTSOURCED_PERSONNEL = 'OUTSOURCED_PERSONNEL', 'Outsourced Personnel'
        CONSULTANT = 'CONSULTANT', 'Consultant'

    class RateBasis(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        MONTHLY = 'MONTHLY', 'Monthly'
        LUMP_SUM = 'LUMP_SUM', 'Lump Sum'
        PER_DELIVERABLE = 'PER_DELIVERABLE', 'Per Deliverable'

    EMPLOYEE_TYPE_CHOICES = EmployeeType.choices
    DURATION_UNIT_CHOICES = [
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ]
    COMPENSATION_TYPES = {
        EmployeeType.JOB_ORDER,
        EmployeeType.CONTRACT_OF_SERVICE,
    }
    CONDITIONAL_FIELD_GROUPS = {
        EmployeeType.JOB_ORDER: ('compensation_rate', 'rate_basis'),
        EmployeeType.CONTRACT_OF_SERVICE: ('compensation_rate', 'rate_basis'),
        EmployeeType.CASUAL: ('salary_grade', 'salary_step'),
        EmployeeType.CONTRACTUAL: ('salary_grade', 'salary_step'),
        EmployeeType.PROJECT_BASED: ('salary_grade', 'salary_step'),
        EmployeeType.TEMPORARY: ('salary_grade', 'salary_step'),
        EmployeeType.EMERGENCY_WORKER: ('work_assignment',),
        EmployeeType.SUBSTITUTE: ('salary_grade', 'salary_step'),
        EmployeeType.OUTSOURCED_PERSONNEL: ('service_provider',),
        EmployeeType.CONSULTANT: ('consultancy_title', 'contract_amount'),
    }
    COMMON_FORM_FIELDS = [
        'name',
        'employee_type',
        'office',
        'position_title',
        'funding_source',
        'reference_number',
        'duties_responsibilities',
        'duration_value',
        'duration_unit',
        'start_date',
        'end_date',
    ]
    SALARY_GRADE_TYPES = {
        EmployeeType.CASUAL,
        EmployeeType.CONTRACTUAL,
        EmployeeType.PROJECT_BASED,
        EmployeeType.TEMPORARY,
        EmployeeType.SUBSTITUTE,
    }

    name           = models.CharField(max_length=255)
    employee_type  = models.CharField(max_length=30, choices=EMPLOYEE_TYPE_CHOICES)
    office         = models.ForeignKey('organization.Office', on_delete=models.PROTECT, related_name='non_plantilla_employees')
    position_title = models.CharField(max_length=255, blank=True, default='')
    funding_source = models.CharField(max_length=255, blank=True, default='')
    reference_number = models.CharField(max_length=100, blank=True, default='')
    duties_responsibilities = models.TextField(blank=True, default='')
    duration_value = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    duration_unit  = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='months')
    start_date     = models.DateField()
    end_date       = models.DateField(null=True, blank=True)
    compensation_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    rate_basis = models.CharField(
        max_length=20,
        choices=RateBasis.choices,
        blank=True,
        default='',
    )
    salary_grade = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(33)],
    )
    salary_step = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    service_provider = models.CharField(max_length=255, blank=True, default='')
    consultancy_title = models.CharField(max_length=255, blank=True, default='')
    contract_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    work_assignment = models.CharField(max_length=255, blank=True, default='')

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

    @classmethod
    def conditional_fields_for(cls, employee_type):
        return cls.CONDITIONAL_FIELD_GROUPS.get(employee_type, ())

    @classmethod
    def all_conditional_fields(cls):
        field_names = []
        for fields in cls.CONDITIONAL_FIELD_GROUPS.values():
            for field_name in fields:
                if field_name not in field_names:
                    field_names.append(field_name)
        return tuple(field_names)

    def _empty_value_for_field(self, field_name):
        model_field = self._meta.get_field(field_name)
        return None if model_field.null else ''

    def _clear_inactive_conditional_fields(self):
        active_fields = set(self.conditional_fields_for(self.employee_type))
        for field_name in self.all_conditional_fields():
            if field_name not in active_fields:
                setattr(self, field_name, self._empty_value_for_field(field_name))

    @property
    def duration_display(self):
        singular_units = {
            'days': 'day',
            'weeks': 'week',
            'months': 'month',
            'years': 'year',
        }
        unit = (
            singular_units[self.duration_unit]
            if self.duration_value == 1
            else self.duration_unit
        )
        return f'{self.duration_value} {unit}'

    @property
    def service_months(self):
        if self.duration_unit == 'days':
            return self.duration_value // 30
        if self.duration_unit == 'weeks':
            return self.duration_value // 4
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
        self.position_title = self.position_title.strip() if self.position_title else ''
        self.funding_source = self.funding_source.strip() if self.funding_source else ''
        self.reference_number = self.reference_number.strip() if self.reference_number else ''
        self.duties_responsibilities = (
            self.duties_responsibilities.strip()
            if self.duties_responsibilities
            else ''
        )
        self.service_provider = self.service_provider.strip() if self.service_provider else ''
        self.consultancy_title = self.consultancy_title.strip() if self.consultancy_title else ''
        self.work_assignment = self.work_assignment.strip() if self.work_assignment else ''
        self._clear_inactive_conditional_fields()

        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors['end_date'] = ['End date cannot be earlier than start date.']

        if self.employee_type in self.COMPENSATION_TYPES:
            if self.compensation_rate is None:
                errors['compensation_rate'] = ['Compensation rate is required for this employee type.']
            if not self.rate_basis:
                errors['rate_basis'] = ['Rate basis is required for this employee type.']

        if self.employee_type in self.SALARY_GRADE_TYPES:
            if self.salary_grade is None:
                errors['salary_grade'] = ['Salary grade is required for this employee type.']
            if self.salary_step is None:
                errors['salary_step'] = ['Salary step is required for this employee type.']

        if self.employee_type == self.EmployeeType.OUTSOURCED_PERSONNEL and not self.service_provider:
            errors['service_provider'] = ['Service provider is required for outsourced personnel.']

        if self.employee_type == self.EmployeeType.CONSULTANT:
            if not self.consultancy_title:
                errors['consultancy_title'] = ['Consultancy title is required for consultants.']
            if self.contract_amount is None:
                errors['contract_amount'] = ['Contract amount is required for consultants.']

        if self.employee_type == self.EmployeeType.EMERGENCY_WORKER and not self.work_assignment:
            errors['work_assignment'] = ['Work assignment is required for emergency workers.']

        if self.reference_number:
            duplicate_reference = NonPlantillaEmployee.objects.filter(
                reference_number__iexact=self.reference_number,
            )
            if self.pk:
                duplicate_reference = duplicate_reference.exclude(pk=self.pk)
            if duplicate_reference.exists():
                errors['reference_number'] = ['Reference number already exists.']

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
        return f"{self.plantilla_item} - {self.get_change_type_display()}"

#CAMILLE CRISOSTOMO - 2026-06-04
#SALARY GRADE MODEL FOR SALARY GRADE TABLE


class SalarySchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(null=True, blank=True)
    effective_date = models.DateField()
    inactive_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_salary_schedules',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_salary_schedules',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "salary_schedule"
        ordering = ["-effective_date", "name"]
        verbose_name = "Salary Schedule"
        verbose_name_plural = "Salary Schedules"
        constraints = [
            models.UniqueConstraint(
                fields=["effective_date"],
                name="unique_salary_schedule_effective_date",
            )
        ]

    def __str__(self):
        return self.name

    @property
    def is_effective(self):
        today = timezone.localdate()
        return (
            self.is_active
            and self.effective_date <= today
            and (self.inactive_date is None or self.inactive_date >= today)
        )

    @property
    def is_inactive(self):
        return self.inactive_date is not None and self.inactive_date < timezone.localdate()

    def clean(self):
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Salary schedule name is required."})
        self.name = self.name.strip()
        self.description = self.description.strip() if self.description else None


class SalaryGrade(models.Model):
    """
    Represents the salary grade number.
    Example: Salary Grade 1, Salary Grade 2, Salary Grade 33, Salary Grade 34.
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
        related_name='created_salary_grades',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_salary_grades',
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
        return f"{self.schedule} - Salary Grade {self.grade_number}"

    def clean(self):
        if self.grade_number < 1:
            raise ValidationError({
                "grade_number": "Salary grade must be greater than 0."
            })


class SalaryGradeStep(models.Model):
    """
    Represents one step amount inside a salary grade.
    Example: Salary Grade 2 - Step 1 - 14900.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class SourceType(models.TextChoices):
        MANUAL = "manual", "Manual"
        IMPORTED = "imported", "Imported"

    salary_grade = models.ForeignKey(SalaryGrade, on_delete=models.PROTECT, related_name="steps")
    step_number = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField()
    source = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    is_editable = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_salary_grade_steps',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_salary_grade_steps',
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
            f"Salary Grade {self.salary_grade.grade_number} - "
            f"Step {self.step_number}"
        )

    @property
    def is_locked(self):
        """
        Imported values are locked.
        Manual values are editable.
        """
        return not self.is_editable

    def clean(self):
        if self.step_number < 1 or self.step_number > 8:
            raise ValidationError({
                "step_number": "Step number must be from 1 to 8 only."
            })
        if self.amount is None or self.amount < 1:
            raise ValidationError({
                "amount": "Amount must be greater than 0."
            })
        self.is_editable = self.source == self.SourceType.MANUAL

    def save(self, *args, **kwargs):
        self.full_clean()
        update_fields = kwargs.get("update_fields")
        if update_fields and "source" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"is_editable"}
        return super().save(*args, **kwargs)
