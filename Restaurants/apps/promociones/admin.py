from django.contrib import admin
from .models import Restricciones, Promocion

# Register your models here.
@admin.register(Restricciones)
class RestriccionesAdmin(admin.ModelAdmin):
    list_display =('id_restriccion','nombre','consumo_minimo_para_aplicar')
    search_fields = ('nombre',)
    ordering = ('nombre',)
    list_per_page = 20

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display =('id_promocion','nombre','descripcion','porcentaje_a_reducir','id_restriccion')
    search_fields = ('nombre','descripcion',)
    list_filter = ('id_restriccion',)
    ordering = ('nombre',)
    list_per_page = 20