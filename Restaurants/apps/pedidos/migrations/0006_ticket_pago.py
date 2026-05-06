from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0005_backfill_codigounico_required"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="metodo_pago",
            field=models.CharField(default="pendiente", max_length=10),
        ),
        migrations.AddField(
            model_name="ticket",
            name="pago_efectivo",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="ticket",
            name="pago_tarjeta",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="ticket",
            name="efectivo_recibido",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="ticket",
            name="cambio",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
