import json

from django import forms
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
            'employee_name',
            'position_title',
            'appointment_type',
            'salary_grade',
            'salary_step',
            'office',
            'employment_type',
            'funding_source',
            'position_status',
            'duties_responsibilities',
            'legalbasis',
        ]

    # Adds labels, placeholders, and shared CSS classes for plantilla templates.
    def __init__(self, *args, **kwargs):
        use_salary_grade_controls = kwargs.pop('use_salary_grade_controls', False)
        super().__init__(*args, **kwargs)

        self.fields['office'].empty_label = 'Select office'
        self.fields['legalbasis'].empty_label = 'Select legal basis (optional)'

        if use_salary_grade_controls:
            active_schedule = SalarySchedule.objects.filter(
                is_active=True,
                effective_date__lte=timezone.localdate(),
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
        self.fields['employee_name'].widget.attrs['placeholder'] = 'Leave blank for vacant or abolished positions'
        self.fields['position_title'].widget.attrs['placeholder'] = 'Example: Administrative Officer IV'
        self.fields['appointment_type'].empty_label = None
        self.fields['duties_responsibilities'].widget.attrs['placeholder'] = 'Summarize the position duties and responsibilities'
        if not use_salary_grade_controls:
            self.fields['salary_grade'].widget.attrs['min'] = '1'
            self.fields['salary_grade'].widget.attrs['max'] = '33'
        self.fields['item_number'].widget.attrs['maxlength'] = '50'
        self.fields['item_number'].widget.attrs['pattern'] = '[A-Za-z0-9-]+'
        self.fields['position_title'].widget.attrs['maxlength'] = '255'
        self.fields['employee_name'].widget.attrs['maxlength'] = '255'

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('position_status')
        employee_name = cleaned_data.get('employee_name', '')
        salary_grade = cleaned_data.get('salary_grade')
        salary_step = cleaned_data.get('salary_step')

        if status == 'filled' and not employee_name.strip():
            self.add_error('employee_name', 'Filled positions require an employee name.')

        if status in {'vacant', 'abolished'}:
            cleaned_data['employee_name'] = ''

        if salary_step:
            if not salary_grade:
                self.add_error('salary_step', 'Select a salary grade before selecting a salary step.')
            elif not SalaryGradeStep.objects.filter(
                salary_grade__grade_number=salary_grade,
                step_number=salary_step,
                amount__isnull=False,
            ).exists():
                self.add_error('salary_step', 'Select a valid salary step for the selected salary grade.')

        return cleaned_data


# Form used by the non-plantilla create and edit views.
class NonPlantillaEmployeeForm(forms.ModelForm):
    class Meta:
        model = NonPlantillaEmployee
        fields = [
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
            'compensation_rate',
            'rate_basis',
            'salary_grade',
            'salary_step',
            'service_provider',
            'consultancy_title',
            'contract_amount',
            'work_assignment',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['office'].empty_label = 'Select office'
        self.fields['employee_type'].empty_label = 'Select type'

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'org-form-control'

        self.fields['name'].widget.attrs['placeholder'] = 'Employee name'
        self.fields['position_title'].label = 'Position or Service Title'
        self.fields['position_title'].widget.attrs['placeholder'] = 'Position or service title'
        self.fields['funding_source'].widget.attrs['placeholder'] = 'Funding source'
        self.fields['reference_number'].label = 'Appointment, Contract, or Reference Number'
        self.fields['reference_number'].widget.attrs['placeholder'] = 'Reference number'
        self.fields['duties_responsibilities'].label = 'Duties or Scope of Work'
        self.fields['duties_responsibilities'].widget = forms.Textarea(
            attrs={
                'class': 'org-form-control',
                'placeholder': 'Summarize duties or scope of work',
                'rows': 4,
            }
        )
        self.fields['duration_value'].widget.attrs['min'] = '1'
        self.fields['duration_value'].widget.attrs['placeholder'] = 'Duration'
        self.fields['start_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'org-form-control'}
        )
        self.fields['end_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'org-form-control'}
        )
        self.fields['compensation_rate'].widget.attrs['min'] = '0'
        self.fields['compensation_rate'].widget.attrs['step'] = '0.01'
        self.fields['contract_amount'].widget.attrs['min'] = '0'
        self.fields['contract_amount'].widget.attrs['step'] = '0.01'
        self.fields['salary_grade'].widget.attrs['min'] = '1'
        self.fields['salary_grade'].widget.attrs['max'] = '33'
        self.fields['salary_step'].widget.attrs['min'] = '1'
        self.fields['salary_step'].widget.attrs['max'] = '8'
        self.fields['service_provider'].widget.attrs['placeholder'] = 'Service provider'
        self.fields['consultancy_title'].widget.attrs['placeholder'] = 'Consultancy title'
        self.fields['work_assignment'].label = 'Work Assignment or Emergency Assignment'
        self.fields['work_assignment'].widget.attrs['placeholder'] = 'Work or emergency assignment'
