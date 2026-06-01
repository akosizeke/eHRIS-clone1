from django import forms

from .models import Item, NonPlantillaEmployee


# Form used by the plantilla create view to validate and style item fields.
class ItemForm(forms.ModelForm):
    class Meta:
        # Fields map directly to the Item model and its office/legal basis links.
        model = Item
        fields = [
            'item_number',
            'employee_name',
            'position_title',
            'salary_grade',
            'office',
            'employment_type',
            'funding_source',
            'position_status',
            'duties_responsibilities',
            'legalbasis',
        ]

    # Adds labels, placeholders, and shared CSS classes for plantilla templates.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['office'].empty_label = 'Select office'
        self.fields['legalbasis'].empty_label = 'Select legal basis (optional)'

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'org-form-control'

        self.fields['item_number'].widget.attrs['placeholder'] = 'Example: HRMO-001'
        self.fields['employee_name'].widget.attrs['placeholder'] = 'Leave blank for vacant or abolished positions'
        self.fields['position_title'].widget.attrs['placeholder'] = 'Example: Administrative Officer IV'
        self.fields['duties_responsibilities'].widget.attrs['placeholder'] = 'Summarize the position duties and responsibilities'
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

        if status == 'filled' and not employee_name.strip():
            self.add_error('employee_name', 'Filled positions require an employee name.')

        if status in {'vacant', 'abolished'}:
            cleaned_data['employee_name'] = ''

        return cleaned_data


# Form used by the non-plantilla create and edit views.
class NonPlantillaEmployeeForm(forms.ModelForm):
    class Meta:
        model = NonPlantillaEmployee
        fields = [
            'name',
            'employee_type',
            'office',
            'duration_value',
            'duration_unit',
            'start_date',
            'end_date',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['office'].empty_label = 'Select office'
        self.fields['employee_type'].empty_label = 'Select type'

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'org-form-control'

        self.fields['name'].widget.attrs['placeholder'] = 'Employee name'
        self.fields['duration_value'].widget.attrs['min'] = '1'
        self.fields['duration_value'].widget.attrs['placeholder'] = 'Duration'
        self.fields['start_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'org-form-control'}
        )
        self.fields['end_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'org-form-control'}
        )
