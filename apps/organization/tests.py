import json
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse

from .models import Organization


# Covers organization API create, list, update, deactivate, and page rendering.
class OrganizationCrudTests(TestCase):
    # Shared valid payload for organization API tests.
    def setUp(self):
        self.payload = {
            'name': 'City Government of Malolos',
            'short_name': 'Malolos City',
            'province_code': 'BUL',
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

    # Confirms inactive organizations are hidden unless requested.
    def test_list_excludes_inactive_by_default(self):
        Organization.objects.create(**self.payload)
        Organization.objects.create(
            name='Inactive City',
            short_name='Inactive',
            province_code='BUL',
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
        self.assertContains(response, 'loadOrganizations()')
