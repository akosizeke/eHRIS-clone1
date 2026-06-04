import apps.organization.models
from django.db import migrations, models
from django.db.models import Q


def clean_existing_province_codes(apps, schema_editor):
    Organization = apps.get_model('organization', 'Organization')

    for organization in Organization.objects.all():
        digits = ''.join(char for char in (organization.province_code or '') if char.isdigit())
        if len(digits) == 4:
            cleaned = digits
        else:
            cleaned = '0000'

        if organization.province_code != cleaned:
            organization.province_code = cleaned
            organization.save(update_fields=['province_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_alter_organization_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(
                max_length=255,
                unique=True,
                validators=[apps.organization.models.organization_name_validator],
            ),
        ),
        migrations.AlterField(
            model_name='organization',
            name='short_name',
            field=models.CharField(
                max_length=100,
                unique=True,
                validators=[apps.organization.models.organization_name_validator],
            ),
        ),
        migrations.AlterField(
            model_name='organization',
            name='province_code',
            field=models.CharField(
                max_length=4,
                validators=[apps.organization.models.province_code_validator],
            ),
        ),
        migrations.AlterField(
            model_name='organization',
            name='address',
            field=models.TextField(
                validators=[apps.organization.models.address_validator],
            ),
        ),
        migrations.RunPython(clean_existing_province_codes, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.CheckConstraint(
                condition=Q(province_code__regex=r'^[0-9]{4}$'),
                name='organization_province_code_4_digits',
            ),
        ),
    ]
