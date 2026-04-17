from django.db import models

# Create your models here.
class Restricciones(models.Model):
    id_restriccion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=25)
    consumo_minimo_para_aplicar = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'restricciones'
        verbose_name = 'Restriccion'
        verbose_name_plural = 'Restricciones'


class Promocion(models.Model):
    id_promocion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=200)
    porcentaje_a_reducir = models.DecimalField(max_digits=5, decimal_places=2)
    id_restriccion = models.ForeignKey(Restricciones, models.DO_NOTHING, db_column='id_restriccion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'promocion'
        verbose_name = 'Promocion'
        verbose_name_plural = 'Promociones'
