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
    class Meta:
        model = Office
        fields = [
            'organization_id',
            'parent_office_id',
            'name',
            'office_code',
            'office_type',
            'level_no',
            'office_head',
            'office_head_title',
            'is_active',
        ]

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data.get('organization_id')
        parent_office = cleaned_data.get('parent_office_id')

        if parent_office and self.instance.pk == parent_office.pk:
            self.add_error('parent_office_id', 'Office cannot be its own parent.')

        if organization and parent_office and parent_office.organization_id_id != organization.pk:
            self.add_error(
                'parent_office_id',
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
