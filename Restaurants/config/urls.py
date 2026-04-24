from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('menu-admin/', views.menu_admin_view, name='menu_admin'),
    path('menu-cliente/', views.menu_cliente_view, name='menu_cliente'),
    path('agregar-ticket/', views.agregar_ticket_view, name='agregar_ticket'),
    path('historial/', views.historial_view, name='historial'),
    path('alimentos-bebidas/', views.alimentos_bebidas_view, name='alimentos_bebidas'),
    path('atender-mesa/', views.atender_mesa_view, name='atender_mesa'),
    path('promociones/', views.promociones_view, name='promociones'),
    path('metricas/', views.metricas_view, name='metricas'),
    path('agregar-alimento/', views.agregar_alimento_view, name='agregar_alimento'),
    path('modificar-alimento/', views.modificar_alimento_view, name='modificar_alimento'),
    path('eliminar-alimento/', views.eliminar_alimento_view, name='eliminar_alimento'),
    path('agregar-promocion/', views.agregar_promocion_view, name='agregar_promocion'),
    path('consultar-promocion/', views.consultar_promocion_view, name='consultar_promocion'),
    path('editar-promocion/', views.editar_promocion_view, name='editar_promocion'),
    path('eliminar-promocion/', views.eliminar_promocion_view, name='eliminar_promocion'),
    path('configurar-restricciones/', views.configurar_restricciones_view, name='configurar_restricciones'),
]

admin.site.site_header = 'Restaurants Admin'
admin.site.site_title = "Panel de Restaurants"
admin.site.index_title = "Bienvenido al Panel de Administración de Restaurants de Django"