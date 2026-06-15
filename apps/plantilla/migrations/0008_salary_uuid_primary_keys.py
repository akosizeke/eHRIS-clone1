import uuid

from django.db import migrations, models
import django.db.models.deletion


def _constraint_names(cursor, table_name, constraint_type, referenced_table_name=None):
    params = [table_name, constraint_type]
    referenced_filter = ''
    if referenced_table_name:
        referenced_filter = 'AND confrelid = to_regclass(%s)'
        params.append(referenced_table_name)

    cursor.execute(
        f"""
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = to_regclass(%s)
          AND contype = %s
          {referenced_filter}
        """,
        params,
    )
    return [row[0] for row in cursor.fetchall()]


def _drop_constraint(schema_editor, table_name, constraint_name):
    schema_editor.execute(
        f'ALTER TABLE {schema_editor.quote_name(table_name)} '
        f'DROP CONSTRAINT IF EXISTS {schema_editor.quote_name(constraint_name)}'
    )


def convert_salary_ids_to_uuid(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        raise RuntimeError('This migration expects PostgreSQL.')

    cursor = schema_editor.connection.cursor()

    cursor.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'salary_grade'
          AND column_name = 'id'
        """
    )
    row = cursor.fetchone()
    if row and row[0] == 'uuid':
        return

    schema_editor.execute('ALTER TABLE salary_grade ADD COLUMN uuid_id uuid')
    schema_editor.execute('ALTER TABLE salary_grade_step ADD COLUMN uuid_id uuid')
    schema_editor.execute('ALTER TABLE salary_grade_step ADD COLUMN salary_grade_uuid uuid')

    cursor.execute('SELECT id FROM salary_grade')
    grade_id_map = {}
    for (old_id,) in cursor.fetchall():
        new_id = uuid.uuid4()
        grade_id_map[old_id] = new_id
        cursor.execute(
            'UPDATE salary_grade SET uuid_id = %s WHERE id = %s',
            [new_id, old_id],
        )

    cursor.execute('SELECT id, salary_grade_id FROM salary_grade_step')
    for old_id, old_grade_id in cursor.fetchall():
        cursor.execute(
            """
            UPDATE salary_grade_step
            SET uuid_id = %s,
                salary_grade_uuid = %s
            WHERE id = %s
            """,
            [uuid.uuid4(), grade_id_map[old_grade_id], old_id],
        )

    schema_editor.execute('ALTER TABLE salary_grade ALTER COLUMN uuid_id SET NOT NULL')
    schema_editor.execute('ALTER TABLE salary_grade_step ALTER COLUMN uuid_id SET NOT NULL')
    schema_editor.execute('ALTER TABLE salary_grade_step ALTER COLUMN salary_grade_uuid SET NOT NULL')

    for constraint_name in _constraint_names(cursor, 'salary_grade_step', 'f', 'salary_grade'):
        _drop_constraint(schema_editor, 'salary_grade_step', constraint_name)
    _drop_constraint(schema_editor, 'salary_grade_step', 'unique_step_per_salary_grade')

    for constraint_name in _constraint_names(cursor, 'salary_grade_step', 'p'):
        _drop_constraint(schema_editor, 'salary_grade_step', constraint_name)
    for constraint_name in _constraint_names(cursor, 'salary_grade', 'p'):
        _drop_constraint(schema_editor, 'salary_grade', constraint_name)

    schema_editor.execute('ALTER TABLE salary_grade_step DROP COLUMN salary_grade_id')
    schema_editor.execute('ALTER TABLE salary_grade_step DROP COLUMN id')
    schema_editor.execute('ALTER TABLE salary_grade DROP COLUMN id')

    schema_editor.execute('ALTER TABLE salary_grade RENAME COLUMN uuid_id TO id')
    schema_editor.execute('ALTER TABLE salary_grade_step RENAME COLUMN uuid_id TO id')
    schema_editor.execute('ALTER TABLE salary_grade_step RENAME COLUMN salary_grade_uuid TO salary_grade_id')

    schema_editor.execute('ALTER TABLE salary_grade ADD CONSTRAINT salary_grade_pkey PRIMARY KEY (id)')
    schema_editor.execute('ALTER TABLE salary_grade_step ADD CONSTRAINT salary_grade_step_pkey PRIMARY KEY (id)')
    schema_editor.execute(
        """
        ALTER TABLE salary_grade_step
        ADD CONSTRAINT salary_grade_step_salary_grade_id_fk
        FOREIGN KEY (salary_grade_id)
        REFERENCES salary_grade(id)
        DEFERRABLE INITIALLY DEFERRED
        """
    )
    schema_editor.execute(
        """
        ALTER TABLE salary_grade_step
        ADD CONSTRAINT unique_step_per_salary_grade
        UNIQUE (salary_grade_id, step_number)
        """
    )
    schema_editor.execute(
        """
        CREATE INDEX IF NOT EXISTS salary_grade_step_salary_grade_id_idx
        ON salary_grade_step (salary_grade_id)
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ('plantilla', '0007_sync_salary_step_editability'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    convert_salary_ids_to_uuid,
                    migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='salarygrade',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='salarygrade',
                    name='grade_number',
                    field=models.PositiveIntegerField(),
                ),
                migrations.AlterField(
                    model_name='salarygradestep',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='salarygradestep',
                    name='salary_grade',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='steps', to='plantilla.salarygrade'),
                ),
                migrations.AlterField(
                    model_name='salarygradestep',
                    name='step_number',
                    field=models.PositiveSmallIntegerField(),
                ),
                migrations.AlterField(
                    model_name='salarygradestep',
                    name='amount',
                    field=models.PositiveIntegerField(),
                ),
            ],
        ),
    ]
