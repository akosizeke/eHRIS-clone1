from django import forms

from .models import Item


# Form used by the plantilla create view to validate and style item fields.
class ItemForm(forms.ModelForm):
    class Meta:
        # Fields map directly to the Item model and its office/legal basis links.
        model = Item
        fields = [
            'item_number',
            'position_title',
            'salary_grade',
            'office',
            'employment_type',
            'funding_source',
            'position_status',
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
        self.fields['position_title'].widget.attrs['placeholder'] = 'Example: Administrative Officer IV'
        self.fields['salary_grade'].widget.attrs['min'] = '1'
        self.fields['salary_grade'].widget.attrs['max'] = '33'
        self.fields['item_number'].widget.attrs['maxlength'] = '50'
        self.fields['item_number'].widget.attrs['pattern'] = '[A-Za-z0-9-]+'
        self.fields['position_title'].widget.attrs['maxlength'] = '255'
