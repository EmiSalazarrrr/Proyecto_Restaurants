from django.contrib import admin
from django.urls import include, path

from apps.pedidos import views as pedidos_views
from apps.promociones import views as promociones_views
from apps.usuarios import views as usuarios_views

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', usuarios_views.login_view, name='login'),
    path('logout/', usuarios_views.logout_view, name='logout'),
    path('registro/', usuarios_views.registro_view, name='registro'),
    path('menu-admin/', views.menu_admin_view, name='menu_admin'),
    path('menu-cliente/', usuarios_views.menu_cliente_view, name='menu_cliente'),
    path('historial/', usuarios_views.historial_view, name='historial'),
    path('alimentos-bebidas/', include('apps.menu.urls')),
    path('atender-mesa/', pedidos_views.atender_mesa, name='atender_mesa'),
    path('guardar-ticket/', pedidos_views.guardar_ticket, name='guardar_ticket'),
    path('tickets/', pedidos_views.lista_tickets, name='lista_tickets'),
    path('promociones/', promociones_views.promociones_view, name='promociones'),
    path('metricas/', views.metricas_view, name='metricas'),
]

admin.site.site_header = 'Restaurants Admin'
admin.site.site_title = "Panel de Restaurants"
admin.site.index_title = "Bienvenido al Panel de Administración de Restaurants de Django"
