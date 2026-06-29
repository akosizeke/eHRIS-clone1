import json

from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import (
    Item,
    NonPlantillaEmployee,
    SalaryGrade,
    SalaryGradeStep,
    SalarySchedule,
)


class SalaryScheduleForm(forms.ModelForm):
    class Meta:
        model = SalarySchedule
        fields = [
            'name',
            'description',
            'effective_date',
        ]
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs['placeholder'] = 'Example: SSL 2026'
        self.fields['description'].widget.attrs['placeholder'] = 'Optional description or legal basis'

        for field in self.fields.values():
            field.widget.attrs['class'] = 'org-form-control'

    def clean_effective_date(self):
        effective_date = self.cleaned_data['effective_date']
        duplicate = SalarySchedule.objects.filter(effective_date=effective_date)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError(
                'A salary schedule already exists for this effective date.'
            )
        return effective_date


# Form used by the plantilla create view to validate and style item fields.
class ItemForm(forms.ModelForm):
    salary_step = forms.ChoiceField(label='Salary Step', required=False)

    class Meta:
        # Fields map directly to the Item model and its office/legal basis links.
        model = Item
        fields = [
            'item_number',
            'position_title',
            'appointment_type',
            'salary_grade',
            'salary_step',
            'office',
            'employment_type',
            'funding_source',
            'position_status',
            'duties_responsibilities',
            'requirements',
            'legalbasis',
        ]

    # Adds labels, placeholders, and shared CSS classes for plantilla templates.
    def __init__(self, *args, **kwargs):
        use_salary_grade_controls = kwargs.pop('use_salary_grade_controls', False)
        super().__init__(*args, **kwargs)

        self.fields['office'].empty_label = 'Select office'
        self.fields['legalbasis'].empty_label = 'Select legal basis (optional)'
        self.fields['appointment_type'].empty_label = 'Select appointment type'

        if use_salary_grade_controls:
            today = timezone.localdate()
            active_schedule = SalarySchedule.objects.filter(
                is_active=True,
                effective_date__lte=today,
            ).filter(
                Q(inactive_date__isnull=True) | Q(inactive_date__gte=today),
            ).order_by('-effective_date', 'name').first()
            salary_grade_queryset = SalaryGrade.objects.none()
            salary_step_queryset = SalaryGradeStep.objects.none()
            if active_schedule:
                salary_grade_queryset = SalaryGrade.objects.filter(
                    schedule=active_schedule,
                    is_active=True,
                )
                salary_step_queryset = SalaryGradeStep.objects.select_related(
                    'salary_grade',
                ).filter(
                    salary_grade__schedule=active_schedule,
                    salary_grade__is_active=True,
                )

            self.fields['salary_grade'].widget = forms.Select(
                choices=[
                    ('', 'Select salary grade'),
                    *[
                        (grade_number, f'SG {grade_number}')
                        for grade_number in salary_grade_queryset.values_list(
                            'grade_number',
                            flat=True,
                        ).order_by('grade_number')
                    ],
                ],
            )

            salary_steps = {}
            for step in salary_step_queryset.order_by(
                'salary_grade__grade_number',
                'step_number',
            ):
                salary_steps.setdefault(str(step.salary_grade.grade_number), []).append({
                    'value': str(step.step_number),
                    'label': f'Step {step.step_number}',
                })

            selected_salary_grade = self.data.get(
                self.add_prefix('salary_grade'),
                self.initial.get(
                    'salary_grade',
                    getattr(self.instance, 'salary_grade', ''),
                ),
            )
            selected_salary_grade = str(selected_salary_grade) if selected_salary_grade else ''
            selected_salary_steps = salary_steps.get(selected_salary_grade, [])

            self.fields['salary_step'].choices = [
                ('', 'Select salary step' if selected_salary_steps else 'Select salary grade first'),
                *[
                    (step['value'], step['label'])
                    for step in selected_salary_steps
                ],
            ]
            self.fields['salary_step'].widget.attrs['data-steps'] = json.dumps(salary_steps)
            self.fields['salary_step'].widget.attrs['data-selected'] = self.data.get(
                self.add_prefix('salary_step'),
                '',
            )
            if not selected_salary_steps:
                self.fields['salary_step'].widget.attrs['disabled'] = 'disabled'
        else:
            self.fields.pop('salary_step')

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'org-form-control'

        self.fields['item_number'].widget.attrs['placeholder'] = 'Example: HRMO-001'
        self.fields['position_title'].widget.attrs['placeholder'] = 'Example: Administrative Officer IV'
        self.fields['duties_responsibilities'].widget.attrs['placeholder'] = 'Summarize the position duties and responsibilities'
        self.fields['requirements'].widget = forms.Textarea(
            attrs={
                'rows': 3,
                'class': 'org-form-control',
                'placeholder': 'List eligibility, education, experience, training, or other requirements',
            }
        )
        if not use_salary_grade_controls:
            self.fields['salary_grade'].widget.attrs['min'] = '1'
            self.fields['salary_grade'].widget.attrs['max'] = '33'
        self.fields['item_number'].widget.attrs['maxlength'] = '50'
        self.fields['item_number'].widget.attrs['pattern'] = '[A-Za-z0-9-]+'
        self.fields['position_title'].widget.attrs['maxlength'] = '255'


# Form used by the non-plantilla create and edit views.
class NonPlantillaEmployeeForm(forms.ModelForm):
    class Meta:
        model = NonPlantillaEmployee
        fields = [
            'employee_type',
            'office',
            'position_title',
            'funding_source',
            'reference_number',
            'duties_responsibilities',
            'requirements',
            'salary_grade',
            'salary_step',
            'duration_value',
            'duration_unit',
            'service_provider',
            'consultancy_title',
            'work_assignment',
        ]

    def __init__(self, *args, **kwargs):
        args = self._without_inactive_conditional_data(args, kwargs)
        super().__init__(*args, **kwargs)

        self.common_field_names = tuple(NonPlantillaEmployee.COMMON_FORM_FIELDS)
        self.conditional_field_names = NonPlantillaEmployee.all_conditional_fields()
        self.dynamic_field_config = json.dumps({
            employee_type: {
                'fields': list(NonPlantillaEmployee.conditional_fields_for(employee_type)),
                'required': list(NonPlantillaEmployee.conditional_fields_for(employee_type)),
            }
            for employee_type, _ in NonPlantillaEmployee.EMPLOYEE_TYPE_CHOICES
        })

        self.fields['office'].empty_label = 'Select office'
        self.fields['employee_type'].empty_label = 'Select type'

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'org-form-control'

        self.fields['position_title'].widget.attrs['placeholder'] = 'Position or engagement title'
        self.fields['funding_source'].widget.attrs['placeholder'] = 'Funding source'
        self.fields['reference_number'].widget.attrs['placeholder'] = 'Reference number'
        self.fields['duties_responsibilities'].widget.attrs['placeholder'] = 'Assigned duties and responsibilities'
        self.fields['requirements'].widget = forms.Textarea(
            attrs={
                'rows': 3,
                'class': 'org-form-control',
                'placeholder': 'List eligibility, education, experience, training, or other requirements',
            }
        )
        self.fields['duration_value'].widget.attrs['min'] = '1'
        self.fields['duration_value'].widget.attrs['placeholder'] = 'Duration'
        self.fields['service_provider'].widget.attrs['placeholder'] = 'Service provider'
        self.fields['consultancy_title'].widget.attrs['placeholder'] = 'Consultancy title'
        self.fields['work_assignment'].widget.attrs['placeholder'] = 'Work assignment'
        self.fields['duties_responsibilities'].widget = forms.Textarea(
            attrs={
                'rows': 3,
                'class': 'org-form-control',
                'placeholder': 'Assigned duties and responsibilities',
            }
        )
        self._configure_salary_fields()

    @staticmethod
    def _without_inactive_conditional_data(args, kwargs):
        data = kwargs.get('data')
        args = list(args)

        if data is None and args:
            data = args[0]

        if data is None:
            return tuple(args)

        employee_type = data.get('employee_type')
        active_fields = set(NonPlantillaEmployee.conditional_fields_for(employee_type))
        inactive_fields = set(NonPlantillaEmployee.all_conditional_fields()) - active_fields

        if not inactive_fields:
            return tuple(args)

        cleaned_data = data.copy()
        for field_name in inactive_fields:
            cleaned_data[field_name] = ''

        if 'data' in kwargs:
            kwargs['data'] = cleaned_data
        elif args:
            args[0] = cleaned_data

        return tuple(args)

    def _configure_salary_fields(self):
        today = timezone.localdate()
        active_schedule = SalarySchedule.objects.filter(
            is_active=True,
            effective_date__lte=today,
        ).filter(
            Q(inactive_date__isnull=True) | Q(inactive_date__gte=today),
        ).order_by('-effective_date', 'name').first()

        salary_grade_queryset = SalaryGrade.objects.none()
        salary_step_queryset = SalaryGradeStep.objects.none()
        if active_schedule:
            salary_grade_queryset = SalaryGrade.objects.filter(
                schedule=active_schedule,
                is_active=True,
            )
            salary_step_queryset = SalaryGradeStep.objects.select_related(
                'salary_grade',
            ).filter(
                salary_grade__schedule=active_schedule,
                salary_grade__is_active=True,
            )

        self.fields['salary_grade'].widget = forms.Select(
            choices=[
                ('', 'Select salary grade'),
                *[
                    (grade_number, f'SG {grade_number}')
                    for grade_number in salary_grade_queryset.values_list(
                        'grade_number',
                        flat=True,
                    ).order_by('grade_number')
                ],
            ],
            attrs={'class': 'org-form-control'},
        )

        salary_steps = {}
        for step in salary_step_queryset.order_by(
            'salary_grade__grade_number',
            'step_number',
        ):
            salary_steps.setdefault(str(step.salary_grade.grade_number), []).append({
                'value': str(step.step_number),
                'label': f'Step {step.step_number}',
            })

        selected_salary_grade = self.data.get(
            self.add_prefix('salary_grade'),
            self.initial.get(
                'salary_grade',
                getattr(self.instance, 'salary_grade', ''),
            ),
        )
        selected_salary_grade = str(selected_salary_grade) if selected_salary_grade else ''
        selected_salary_steps = salary_steps.get(selected_salary_grade, [])

        self.fields['salary_step'].widget = forms.Select(
            choices=[
                ('', 'Select salary step' if selected_salary_steps else 'Select salary grade first'),
                *[
                    (step['value'], step['label'])
                    for step in selected_salary_steps
                ],
            ],
            attrs={
                'class': 'org-form-control',
                'data-steps': json.dumps(salary_steps),
                'data-selected': self.data.get(self.add_prefix('salary_step'), ''),
            },
        )
        if not selected_salary_steps:
            self.fields['salary_step'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super().clean()
        employee_type = cleaned_data.get('employee_type')
        active_fields = set(NonPlantillaEmployee.conditional_fields_for(employee_type))

        for field_name in NonPlantillaEmployee.all_conditional_fields():
            if field_name not in active_fields:
                cleaned_data[field_name] = None if self._meta.model._meta.get_field(field_name).null else ''

        salary_grade = cleaned_data.get('salary_grade')
        salary_step = cleaned_data.get('salary_step')
        if salary_grade and salary_step:
            today = timezone.localdate()
            step_exists = SalaryGradeStep.objects.filter(
                salary_grade__grade_number=salary_grade,
                salary_grade__schedule__is_active=True,
                salary_grade__schedule__effective_date__lte=today,
                salary_grade__is_active=True,
                step_number=salary_step,
            ).filter(
                Q(salary_grade__schedule__inactive_date__isnull=True)
                | Q(salary_grade__schedule__inactive_date__gte=today),
            ).exists()
            if not step_exists:
                self.add_error('salary_step', 'Select a valid salary step for this salary grade.')

        return cleaned_data
