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
    organization = forms.ModelChoiceField(queryset=Organization.objects.all(), required=False)
    parent_office = forms.ModelChoiceField(queryset=Office.objects.all(), required=False)
    office_type = forms.ChoiceField(choices=Office.OfficeType.choices, required=False)

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
