import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='office',
            options={'ordering': ['level_no', 'name']},
        ),
        migrations.AlterField(
            model_name='office',
            name='organization_id',
            field=models.ForeignKey(
                db_column='organization_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='offices',
                to='organization.organization',
            ),
        ),
        migrations.AlterField(
            model_name='office',
            name='parent_office_id',
            field=models.ForeignKey(
                blank=True,
                db_column='parent_office_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='child_offices',
                to='organization.office',
            ),
        ),
        migrations.AlterField(
            model_name='office',
            name='office_type',
            field=models.CharField(
                choices=[
                    ('Department', 'Department'),
                    ('Division', 'Division'),
                    ('Unit', 'Unit'),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name='office',
            name='office_head_title',
            field=models.CharField(
                choices=[
                    ('DH', 'Department Head'),
                    ('OIC', 'Officer In Charge'),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name='officeversion',
            name='office_id',
            field=models.ForeignKey(
                db_column='office_id',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='versions',
                to='organization.office',
            ),
        ),
    ]
