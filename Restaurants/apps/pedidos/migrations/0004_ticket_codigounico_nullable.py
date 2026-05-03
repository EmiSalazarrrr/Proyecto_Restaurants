from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE ticket MODIFY COLUMN codigounico INT NULL;",
                    reverse_sql="ALTER TABLE ticket MODIFY COLUMN codigounico INT NOT NULL;",
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='ticket',
                    name='codigounico',
                    field=models.IntegerField(blank=True, null=True, unique=True),
                ),
            ],
        ),
    ]
