from django.db import migrations, models


def populate_inactive_dates(apps, schema_editor):
    SalarySchedule = apps.get_model('plantilla', 'SalarySchedule')
    schedules = list(SalarySchedule.objects.order_by('effective_date', 'name'))

    for index, schedule in enumerate(schedules[:-1]):
        next_schedule = schedules[index + 1]
        if schedule.effective_date < next_schedule.effective_date and not schedule.inactive_date:
            schedule.inactive_date = next_schedule.effective_date
            schedule.save(update_fields=['inactive_date'])


class Migration(migrations.Migration):

    dependencies = [
        ('plantilla', '0009_salaryschedule_unique_salary_schedule_effective_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='salaryschedule',
            name='inactive_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(populate_inactive_dates, migrations.RunPython.noop),
    ]
