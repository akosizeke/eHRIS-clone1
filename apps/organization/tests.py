import json
from datetime import date
from uuid import uuid4

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from apps.legal_basis.models import LegalBasis

from .forms import OfficeForm
from .models import Office, OfficeVersion, Organization


# Covers organization API create, list, update, deactivate, and page rendering.
class OrganizationCrudTests(TestCase):
    # Shared valid payload for organization API tests.
    def setUp(self):
        self.payload = {
            'name': 'City Government of Malolos',
            'short_name': 'Malolos City',
            'province_code': '3000',
            'address': 'Malolos, Bulacan',
            'seal_path': 'seals/malolos.png',
        }

    # Sends JSON POST requests to organization API endpoints.
    def post_json(self, url, payload):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    # Sends JSON PATCH requests to organization detail endpoints.
    def patch_json(self, url, payload):
        return self.client.patch(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    # Verifies organization API creates active records.
    def test_create_organization(self):
        response = self.post_json(reverse('organization:organization_collection'), self.payload)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], self.payload['name'])
        self.assertTrue(data['is_active'])
        self.assertTrue(Organization.objects.filter(id=data['id']).exists())

    # Ensures model/API validation rejects blank organization names.
    def test_create_organization_requires_name(self):
        payload = {**self.payload, 'name': ' '}

        response = self.post_json(reverse('organization:organization_collection'), payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json()['errors'])

    def test_create_organization_rejects_duplicate_name_case_insensitive(self):
        Organization.objects.create(**self.payload)
        payload = {
            **self.payload,
            'name': self.payload['name'].lower(),
            'short_name': 'Different Short Name',
        }

        response = self.post_json(reverse('organization:organization_collection'), payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json()['errors'])

    def test_create_organization_rejects_invalid_province_code(self):
        payload = {**self.payload, 'province_code': 'BUL'}

        response = self.post_json(reverse('organization:organization_collection'), payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('province_code', response.json()['errors'])

    def test_create_organization_rejects_special_characters(self):
        payload = {**self.payload, 'name': 'City <script>'}

        response = self.post_json(reverse('organization:organization_collection'), payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json()['errors'])

    # Confirms inactive organizations are hidden unless requested.
    def test_list_excludes_inactive_by_default(self):
        Organization.objects.create(**self.payload)
        Organization.objects.create(
            name='Inactive City',
            short_name='Inactive',
            province_code='3000',
            address='Bulacan',
            seal_path='seals/inactive.png',
            is_active=False,
        )

        response = self.client.get(reverse('organization:organization_collection'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)

    # Verifies partial updates through the organization detail API.
    def test_patch_organization(self):
        organization = Organization.objects.create(**self.payload)
        url = reverse('organization:organization_detail', args=[organization.id])

        response = self.patch_json(url, {'short_name': 'Malolos'})

        self.assertEqual(response.status_code, 200)
        organization.refresh_from_db()
        self.assertEqual(organization.short_name, 'Malolos')

    # Verifies inactive organizations can be reactivated through the API.
    def test_patch_reactivates_organization(self):
        organization = Organization.objects.create(**self.payload, is_active=False)
        url = reverse('organization:organization_detail', args=[organization.id])

        response = self.patch_json(url, {'is_active': True})

        self.assertEqual(response.status_code, 200)
        organization.refresh_from_db()
        self.assertTrue(organization.is_active)

    # Ensures DELETE soft-deactivates instead of removing the database row.
    def test_delete_soft_deactivates_organization(self):
        organization = Organization.objects.create(**self.payload)
        url = reverse('organization:organization_detail', args=[organization.id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        organization.refresh_from_db()
        self.assertFalse(organization.is_active)
        self.assertTrue(Organization.objects.filter(id=organization.id).exists())

    # Verifies clients may supply a valid UUID for new organizations.
    def test_can_create_organization_with_uuid_id(self):
        organization_id = uuid4()
        payload = {**self.payload, 'id': str(organization_id)}

        response = self.post_json(reverse('organization:organization_collection'), payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['id'], str(organization_id))

    # Confirms the organization page renders the dynamic form/table shell.
    def test_organization_page_renders_dynamic_shell(self):
        response = self.client.get(reverse('organization:organization_page'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="organizationForm"')
        self.assertContains(response, 'id="organizationRows"')
        self.assertContains(response, 'Reactivate')
        self.assertContains(response, 'loadOrganizations()')


# Covers office form organization selection behavior.
class OfficeFormTests(TestCase):
    def test_organization_dropdown_excludes_inactive_organizations(self):
        active = Organization.objects.create(
            name='Active City',
            short_name='Active',
            province_code='3001',
            address='Bulacan',
            seal_path='seals/active.png',
        )
        inactive = Organization.objects.create(
            name='City of Malolos',
            short_name='Malolos',
            province_code='3001',
            address='Malolos, Bulacan',
            seal_path='seals/malolos.png',
            is_active=False,
        )

        form = OfficeForm()

        self.assertIn(active, form.fields['organization'].queryset)
        self.assertNotIn(inactive, form.fields['organization'].queryset)

    def test_office_cannot_be_created_under_inactive_organization(self):
        organization = Organization.objects.create(
            name='City of Malolos',
            short_name='Malolos',
            province_code='3000',
            address='Malolos, Bulacan',
            seal_path='seals/malolos.png',
            is_active=False,
        )

        form = OfficeForm(data={
            'organization': str(organization.pk),
            'name': 'Planning Office',
            'office_code': 'PLO',
            'office_type': Office.OfficeType.DEPARTMENT,
            'office_head': '',
            'office_head_title': '',
            'is_active': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('organization', form.errors)

    def test_office_rejects_duplicate_name_in_same_organization(self):
        organization = Organization.objects.create(
            name='City of Malolos',
            short_name='Malolos',
            province_code='3000',
            address='Malolos, Bulacan',
            seal_path='seals/malolos.png',
        )
        Office.objects.create(
            organization=organization,
            name='Planning Office',
            office_code='PLO',
            office_type=Office.OfficeType.DEPARTMENT,
        )

        form = OfficeForm(data={
            'organization': str(organization.pk),
            'name': 'planning office',
            'office_code': 'PLOX',
            'office_type': Office.OfficeType.DEPARTMENT,
            'office_head': '',
            'office_head_title': '',
            'is_active': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_office_rejects_invalid_code_and_head_title(self):
        organization = Organization.objects.create(
            name='City of Malolos',
            short_name='Malolos',
            province_code='3000',
            address='Malolos, Bulacan',
            seal_path='seals/malolos.png',
        )

        form = OfficeForm(data={
            'organization': str(organization.pk),
            'name': 'Planning Office',
            'office_code': 'pito1',
            'office_type': Office.OfficeType.DEPARTMENT,
            'office_head': '',
            'office_head_title': 'Unit Head',
            'is_active': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('office_code', form.errors)
        self.assertIn('office_head_title', form.errors)

    def test_office_version_rejects_invalid_date_order_and_duplicate_version(self):
        organization = Organization.objects.create(
            name='City of Malolos',
            short_name='Malolos',
            province_code='3000',
            address='Malolos, Bulacan',
            seal_path='seals/malolos.png',
        )
        office = Office.objects.create(
            organization=organization,
            name='Planning Office',
            office_code='PLO',
            office_type=Office.OfficeType.DEPARTMENT,
        )
        legal_basis = LegalBasis.objects.create(
            reference_type='resolution',
            reference_number='2026-001',
            effectivity_date=date(2026, 1, 1),
        )
        OfficeVersion.objects.create(
            office_id=office,
            version_no=1,
            effective_start_date=date(2026, 1, 1),
            legal_basis=legal_basis,
            change_description='Initial structure',
        )

        duplicate = OfficeVersion(
            office_id=office,
            version_no=1,
            effective_start_date=date(2026, 2, 1),
            effective_end_date=date(2026, 1, 31),
            legal_basis=legal_basis,
            change_description='Duplicate version',
        )

        with self.assertRaisesMessage(Exception, 'Version number already exists for this office.'):
            duplicate.full_clean()


# Covers office hierarchy rendering and JSON create behavior.
class OfficeHierarchyTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Provincial Information Technology Office',
            short_name='PITO',
            province_code='3000',
            address='Capitol Compound',
            seal_path='seals/pito.png',
        )

    def create_office(self, **kwargs):
        defaults = {
            'organization': self.organization,
            'name': 'PITO Department',
            'office_code': 'PITO',
            'office_type': Office.OfficeType.DEPARTMENT,
        }
        defaults.update(kwargs)
        return Office.objects.create(**defaults)

    def test_viewing_office_hierarchy_page_excludes_inactive_offices(self):
        department = self.create_office()
        active_division = self.create_office(
            parent_office=department,
            name='Existing Division',
            office_code='EXDIV',
            office_type=Office.OfficeType.DIVISION,
            office_head_title=Office.HEAD_TITLE_OFFICER_IN_CHARGE,
        )
        self.create_office(
            parent_office=department,
            name='Inactive Division',
            office_code='INACTIVE',
            office_type=Office.OfficeType.DIVISION,
            is_active=False,
        )

        response = self.client.get(
            reverse('organization:office_hierarchy', args=[department.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, department.name)
        self.assertContains(response, active_division.name)
        self.assertNotContains(response, 'Inactive Division')

    def test_hierarchy_index_shows_empty_state_without_offices(self):
        response = self.client.get(reverse('organization:office_hierarchy_index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No office hierarchy records yet.')
        self.assertContains(
            response,
            'Click New Unit to create the first office, division, or unit.',
        )

    def test_hierarchy_page_renders_database_records_only(self):
        department = self.create_office()

        response = self.client.get(
            reverse('organization:office_hierarchy', args=[department.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, department.name)
        self.assertContains(response, 'No child offices under this office yet.')

    def test_create_office_json_endpoint(self):
        user = User.objects.create_user(username='office-admin', password='test-pass')
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='organization',
                codename='add_office',
            )
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('organization:office_create'),
            data=json.dumps({
                'organization': str(self.organization.pk),
                'name': 'Database Management Division',
                'office_code': 'DMD',
                'office_type': Office.OfficeType.DEPARTMENT,
                'office_head': '',
                'office_head_title': '',
                'is_active': True,
            }),
            content_type='application/json',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['office']['level_no'], 1)
