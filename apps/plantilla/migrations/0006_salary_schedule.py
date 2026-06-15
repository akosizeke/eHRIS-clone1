import datetime
import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_default_salary_schedule(apps, schema_editor):
    SalarySchedule = apps.get_model('plantilla', 'SalarySchedule')
    SalaryGrade = apps.get_model('plantilla', 'SalaryGrade')

    schedule, _ = SalarySchedule.objects.get_or_create(
        name='Default Salary Schedule',
        defaults={
            'id': uuid.uuid4(),
            'description': 'Default container for existing salary grade data.',
            'effective_date': datetime.date(2026, 1, 1),
            'is_active': True,
        },
    )
    SalaryGrade.objects.filter(schedule__isnull=True).update(schedule=schedule)


def delete_empty_salary_steps(apps, schema_editor):
    SalaryGradeStep = apps.get_model('plantilla', 'SalaryGradeStep')
    SalaryGradeStep.objects.filter(amount__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plantilla', '0005_salarygrade_salarygradestep'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalarySchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('effective_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_salary_schedules', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='updated_salary_schedules', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Salary Schedule',
                'verbose_name_plural': 'Salary Schedules',
                'db_table': 'salary_schedule',
                'ordering': ['-effective_date', 'name'],
            },
        ),
        migrations.AlterModelOptions(
            name='salarygrade',
            options={
                'ordering': ['schedule', 'grade_number'],
                'verbose_name': 'Salary Grade',
                'verbose_name_plural': 'Salary Grades',
            },
        ),
        migrations.AddField(
            model_name='salarygrade',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='salarygrade',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_salary_grades', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='salarygrade',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='updated_salary_grades', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='salarygrade',
            name='schedule',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='salary_grades', to='plantilla.salaryschedule'),
        ),
        migrations.RunPython(create_default_salary_schedule, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='salarygrade',
            name='schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='salary_grades', to='plantilla.salaryschedule'),
        ),
        migrations.AlterField(
            model_name='salarygrade',
            name='grade_number',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddConstraint(
            model_name='salarygrade',
            constraint=models.UniqueConstraint(fields=('schedule', 'grade_number'), name='unique_salary_grade_per_schedule'),
        ),
        migrations.AlterModelOptions(
            name='salarygradestep',
            options={
                'ordering': ['salary_grade__grade_number', 'step_number'],
                'verbose_name': 'Salary Grade Step',
                'verbose_name_plural': 'Salary Grade Steps',
            },
        ),
        migrations.AddField(
            model_name='salarygradestep',
            name='is_editable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='salarygradestep',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_salary_grade_steps', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='salarygradestep',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='updated_salary_grade_steps', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='salarygradestep',
            name='imported_at',
        ),
        migrations.RunPython(delete_empty_salary_steps, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='salarygradestep',
            name='amount',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
