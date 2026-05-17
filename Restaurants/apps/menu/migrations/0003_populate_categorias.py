from django.db import migrations

CATEGORIAS = [
    (1,  'Entradas / Botanas',   '🥗'),
    (2,  'Sopas y Caldos',       '🍲'),
    (3,  'Platillo Fuerte',      '🍽️'),
    (4,  'Mariscos',             '🐟'),
    (5,  'Ensaladas',            '🥬'),
    (6,  'Pizzas y Pastas',      '🍕'),
    (7,  'Postres',              '🍰'),
    (8,  'Bebidas',              '🥤'),
    (9,  'Bebidas Alcoholicas',  '🍺'),
    (10, 'Desayunos',            '☕'),
]


def forward(apps, schema_editor):
    Categoria = apps.get_model('menu', 'Categoria')
    for orden, nombre, icono in CATEGORIAS:
        Categoria.objects.get_or_create(nombre=nombre, defaults={'icono': icono, 'orden': orden})


def backward(apps, schema_editor):
    Categoria = apps.get_model('menu', 'Categoria')
    Categoria.objects.filter(nombre__in=[n for _, n, _ in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0002_categoria_alimentosbebidas_categoria'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
