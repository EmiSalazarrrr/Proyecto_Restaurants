from django.contrib import admin
from .models import Productopedido, Ticket, Detalleticket

# Register your models here.
@admin.register(Productopedido)
class ProductopedidoAdmin(admin.ModelAdmin):
    list_display= ('id_productopedido','id_alimentosbebidas')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display =('id_ticket','nombre_usuario','precio_final','fecha','canjeado','id_promocion','codigounico')
    search_fields = ('codigounico','nombre_usuario__nombreusuario')
    list_filter = ('canjeado','id_promocion')

@admin.register(Detalleticket)
class DetalleticketAdmin(admin.ModelAdmin):
    list_display =('id_ticket','id_productopedido')