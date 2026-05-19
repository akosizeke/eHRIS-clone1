from django import forms

from .models import Office, OfficeVersion, Organization


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name',
            'short_name',
            'province_code',
            'address',
            'seal_path',
            'is_active',
        ]


class OfficeForm(forms.ModelForm):
    organization = forms.ModelChoiceField(queryset=Organization.objects.all(), required=True)
    parent_office = forms.ModelChoiceField(queryset=Office.objects.all(), required=False)
    office_type = forms.ChoiceField(choices=Office.OfficeType.choices, required=True)

    class Meta:
        model = Office
        fields = [
            'organization',
            'parent_office',
            'name',
            'office_code',
            'office_type',
            'office_head',
            'office_head_title',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        selected_organization = None
        organization_value = self.data.get('organization') if self.is_bound else self.initial.get('organization')
        parent_value = self.data.get('parent_office') if self.is_bound else self.initial.get('parent_office')

        if isinstance(organization_value, Organization):
            selected_organization = organization_value
        elif organization_value:
            selected_organization = Organization.objects.filter(pk=organization_value).first()

        if not selected_organization and isinstance(parent_value, Office):
            selected_organization = parent_value.organization
        elif not selected_organization and parent_value:
            parent = Office.objects.filter(pk=parent_value).select_related('organization').first()
            if parent:
                selected_organization = parent.organization

        self.fields['organization'].queryset = Organization.objects.filter(
            is_active=True,
        ).order_by('name')
        parent_queryset = Office.objects.filter(
            is_active=True,
            office_type__in=[
                Office.OfficeType.DEPARTMENT,
                Office.OfficeType.DIVISION,
            ],
        ).select_related('organization')

        if selected_organization:
            parent_queryset = parent_queryset.filter(organization=selected_organization)

        self.fields['parent_office'].queryset = parent_queryset.order_by(
            'organization__name',
            'level_no',
            'name',
        )

        self.fields['organization'].empty_label = 'Select organization'
        self.fields['parent_office'].empty_label = 'Select parent office (optional)'
        self.fields['office_head'].empty_label = 'Select office head (optional)'
        self.fields['office_type'].choices = [('', 'Select office type'), *Office.OfficeType.choices]
        self.fields['is_active'].initial = True

        field_classes = {
            'organization': 'org-form-control',
            'parent_office': 'org-form-control',
            'name': 'org-form-control',
            'office_code': 'org-form-control',
            'office_type': 'org-form-control',
            'office_head': 'org-form-control',
            'office_head_title': 'org-form-control',
            'is_active': 'org-checkbox',
        }
        placeholders = {
            'name': 'Enter office, division, or unit name',
            'office_code': 'Example: PITO, PPDO, SDMD',
            'office_head_title': 'Example: DH, OIC, Unit Head',
        }

        for field_name, css_class in field_classes.items():
            self.fields[field_name].widget.attrs['class'] = css_class
            if field_name in placeholders:
                self.fields[field_name].widget.attrs['placeholder'] = placeholders[field_name]

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data.get('organization')
        parent_office = cleaned_data.get('parent_office')
        office_type = cleaned_data.get('office_type')

        if parent_office and not organization:
            cleaned_data['organization'] = parent_office.organization
            organization = parent_office.organization

        if not organization:
            self.add_error('organization', 'This field is required.')

        if not office_type:
            if not parent_office:
                cleaned_data['office_type'] = Office.OfficeType.DEPARTMENT
            elif parent_office.office_type == Office.OfficeType.DEPARTMENT:
                cleaned_data['office_type'] = Office.OfficeType.DIVISION
            elif parent_office.office_type == Office.OfficeType.DIVISION:
                cleaned_data['office_type'] = Office.OfficeType.UNIT

        if organization and parent_office and parent_office.organization_id != organization.pk:
            self.add_error(
                'parent_office',
                'Parent office must belong to the same organization.',
            )

        return cleaned_data


class OfficeVersionForm(forms.ModelForm):
    class Meta:
        model = OfficeVersion
        fields = [
            'office_id',
            'version_no',
            'effective_start_date',
            'effective_end_date',
            'legal_basis',
            'change_description',
        ]

    def __init__(self, *args, office=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['office_id'].empty_label = 'Select office'
        self.fields['legal_basis'].empty_label = 'Select legal basis'
        if office is not None:
            self.fields['office_id'].initial = office
            self.fields['office_id'].disabled = True

        for field in self.fields.values():
            field.widget.attrs['class'] = 'org-form-control'

        self.fields['effective_start_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'org-form-control'}
        )
        self.fields['effective_end_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'org-form-control'}
        )
