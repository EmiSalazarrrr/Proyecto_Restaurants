from django.db import models
from django.utils import timezone
from apps.usuarios.models import Cliente
from apps.menu.models import Alimentosbebidas
from apps.promociones.models import Promocion

# Create your models here.
class Productopedido(models.Model):
    id_productopedido = models.AutoField(primary_key=True)
    id_alimentosbebidas = models.ForeignKey(Alimentosbebidas, models.DO_NOTHING, db_column='id_alimentosbebidas', blank=True, null=True)

    def __str__(self):
        if self.id_alimentosbebidas:
            return f"{self.id_productopedido} - {self.id_alimentosbebidas.nombre}"
        return f"{self.id_productopedido} - (sin producto)"

    class Meta:
        db_table = 'productopedido'
        verbose_name = 'Producto Pedido'
        verbose_name_plural = 'Productos Pedidos'



class Ticket(models.Model):
    id_ticket = models.AutoField(primary_key=True)
    precio_final = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    canjeado = models.IntegerField(blank=True, null=True, default=0)
    id_promocion = models.ForeignKey(Promocion, models.DO_NOTHING, db_column='id_promocion', blank=True, null=True)
    nombre_usuario = models.ForeignKey(Cliente, models.DO_NOTHING, db_column='nombre_usuario', blank=True, null=True)
    codigounico = models.IntegerField(unique=True)
    metodo_pago = models.CharField(max_length=10, default='pendiente')
    pago_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pago_tarjeta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    efectivo_recibido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cambio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagado = models.BooleanField(default=False)

    def calcular_total(self):
        total = 0
        for detalle in self.detalleticket_set.all():
            if detalle.id_productopedido and detalle.id_productopedido.id_alimentosbebidas:
                total += detalle.id_productopedido.id_alimentosbebidas.costo
        if self.id_promocion and self.id_promocion.porcentaje_a_reducir:
            descuento = total * (self.id_promocion.porcentaje_a_reducir / 100)
            total -= descuento
        return total

    def __str__(self):
        usuario = self.nombre_usuario.nombre_usuario if self.nombre_usuario else 'sin usuario'
        return f"Ticket {self.id_ticket} - Usuario: {usuario} - Precio Final: {self.precio_final}"

    class Meta:
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'


class Detalleticket(models.Model):
    id = models.AutoField(primary_key=True)
    id_ticket = models.ForeignKey(Ticket, models.DO_NOTHING, db_column='id_ticket', blank=False, null=False)
    id_productopedido = models.ForeignKey(Productopedido, models.DO_NOTHING, db_column='id_productopedido', blank=True, null=True)

    def __str__(self):
        ticket_id = self.id_ticket.id_ticket if self.id_ticket else '?'
        producto_id = self.id_productopedido.id_productopedido if self.id_productopedido else 'sin producto'
        return f"Detalle Ticket - Ticket ID: {ticket_id} - Producto Pedido ID: {producto_id}"

    class Meta:
        db_table = 'detalleticket'
        verbose_name = 'Detalle Ticket'
        verbose_name_plural = 'Detalles Tickets'
