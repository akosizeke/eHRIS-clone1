import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('employee_number', models.CharField(max_length=50, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, default='', max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('suffix', models.CharField(blank=True, default='', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Employee Profile',
                'verbose_name_plural': 'Employee Profiles',
                'db_table': 'employee_profile',
                'ordering': ['last_name', 'first_name'],
            },
        ),
    ]
