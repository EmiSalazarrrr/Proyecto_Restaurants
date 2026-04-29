# Generated manually to keep the unmanaged detalleticket table in sync.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0002_alter_detalleticket_options_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE detalleticket "
                "ADD COLUMN IF NOT EXISTS id int NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST"
            ),
            reverse_sql=(
                "ALTER TABLE detalleticket "
                "DROP COLUMN IF EXISTS id"
            ),
        ),
    ]
