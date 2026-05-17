from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_populate_categorias'),
        ('promociones', '0002_promocion_fecha_fin_promocion_fecha_inicio'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocion',
            name='tipo',
            field=models.CharField(
                choices=[('TOTAL', 'Total ticket'), ('CATEGORIA', 'Por categoría')],
                default='TOTAL',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='promocion',
            name='categoria',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='promociones',
                to='menu.categoria',
            ),
        ),
    ]
