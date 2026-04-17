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
]