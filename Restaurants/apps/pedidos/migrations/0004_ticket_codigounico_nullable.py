from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0003_detalleticket_id'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE ticket MODIFY COLUMN codigounico INT NULL;",
            reverse_sql="ALTER TABLE ticket MODIFY COLUMN codigounico INT NOT NULL;",
        ),
    ]
