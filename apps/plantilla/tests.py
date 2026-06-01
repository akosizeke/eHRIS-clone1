import json
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.organization.models import Office, Organization

from .forms import ItemForm
from .models import Item, NonPlantillaEmployee


class PlantillaValidationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='City of Malolos',
            short_name='Malolos',
            province_code='3000',
            address='Malolos, Bulacan',
            seal_path='seals/malolos.png',
        )
        self.office = Office.objects.create(
            organization=self.organization,
            name='Human Resource Management Office',
            office_code='HRMO',
            office_type=Office.OfficeType.DEPARTMENT,
        )
        self.payload = {
            'item_number': 'hrmo-001',
            'position_title': 'Administrative Officer IV',
            'salary_grade': 15,
            'office': str(self.office.pk),
            'employment_type': 'permanent',
            'funding_source': 'PS',
            'position_status': 'vacant',
            'legalbasis': '',
        }

    def test_item_number_is_normalized_to_uppercase(self):
        item = Item.objects.create(
            item_number='hrmo-001',
            position_title='Administrative Officer IV',
            salary_grade=15,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )

        self.assertEqual(item.item_number, 'HRMO-001')

    def test_item_number_rejects_invalid_format(self):
        form = ItemForm(data={**self.payload, 'item_number': 'HRMO 001!'})

        self.assertFalse(form.is_valid())
        self.assertIn('item_number', form.errors)

    def test_salary_grade_must_be_within_one_to_thirty_three(self):
        form = ItemForm(data={**self.payload, 'salary_grade': 34})

        self.assertFalse(form.is_valid())
        self.assertIn('salary_grade', form.errors)

    def test_filled_position_requires_employee_name(self):
        form = ItemForm(data={**self.payload, 'position_status': 'filled'})

        self.assertFalse(form.is_valid())
        self.assertIn('employee_name', form.errors)

    def test_position_title_must_be_unique_per_office_case_insensitive(self):
        Item.objects.create(
            item_number='HRMO-001',
            position_title='Administrative Officer IV',
            salary_grade=15,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )

        form = ItemForm(data={
            **self.payload,
            'item_number': 'HRMO-002',
            'position_title': 'administrative officer iv',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('position_title', form.errors)

    def test_duplicate_item_number_is_rejected_after_uppercase_normalization(self):
        Item.objects.create(
            item_number='hrmo-001',
            position_title='Administrative Officer IV',
            salary_grade=15,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )

        duplicate = Item(
            item_number='HRMO-001',
            position_title='Administrative Officer V',
            salary_grade=18,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_json_create_uses_json_body(self):
        response = self.client.post(
            reverse('plantilla:create'),
            data=json.dumps(self.payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['item_number'], 'HRMO-001')
        self.assertTrue(Item.objects.filter(item_number='HRMO-001').exists())

    def test_non_plantilla_eligibility_uses_duration(self):
        employee = NonPlantillaEmployee.objects.create(
            name='Juan Dela Cruz',
            employee_type='JO',
            office=self.office,
            duration_value=2,
            duration_unit='years',
            start_date=date(2024, 1, 1),
        )

        self.assertEqual(employee.service_months, 24)
        self.assertTrue(employee.eligible_for_permanent)

    def test_non_plantilla_end_date_must_not_precede_start_date(self):
        employee = NonPlantillaEmployee(
            name='Maria Santos',
            employee_type='casual',
            office=self.office,
            duration_value=6,
            duration_unit='months',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 31),
        )

        with self.assertRaises(ValidationError):
            employee.full_clean()
