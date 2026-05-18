from django.db import models


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    icono = models.CharField(max_length=10, default='🍽️')
    orden = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.icono} {self.nombre}"

    class Meta:
        db_table = 'categoria'
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['orden', 'nombre']


class Alimentosbebidas(models.Model):
    id_alimentosbebidas = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=200)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    nombre = models.CharField(unique=True, max_length=50)
    activo = models.BooleanField(default=True)
    categoria = models.ForeignKey(
        Categoria, models.SET_NULL,
        db_column='id_categoria', null=True, blank=True,
    )

    def __str__(self):
        return f"{self.nombre} - ${self.costo}"

    class Meta:
        db_table = 'alimentosbebidas'
        verbose_name = 'Alimento o Bebida'
        verbose_name_plural = 'Alimentos y Bebidas'
