from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0006_ticket_pago"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="pagado",
            field=models.BooleanField(default=False),
        ),
    ]
