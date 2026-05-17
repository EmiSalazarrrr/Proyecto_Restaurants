from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promociones', '0003_promocion_tipo_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='restricciones',
            name='tipo_restriccion',
            field=models.CharField(
                choices=[
                    ('ITEMS',   'Piezas en pedido'),
                    ('VISITAS', 'Compras anteriores'),
                    ('MONTO',   'Monto gastado ($)'),
                ],
                default='ITEMS',
                max_length=10,
            ),
        ),
    ]
