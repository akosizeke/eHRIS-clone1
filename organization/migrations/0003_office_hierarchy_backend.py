import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_fix_office_fk_columns'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS organization_office (
                        id uuid NOT NULL PRIMARY KEY,
                        name varchar(255) NOT NULL,
                        office_code varchar(100) NOT NULL DEFAULT '',
                        office_type varchar(100) NOT NULL,
                        level_no integer NOT NULL,
                        office_head uuid NULL,
                        office_head_title varchar(100) NOT NULL DEFAULT '',
                        is_active boolean NOT NULL,
                        created_at timestamp with time zone NOT NULL,
                        modified_at timestamp with time zone NOT NULL,
                        organization_id uuid NOT NULL,
                        parent_office_id uuid NULL,
                        CONSTRAINT organization_office_organization_id_fk
                            FOREIGN KEY (organization_id)
                            REFERENCES organization (id)
                            DEFERRABLE INITIALLY DEFERRED,
                        CONSTRAINT organization_office_parent_office_id_fk
                            FOREIGN KEY (parent_office_id)
                            REFERENCES organization_office (id)
                            DEFERRABLE INITIALLY DEFERRED
                    );

                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'organization_office'
                              AND column_name = 'organization_id_id'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'organization_office'
                              AND column_name = 'organization_id'
                        ) THEN
                            ALTER TABLE organization_office
                            RENAME COLUMN organization_id_id TO organization_id;
                        END IF;

                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'organization_office'
                              AND column_name = 'parent_office_id_id'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'organization_office'
                              AND column_name = 'parent_office_id'
                        ) THEN
                            ALTER TABLE organization_office
                            RENAME COLUMN parent_office_id_id TO parent_office_id;
                        END IF;
                    END $$;

                    ALTER TABLE organization_office
                    ALTER COLUMN office_code SET DEFAULT '',
                    ALTER COLUMN office_head_title SET DEFAULT '';

                    CREATE INDEX IF NOT EXISTS organization_office_organization_id_idx
                        ON organization_office (organization_id);

                    CREATE INDEX IF NOT EXISTS organization_office_parent_office_id_idx
                        ON organization_office (parent_office_id);

                    CREATE UNIQUE INDEX IF NOT EXISTS uniq_office_code_per_org
                        ON organization_office (organization_id, office_code)
                        WHERE NOT (office_code = '');

                    CREATE TABLE IF NOT EXISTS organization_office_version (
                        id uuid NOT NULL PRIMARY KEY,
                        version_no integer NOT NULL,
                        effective_start_date date NOT NULL,
                        effective_end_date date NULL,
                        legal_basis uuid NOT NULL,
                        change_description text NOT NULL,
                        created_at timestamp with time zone NOT NULL,
                        modified_at timestamp with time zone NOT NULL,
                        office_id uuid NOT NULL,
                        CONSTRAINT organization_office_version_office_id_fk
                            FOREIGN KEY (office_id)
                            REFERENCES organization_office (id)
                            DEFERRABLE INITIALLY DEFERRED
                    );

                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'organization_office_version'
                              AND column_name = 'office_id_id'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'organization_office_version'
                              AND column_name = 'office_id'
                        ) THEN
                            ALTER TABLE organization_office_version
                            RENAME COLUMN office_id_id TO office_id;
                        END IF;
                    END $$;

                    CREATE INDEX IF NOT EXISTS organization_office_version_office_id_idx
                        ON organization_office_version (office_id);
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name='office',
                    old_name='organization_id',
                    new_name='organization',
                ),
                migrations.RenameField(
                    model_name='office',
                    old_name='parent_office_id',
                    new_name='parent_office',
                ),
                migrations.AlterField(
                    model_name='office',
                    name='organization',
                    field=models.ForeignKey(
                        db_column='organization_id',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='offices',
                        to='organization.organization',
                    ),
                ),
                migrations.AlterField(
                    model_name='office',
                    name='parent_office',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='parent_office_id',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='children',
                        to='organization.office',
                    ),
                ),
                migrations.AlterField(
                    model_name='office',
                    name='office_code',
                    field=models.CharField(blank=True, default='', max_length=100),
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
                    name='level_no',
                    field=models.PositiveIntegerField(default=1),
                ),
                migrations.AlterField(
                    model_name='office',
                    name='office_head_title',
                    field=models.CharField(blank=True, default='', max_length=100),
                ),
                migrations.AddConstraint(
                    model_name='office',
                    constraint=models.UniqueConstraint(
                        condition=models.Q(('office_code', ''), _negated=True),
                        fields=('organization', 'office_code'),
                        name='uniq_office_code_per_org',
                    ),
                ),
            ],
        ),
    ]
