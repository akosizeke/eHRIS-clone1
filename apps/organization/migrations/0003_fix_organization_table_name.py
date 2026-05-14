from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_remove_office_models'),
    ]

    operations = [
        migrations.RunSQL(
            '''
            DO $$
            BEGIN
                IF to_regclass('organization') IS NULL
                   AND to_regclass('organization_organization') IS NOT NULL THEN
                    ALTER TABLE "organization_organization" RENAME TO "organization";
                END IF;
            END $$;
            ''',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
