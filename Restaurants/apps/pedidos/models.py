from django.db import models
from apps.usuarios.models import Cliente
from apps.menu.models import Alimentosbebidas
from apps.promociones.models import Promocion

# Create your models here.
class Productopedido(models.Model):
    id_productopedido = models.AutoField(primary_key=True)
    id_alimentosbebidas = models.ForeignKey(Alimentosbebidas, models.DO_NOTHING, db_column='id_alimentosbebidas', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'productopedido'
        verbose_name = 'Producto Pedido'
        verbose_name_plural = 'Productos Pedidos'


class Ticket(models.Model):
    id_ticket = models.AutoField(primary_key=True)
    precio_final = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField()
    canjeado = models.IntegerField(blank=True, null=True)
    id_promocion = models.ForeignKey(Promocion, models.DO_NOTHING, db_column='id_promocion', blank=True, null=True)
    nombre_usuario = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='nombre_usuario', blank=True, null=True)
    codigounico = models.IntegerField(unique=True)

    class Meta:
        managed = False
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'


class Detalleticket(models.Model):
    id_ticket = models.ForeignKey(Ticket, models.DO_NOTHING, db_column='id_ticket', primary_key=True, blank=True, null=False)
    id_productopedido = models.ForeignKey(Productopedido, models.DO_NOTHING, db_column='id_productopedido', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalleticket'
        verbose_name = 'Detalle Ticket'
        verbose_name_plural = 'Detalles Tickets'