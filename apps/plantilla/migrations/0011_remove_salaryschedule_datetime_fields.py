from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plantilla', '0010_salaryschedule_inactive_date'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE salary_schedule '
                'DROP COLUMN IF EXISTS effective_at, '
                'DROP COLUMN IF EXISTS inactive_at'
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
