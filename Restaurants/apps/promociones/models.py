from datetime import date

from django.db import models


TIPO_PROMO_CHOICES = [
    ('TOTAL',     'Total ticket'),
    ('CATEGORIA', 'Por categoría'),
    ('COMBO',     'Combo de categorías'),
]

TIPO_RESTRICCION_CHOICES = [
    ('ITEMS',   'Piezas en pedido'),
    ('VISITAS', 'Compras anteriores'),
    ('MONTO',   'Monto gastado ($)'),
]


# Create your models here.
class Restricciones(models.Model):
    id_restriccion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=25)
    consumo_minimo_para_aplicar = models.IntegerField()
    tipo_restriccion = models.CharField(
        max_length=10,
        choices=TIPO_RESTRICCION_CHOICES,
        default='ITEMS',
    )

    class Meta:
        db_table = 'restricciones'
        verbose_name = 'Restriccion'
        verbose_name_plural = 'Restricciones'


class Promocion(models.Model):
    id_promocion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=200)
    porcentaje_a_reducir = models.DecimalField(max_digits=5, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=TIPO_PROMO_CHOICES, default='TOTAL')
    # Solo relevante cuando tipo='CATEGORIA'
    categoria = models.ForeignKey(
        'menu.Categoria',
        models.SET_NULL,
        null=True,
        blank=True,
        related_name='promociones',
    )
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


class PromocionComboItem(models.Model):
    """Cada fila define una categoría + mínimo requerido para un combo."""
    id = models.AutoField(primary_key=True)
    promocion = models.ForeignKey(
        Promocion, models.CASCADE,
        related_name='combo_items',
    )
    categoria = models.ForeignKey(
        'menu.Categoria', models.CASCADE,
        related_name='combo_items',
    )
    cantidad_minima = models.IntegerField(default=1)

    class Meta:
        db_table = 'promocion_combo_item'
        verbose_name = 'Componente de combo'
        verbose_name_plural = 'Componentes de combo'
