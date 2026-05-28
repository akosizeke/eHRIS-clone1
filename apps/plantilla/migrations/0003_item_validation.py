import apps.plantilla.models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
from django.db.models import Q
from django.db.models.functions import Lower


def uppercase_item_numbers(apps, schema_editor):
    Item = apps.get_model('plantilla', 'Item')
    for item in Item.objects.exclude(item_number=''):
        normalized = item.item_number.strip().upper()
        if item.item_number != normalized:
            item.item_number = normalized
            item.save(update_fields=['item_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('plantilla', '0002_alter_item_employment_type'),
    ]

    operations = [
        migrations.RunPython(uppercase_item_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='item',
            name='item_number',
            field=models.CharField(
                max_length=50,
                unique=True,
                validators=[apps.plantilla.models.item_number_validator],
            ),
        ),
        migrations.AlterField(
            model_name='item',
            name='salary_grade',
            field=models.PositiveIntegerField(
                validators=[MinValueValidator(1), MaxValueValidator(33)],
            ),
        ),
        migrations.AddConstraint(
            model_name='item',
            constraint=models.UniqueConstraint(
                Lower('position_title'),
                models.F('office'),
                name='uniq_plantilla_position_title_per_office_ci',
            ),
        ),
        migrations.AddConstraint(
            model_name='item',
            constraint=models.CheckConstraint(
                condition=Q(salary_grade__gte=1, salary_grade__lte=33),
                name='plantilla_salary_grade_1_33',
            ),
        ),
        migrations.AddConstraint(
            model_name='item',
            constraint=models.CheckConstraint(
                condition=Q(item_number__regex=r'^[A-Z0-9-]+$'),
                name='plantilla_item_number_format',
            ),
        ),
    ]
