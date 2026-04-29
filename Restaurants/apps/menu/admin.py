from django.contrib import admin
from .models import Alimentosbebidas

# Register your models here.
@admin.register(Alimentosbebidas)
class AlimentosbebidasAdmin(admin.ModelAdmin):
    list_display =('id_alimentosbebidas','nombre','descripcion','costo','activo')
    search_fields = ('nombre','descripcion')
    list_filter = ('activo','costo',)
    list_editable = ('costo','activo',)
    ordering = ('nombre',)
    list_per_page = 20
