import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee_profile', '0001_initial'),
        ('legal_basis', '0001_initial'),
        ('organization', '0004_alter_organization_options_office_officeversion_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='office',
            name='office_head',
            field=models.ForeignKey(
                blank=True,
                db_column='office_head_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='headed_offices',
                to='employee_profile.employeeprofile',
            ),
        ),
        migrations.AlterField(
            model_name='officeversion',
            name='legal_basis',
            field=models.ForeignKey(
                db_column='legal_basis_id',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='office_versions',
                to='legal_basis.legalbasis',
            ),
        ),
    ]
