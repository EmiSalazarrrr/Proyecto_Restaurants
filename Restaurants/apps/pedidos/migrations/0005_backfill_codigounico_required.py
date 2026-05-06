import random

from django.db import migrations, models


def backfill_codigos(apps, schema_editor):
    Ticket = apps.get_model("pedidos", "Ticket")
    usados = set(
        Ticket.objects
        .exclude(codigounico__isnull=True)
        .values_list("codigounico", flat=True)
    )

    for ticket in Ticket.objects.filter(codigounico__isnull=True):
        while True:
            codigo = random.randint(100000, 999999)
            if codigo not in usados:
                usados.add(codigo)
                ticket.codigounico = codigo
                ticket.save(update_fields=["codigounico"])
                break


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0004_ticket_codigounico_nullable"),
    ]

    operations = [
        migrations.RunPython(backfill_codigos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="ticket",
            name="codigounico",
            field=models.IntegerField(unique=True),
        ),
    ]
