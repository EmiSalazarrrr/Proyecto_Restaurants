from django.contrib import admin
from .models import Cliente, Perfiles

# Register your models here.
@admin.register(Perfiles)
class PerfilesAdmin(admin.ModelAdmin):
    list_display = ('id_tipo_de_usuario', 'tipo_de_usuario')
    search_fields = ('tipo_de_usuario',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display =('nombre_usuario','nombre','apellido_paterno','numero_celular','id_tipo_de_usuario')
    search_fields = ('nombre_usuario','nombre','apellido_paterno','numero_celular')
    list_filter = ('id_tipo_de_usuario',)