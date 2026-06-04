import apps.organization.models
import django.db.models.deletion
import re
from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


def clean_existing_offices(apps, schema_editor):
    Office = apps.get_model('organization', 'Office')

    used_names = {}
    for office in Office.objects.order_by('organization_id', 'created_at', 'id'):
        key = (office.organization_id, (office.name or '').strip().lower())
        count = used_names.get(key, 0) + 1
        used_names[key] = count

        if count > 1:
            base_name = (office.name or 'Office').strip() or 'Office'
            candidate = f'{base_name} ({count})'
            suffix = count
            while Office.objects.filter(
                organization_id=office.organization_id,
                name__iexact=candidate,
            ).exclude(pk=office.pk).exists():
                suffix += 1
                candidate = f'{base_name} ({suffix})'
            office.name = candidate
            office.save(update_fields=['name'])

    used_codes = {}
    for office in Office.objects.order_by('organization_id', 'created_at', 'id'):
        org_id = office.organization_id
        used_codes.setdefault(org_id, set())
        code = re.sub(r'[^A-Z]', '', (office.office_code or '').upper())
        if not code:
            code = 'OFFICE'

        candidate = code[:100]
        suffix_number = 1
        while candidate.lower() in used_codes[org_id]:
            suffix = _alpha_suffix(suffix_number)
            candidate = f'{code[:100 - len(suffix)]}{suffix}'
            suffix_number += 1

        used_codes[org_id].add(candidate.lower())
        if office.office_code != candidate:
            office.office_code = candidate
            office.save(update_fields=['office_code'])


def _alpha_suffix(number):
    letters = ''
    while number:
        number, remainder = divmod(number - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('employee_profile', '0001_initial'),
        ('organization', '0007_organization_validation'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='office',
            name='uniq_office_code_per_org',
        ),
        migrations.AlterField(
            model_name='office',
            name='name',
            field=models.CharField(
                max_length=255,
                validators=[apps.organization.models.office_name_validator],
            ),
        ),
        migrations.AlterField(
            model_name='office',
            name='office_code',
            field=models.CharField(
                max_length=100,
                validators=[apps.organization.models.office_code_validator],
            ),
        ),
        migrations.AlterField(
            model_name='office',
            name='office_head_title',
            field=models.CharField(
                blank=True,
                choices=[
                    ('DH', 'Department Head'),
                    ('OIC', 'Officer In Charge'),
                ],
                default='',
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name='officeversion',
            name='version_no',
            field=models.PositiveIntegerField(),
        ),
        migrations.RunPython(clean_existing_offices, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='office',
            constraint=models.UniqueConstraint(
                Lower('office_code'),
                models.F('organization'),
                condition=~Q(office_code=''),
                name='uniq_office_code_per_org_ci',
            ),
        ),
        migrations.AddConstraint(
            model_name='office',
            constraint=models.UniqueConstraint(
                Lower('name'),
                models.F('organization'),
                name='uniq_office_name_per_org_ci',
            ),
        ),
        migrations.AddConstraint(
            model_name='office',
            constraint=models.CheckConstraint(
                condition=Q(office_code__regex=r'^[A-Z]+$'),
                name='office_code_uppercase_letters',
            ),
        ),
        migrations.AddConstraint(
            model_name='officeversion',
            constraint=models.UniqueConstraint(
                fields=['office_id', 'version_no'],
                name='uniq_office_version_no_per_office',
            ),
        ),
        migrations.AddConstraint(
            model_name='officeversion',
            constraint=models.CheckConstraint(
                condition=Q(version_no__gte=1),
                name='office_version_no_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='officeversion',
            constraint=models.CheckConstraint(
                condition=(
                    Q(effective_end_date__isnull=True)
                    | Q(effective_end_date__gt=models.F('effective_start_date'))
                ),
                name='office_version_end_after_start',
            ),
        ),
    ]
