# Generated manually to keep the unmanaged alimentosbebidas table in sync.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0002_alter_alimentosbebidas_options"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE alimentosbebidas "
                "ADD COLUMN IF NOT EXISTS activo tinyint(1) NOT NULL DEFAULT 1"
            ),
            reverse_sql=(
                "ALTER TABLE alimentosbebidas "
                "DROP COLUMN IF EXISTS activo"
            ),
        ),
    ]
