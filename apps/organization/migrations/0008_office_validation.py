import apps.organization.models
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


class Migration(migrations.Migration):

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
