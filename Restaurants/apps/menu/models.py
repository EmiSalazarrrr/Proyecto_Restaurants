from django.db import models

# Create your models here.
class Alimentosbebidas(models.Model):
    id_alimentosbebidas = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=200)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'alimentosbebidas'
        verbose_name = 'Alimento o Bebida'
        verbose_name_plural = 'Alimentos y Bebidas'