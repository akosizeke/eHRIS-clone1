import json
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.organization.models import Office, Organization

from .forms import ItemForm, NonPlantillaEmployeeForm
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
            'appointment_type': Item.AppointmentType.PERMANENT,
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
            appointment_type=Item.AppointmentType.PERMANENT,
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
            appointment_type=Item.AppointmentType.PERMANENT,
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
            appointment_type=Item.AppointmentType.PERMANENT,
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
        self.assertEqual(response.json()['appointment_type'], Item.AppointmentType.PERMANENT)
        self.assertTrue(Item.objects.filter(item_number='HRMO-001').exists())

    def test_create_permanent_position(self):
        form = ItemForm(data=self.payload)

        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.appointment_type, Item.AppointmentType.PERMANENT)

    def test_create_coterminous_elective_position(self):
        form = ItemForm(data={
            **self.payload,
            'item_number': 'HRMO-002',
            'position_title': 'Executive Assistant',
            'appointment_type': Item.AppointmentType.COTERMINOUS_ELECTIVE,
        })

        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.get_appointment_type_display(), 'Coterminous / Elective Official')

    def test_invalid_appointment_type_is_rejected(self):
        form = ItemForm(data={**self.payload, 'appointment_type': 'COTERMINOUS'})

        self.assertFalse(form.is_valid())
        self.assertIn('appointment_type', form.errors)

    def test_vacant_position_clears_employee_name(self):
        form = ItemForm(data={**self.payload, 'employee_name': 'Juan Dela Cruz'})

        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.employee_name, '')

    def test_editing_appointment_type(self):
        item = Item.objects.create(
            item_number='HRMO-010',
            position_title='Administrative Aide VI',
            appointment_type=Item.AppointmentType.PERMANENT,
            salary_grade=6,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )

        response = self.client.post(reverse('plantilla:edit', args=[item.pk]), data={
            'item_number': item.item_number,
            'employee_name': '',
            'position_title': item.position_title,
            'appointment_type': Item.AppointmentType.COTERMINOUS_ELECTIVE,
            'salary_grade': item.salary_grade,
            'office': str(self.office.pk),
            'position_status': 'vacant',
            'duties_responsibilities': '',
            'legalbasis': '',
        })

        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.appointment_type, Item.AppointmentType.COTERMINOUS_ELECTIVE)

    def test_filtering_by_appointment_type(self):
        Item.objects.create(
            item_number='HRMO-020',
            position_title='Permanent Position',
            appointment_type=Item.AppointmentType.PERMANENT,
            salary_grade=10,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )
        coterminous = Item.objects.create(
            item_number='HRMO-021',
            position_title='Coterminous Position',
            appointment_type=Item.AppointmentType.COTERMINOUS_ELECTIVE,
            salary_grade=11,
            office=self.office,
            employment_type='permanent',
            funding_source='PS',
            position_status='vacant',
        )

        response = self.client.get(
            reverse('plantilla:list'),
            {'tab': 'plantilla', 'appointment_type': Item.AppointmentType.COTERMINOUS_ELECTIVE},
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        item_numbers = {item['item_number'] for item in response.json()['plantilla']}
        self.assertEqual(item_numbers, {coterminous.item_number})

    def test_non_plantilla_eligibility_uses_duration(self):
        employee = NonPlantillaEmployee.objects.create(
            name='Juan Dela Cruz',
            employee_type=NonPlantillaEmployee.EmployeeType.JOB_ORDER,
            office=self.office,
            duration_value=2,
            duration_unit='years',
            start_date=date(2024, 1, 1),
            compensation_rate=750,
            rate_basis=NonPlantillaEmployee.RateBasis.DAILY,
        )

        self.assertEqual(employee.service_months, 24)
        self.assertTrue(employee.eligible_for_permanent)

    def test_non_plantilla_end_date_must_not_precede_start_date(self):
        employee = NonPlantillaEmployee(
            name='Maria Santos',
            employee_type=NonPlantillaEmployee.EmployeeType.CASUAL,
            office=self.office,
            duration_value=6,
            duration_unit='months',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 31),
            salary_grade=4,
            salary_step=1,
        )

        with self.assertRaises(ValidationError):
            employee.full_clean()

    def non_plantilla_payload(self, employee_type, **overrides):
        payload = {
            'name': f'{employee_type} Employee',
            'employee_type': employee_type,
            'office': str(self.office.pk),
            'position_title': 'Administrative Support',
            'funding_source': 'MOOE',
            'reference_number': '',
            'duties_responsibilities': 'Assigned work.',
            'duration_value': 6,
            'duration_unit': 'months',
            'start_date': '2026-01-01',
            'end_date': '2026-06-30',
        }
        payload.update(overrides)
        return payload

    def assert_non_plantilla_form_valid(self, employee_type, **overrides):
        form = NonPlantillaEmployeeForm(
            data=self.non_plantilla_payload(employee_type, **overrides)
        )

        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def test_create_job_order_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.JOB_ORDER,
            compensation_rate='750.00',
            rate_basis=NonPlantillaEmployee.RateBasis.DAILY,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.JOB_ORDER)

    def test_create_contract_of_service_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.CONTRACT_OF_SERVICE,
            compensation_rate='50000.00',
            rate_basis=NonPlantillaEmployee.RateBasis.LUMP_SUM,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.CONTRACT_OF_SERVICE)

    def test_create_casual_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.CASUAL,
            salary_grade=4,
            salary_step=1,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.CASUAL)

    def test_create_contractual_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.CONTRACTUAL,
            salary_grade=8,
            salary_step=2,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.CONTRACTUAL)

    def test_create_project_based_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.PROJECT_BASED,
            salary_grade=12,
            salary_step=1,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.PROJECT_BASED)

    def test_create_temporary_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.TEMPORARY,
            salary_grade=5,
            salary_step=3,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.TEMPORARY)

    def test_create_emergency_worker_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.EMERGENCY_WORKER,
            work_assignment='Flood response operations',
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.EMERGENCY_WORKER)

    def test_create_substitute_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.SUBSTITUTE,
            salary_grade=7,
            salary_step=1,
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.SUBSTITUTE)

    def test_create_outsourced_personnel_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.OUTSOURCED_PERSONNEL,
            service_provider='ABC Services',
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.OUTSOURCED_PERSONNEL)

    def test_create_consultant_record(self):
        employee = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.CONSULTANT,
            consultancy_title='Records Management Consultant',
            contract_amount='100000.00',
        )

        self.assertEqual(employee.employee_type, NonPlantillaEmployee.EmployeeType.CONSULTANT)

    def test_non_plantilla_rejects_required_conditional_fields(self):
        form = NonPlantillaEmployeeForm(data=self.non_plantilla_payload(
            NonPlantillaEmployee.EmployeeType.CONTRACT_OF_SERVICE,
        ))

        self.assertFalse(form.is_valid())
        self.assertIn('compensation_rate', form.errors)
        self.assertIn('rate_basis', form.errors)

    def test_non_plantilla_rejects_invalid_employee_type(self):
        form = NonPlantillaEmployeeForm(data=self.non_plantilla_payload('INVALID_TYPE'))

        self.assertFalse(form.is_valid())
        self.assertIn('employee_type', form.errors)

    def test_existing_job_order_and_casual_canonical_values_remain_valid(self):
        job_order = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.JOB_ORDER,
            compensation_rate='750.00',
            rate_basis=NonPlantillaEmployee.RateBasis.DAILY,
        )
        casual = self.assert_non_plantilla_form_valid(
            NonPlantillaEmployee.EmployeeType.CASUAL,
            name='Casual Employee',
            salary_grade=4,
            salary_step=1,
        )

        self.assertEqual(job_order.get_employee_type_display(), 'Job Order')
        self.assertEqual(casual.get_employee_type_display(), 'Casual')
