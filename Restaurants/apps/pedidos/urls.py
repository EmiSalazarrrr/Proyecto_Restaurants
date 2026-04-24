from django.urls import path
from . import views
urlpatterns = [
    path('atender-mesa/', views.atender_mesa, name='atender_mesa'),
    path('guardar-ticket/', views.guardar_ticket, name='guardar_ticket'),
    path('tickets/', views.lista_tickets, name='lista_tickets'),
]