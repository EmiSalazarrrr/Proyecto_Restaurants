from django.contrib import admin
from .models import Productopedido, Ticket, Detalleticket

# Register your models here.

class DetalleticketInline(admin.TabularInline):
    model = Detalleticket
    extra = 1
    can_delete = True
    verbose_name = 'Producto'
    verbose_name_plural = 'Productos del Ticket'

@admin.register(Productopedido)
class ProductopedidoAdmin(admin.ModelAdmin):
    list_display= ('id_productopedido','id_alimentosbebidas')
    search_fields = ('id_alimentosbebidas__nombre',)
    list_filter = ('id_productopedido',)
    list_per_page = 20

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display =('id_ticket','nombre_usuario','precio_final','fecha','canjeado','id_promocion','codigounico')
    search_fields = ('codigounico','nombre_usuario__nombreusuario')
    list_filter = ('canjeado','id_promocion','fecha',)
    ordering = ('-fecha',)
    list_per_page = 20
    inlines = [DetalleticketInline]
    readonly_fields = ('precio_final',)

    def productos_del_ticket(self, obj):
        productos = obj.detalleticket_set.all()
        if not productos:
            return "No hay productos asociados"
        nombres = [
            d.id_productopedido.id_alimentosbebidas.nombre
            for d in productos
            if d.id_productopedido and d.id_productopedido.id_alimentosbebidas
        ]
        return ", ".join(nombres) if nombres else "No hay productos asociados"
    productos_del_ticket.short_description = "Productos del Ticket"

@admin.register(Detalleticket)
class DetalleticketAdmin(admin.ModelAdmin):
    list_display =('id_ticket','id_productopedido')
    search_fields = ('id_ticket__codigounico','id_productopedido__id_alimentosbebidas__nombre')
    ordering = ('id_ticket',)
    list_per_page = 20