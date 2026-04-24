from django.contrib import admin
from django.urls import include, path
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
    path('promociones-lista/', views.promociones_view, name='promociones_web'),
    path('metricas/', views.metricas_view, name='metricas'),
    path('menu/', include('apps.menu.urls')),
    path('pedidos/', include('apps.pedidos.urls')),
    path('promociones/', include('apps.promociones.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
]

admin.site.site_header = 'Restaurants Admin'
admin.site.site_title = "Panel de Restaurants"
admin.site.index_title = "Bienvenido al Panel de Administración de Restaurants de Django"