from django.db import models
from apps.usuarios.models import Cliente
from apps.menu.models import Alimentosbebidas
from apps.promociones.models import Promocion

# Create your models here.
class Productopedido(models.Model):
    id_productopedido = models.AutoField(primary_key=True)
    id_alimentosbebidas = models.ForeignKey(Alimentosbebidas, models.DO_NOTHING, db_column='id_alimentosbebidas', blank=True, null=True)

    def __str__(self):
        return f"{self.id_productopedido} - {self.id_alimentosbebidas.nombre}"

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

    def calcular_total(self):
        total = sum(detalle.id_productopedido.id_alimentosbebidas.costo for detalle in self.detalleticket_set.all())
        if self.id_promocion and self.id_promocion.porcentaje_a_reducir:
            descuento = total * (self.id_promocion.porcentaje_a_reducir / 100)
            total -= descuento
        return total

    def __str__(self):
        return f"Ticket {self.id_ticket} - Usuario: {self.nombre_usuario.nombre_usuario} - Precio Final: {self.precio_final}"
    class Meta:
        managed = False
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'


class Detalleticket(models.Model):
    id = models.AutoField(primary_key=True)
    id_ticket = models.ForeignKey(Ticket, models.DO_NOTHING, db_column='id_ticket', blank=True, null=False)
    id_productopedido = models.ForeignKey(Productopedido, models.DO_NOTHING, db_column='id_productopedido', blank=True, null=True)

    def __str__(self):
        return f"Detalle Ticket - Ticket ID: {self.id_ticket.id_ticket} - Producto Pedido ID: {self.id_productopedido.id_productopedido}"

    class Meta:
        managed = False
        db_table = 'detalleticket'
        verbose_name = 'Detalle Ticket'
        verbose_name_plural = 'Detalles Tickets'