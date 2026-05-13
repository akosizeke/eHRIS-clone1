import json

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Office, Organization


class OfficeHierarchyTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Provincial Information Technology Office',
            short_name='PITO',
            province_code='PITO',
            address='Capitol Compound',
            seal_path='seals/pito.png',
        )

    def create_office(self, **kwargs):
        defaults = {
            'organization': self.organization,
            'name': 'PITO',
            'office_code': 'PITO',
            'office_type': Office.OfficeType.DEPARTMENT,
        }
        defaults.update(kwargs)
        return Office.objects.create(**defaults)

    def test_creating_top_level_office_sets_level_one(self):
        office = self.create_office()

        self.assertEqual(office.level_no, 1)
        self.assertIsNone(office.parent_office)

    def test_creating_division_under_department_sets_level_two(self):
        department = self.create_office()
        division = self.create_office(
            parent_office=department,
            name='Existing Division',
            office_code='EXDIV',
            office_type=Office.OfficeType.DIVISION,
        )

        self.assertEqual(division.level_no, 2)
        self.assertEqual(division.parent_office, department)

    def test_creating_unit_under_division_sets_level_three(self):
        department = self.create_office()
        division = self.create_office(
            parent_office=department,
            name='Existing Division',
            office_code='EXDIV',
            office_type=Office.OfficeType.DIVISION,
        )
        unit = self.create_office(
            parent_office=division,
            name='Existing Unit',
            office_code='EXUNIT',
            office_type=Office.OfficeType.UNIT,
        )

        self.assertEqual(unit.level_no, 3)
        self.assertEqual(unit.parent_office, division)

    def test_prevents_self_parent(self):
        office = self.create_office()
        office.parent_office = office
        office.office_type = Office.OfficeType.DIVISION

        with self.assertRaises(ValidationError):
            office.full_clean()

    def test_viewing_office_hierarchy_page_excludes_inactive_offices(self):
        department = self.create_office()
        active_division = self.create_office(
            parent_office=department,
            name='Existing Division',
            office_code='EXDIV',
            office_type=Office.OfficeType.DIVISION,
            office_head_title='OIC',
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
        user.user_permissions.add(Permission.objects.get(codename='add_office'))
        self.client.force_login(user)

        response = self.client.post(
            reverse('organization:office_create'),
            data=json.dumps({
                'organization': str(self.organization.pk),
                'name': 'PITO',
                'office_code': 'PITO',
                'office_type': Office.OfficeType.DEPARTMENT,
                'is_active': True,
            }),
            content_type='application/json',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['office']['level_no'], 1)
