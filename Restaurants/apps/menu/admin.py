from django.contrib import admin
from .models import Alimentosbebidas

# Register your models here.
@admin.register(Alimentosbebidas)
class AlimentosbebidasAdmin(admin.ModelAdmin):
    list_display =('id_alimentosbebidas','nombre','descripcion','costo')
    search_fields = ('nombre','descripcion')
    list_filter = ('costo',)
    list_editable = ('costo',)
    ordering = ('nombre',)
    list_per_page = 20
