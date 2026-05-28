import apps.organization.models
from django.db import migrations, models
from django.db.models import Q


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
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.CheckConstraint(
                condition=Q(province_code__regex=r'^\d{4}$'),
                name='organization_province_code_4_digits',
            ),
        ),
    ]
