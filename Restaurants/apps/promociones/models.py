from datetime import date

from django.db import models


# Create your models here.
class Restricciones(models.Model):
    id_restriccion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=25)
    consumo_minimo_para_aplicar = models.IntegerField()

    class Meta:
        db_table = 'restricciones'
        verbose_name = 'Restriccion'
        verbose_name_plural = 'Restricciones'


class Promocion(models.Model):
    id_promocion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=200)
    porcentaje_a_reducir = models.DecimalField(max_digits=5, decimal_places=2)
    id_restriccion = models.ForeignKey(Restricciones, models.DO_NOTHING, db_column='id_restriccion', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    @property
    def esta_vigente(self):
        hoy = date.today()
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        return True

    @property
    def esta_vencida(self):
        return bool(self.fecha_fin and date.today() > self.fecha_fin)

    @property
    def vigencia_display(self):
        if not self.fecha_inicio and not self.fecha_fin:
            return "Sin fecha límite"
        inicio = self.fecha_inicio.strftime('%d/%m') if self.fecha_inicio else '—'
        fin = self.fecha_fin.strftime('%d/%m/%Y') if self.fecha_fin else '—'
        return f"{inicio} – {fin}"

    def __str__(self):
        return f"{self.nombre} - {self.descripcion}"

    class Meta:
        db_table = 'promocion'
        verbose_name = 'Promocion'
        verbose_name_plural = 'Promociones'
