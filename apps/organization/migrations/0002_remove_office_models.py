from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    'DROP TABLE IF EXISTS "organization_office_version" CASCADE;',
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    'DROP TABLE IF EXISTS "organization_office" CASCADE;',
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.DeleteModel(
                    name='OfficeVersion',
                ),
                migrations.DeleteModel(
                    name='Office',
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name='organization',
            options={'ordering': ['name']},
        ),
    ]
