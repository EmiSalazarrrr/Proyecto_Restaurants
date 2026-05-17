from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id_categoria', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=50, unique=True)),
                ('icono', models.CharField(default='🍽️', max_length=10)),
                ('orden', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
                'db_table': 'categoria',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.AddField(
            model_name='alimentosbebidas',
            name='categoria',
            field=models.ForeignKey(
                blank=True,
                db_column='id_categoria',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='menu.categoria',
            ),
        ),
    ]
