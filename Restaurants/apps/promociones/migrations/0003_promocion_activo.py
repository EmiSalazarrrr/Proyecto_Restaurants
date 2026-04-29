# Generated manually to keep the unmanaged promocion table in sync.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("promociones", "0002_alter_promocion_options_alter_restricciones_options"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE promocion "
                "ADD COLUMN IF NOT EXISTS activo tinyint(1) NOT NULL DEFAULT 1"
            ),
            reverse_sql=(
                "ALTER TABLE promocion "
                "DROP COLUMN IF EXISTS activo"
            ),
        ),
    ]
