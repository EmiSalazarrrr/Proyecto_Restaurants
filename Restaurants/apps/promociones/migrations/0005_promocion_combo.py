import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_populate_categorias'),
        ('promociones', '0004_restricciones_tipo'),
    ]

    operations = [
        # Actualizar choices del campo tipo en Promocion
        migrations.AlterField(
            model_name='promocion',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('TOTAL',     'Total ticket'),
                    ('CATEGORIA', 'Por categoría'),
                    ('COMBO',     'Combo de categorías'),
                ],
                default='TOTAL',
                max_length=20,
            ),
        ),
        # Nueva tabla para componentes de combo
        migrations.CreateModel(
            name='PromocionComboItem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad_minima', models.IntegerField(default=1)),
                ('promocion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='combo_items',
                    to='promociones.promocion',
                )),
                ('categoria', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='combo_items',
                    to='menu.categoria',
                )),
            ],
            options={'db_table': 'promocion_combo_item',
                     'verbose_name': 'Componente de combo',
                     'verbose_name_plural': 'Componentes de combo'},
        ),
    ]
