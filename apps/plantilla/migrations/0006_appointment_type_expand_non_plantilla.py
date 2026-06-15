import django.core.validators
from django.db import migrations, models


def normalize_non_plantilla_employee_types(apps, schema_editor):
    NonPlantillaEmployee = apps.get_model('plantilla', 'NonPlantillaEmployee')
    NonPlantillaEmployee.objects.filter(employee_type='JO').update(employee_type='JOB_ORDER')
    NonPlantillaEmployee.objects.filter(employee_type='casual').update(employee_type='CASUAL')


def restore_non_plantilla_employee_types(apps, schema_editor):
    NonPlantillaEmployee = apps.get_model('plantilla', 'NonPlantillaEmployee')
    NonPlantillaEmployee.objects.filter(employee_type='JOB_ORDER').update(employee_type='JO')
    NonPlantillaEmployee.objects.filter(employee_type='CASUAL').update(employee_type='casual')


class Migration(migrations.Migration):

    dependencies = [
        ('plantilla', '0005_salarygrade_salarygradestep'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='appointment_type',
            field=models.CharField(
                choices=[
                    ('PERMANENT', 'Permanent'),
                    ('COTERMINOUS_ELECTIVE', 'Coterminous / Elective Official'),
                ],
                default='PERMANENT',
                max_length=30,
            ),
        ),
        migrations.RunPython(
            normalize_non_plantilla_employee_types,
            restore_non_plantilla_employee_types,
        ),
        migrations.AlterField(
            model_name='nonplantillaemployee',
            name='employee_type',
            field=models.CharField(
                choices=[
                    ('JOB_ORDER', 'Job Order'),
                    ('CONTRACT_OF_SERVICE', 'Contract of Service'),
                    ('CASUAL', 'Casual'),
                    ('CONTRACTUAL', 'Contractual'),
                    ('PROJECT_BASED', 'Project-Based'),
                    ('TEMPORARY', 'Temporary'),
                    ('EMERGENCY_WORKER', 'Emergency Worker'),
                    ('SUBSTITUTE', 'Substitute'),
                    ('OUTSOURCED_PERSONNEL', 'Outsourced Personnel'),
                    ('CONSULTANT', 'Consultant'),
                ],
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='nonplantillaemployee',
            name='duration_unit',
            field=models.CharField(
                choices=[
                    ('days', 'Days'),
                    ('weeks', 'Weeks'),
                    ('months', 'Months'),
                    ('years', 'Years'),
                ],
                default='months',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='position_title',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='funding_source',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='reference_number',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='duties_responsibilities',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='compensation_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='rate_basis',
            field=models.CharField(
                blank=True,
                choices=[
                    ('DAILY', 'Daily'),
                    ('MONTHLY', 'Monthly'),
                    ('LUMP_SUM', 'Lump Sum'),
                    ('PER_DELIVERABLE', 'Per Deliverable'),
                ],
                default='',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='salary_grade',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(33),
                ],
            ),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='salary_step',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(8),
                ],
            ),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='service_provider',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='consultancy_title',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='contract_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='nonplantillaemployee',
            name='work_assignment',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
