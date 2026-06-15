from django.db import migrations


def sync_salary_step_editability(apps, schema_editor):
    SalaryGradeStep = apps.get_model('plantilla', 'SalaryGradeStep')
    SalaryGradeStep.objects.filter(source='imported').update(is_editable=False)
    SalaryGradeStep.objects.filter(source='manual').update(is_editable=True)


class Migration(migrations.Migration):

    dependencies = [
        ('plantilla', '0006_salary_schedule'),
    ]

    operations = [
        migrations.RunPython(
            sync_salary_step_editability,
            migrations.RunPython.noop,
        ),
    ]
