from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_alimentos, name='lista_alimentos'),
    path('agregar/', views.agregar_alimento, name='agregar_alimento'),
    path('modificar/', views.modificar_alimento, name='modificar_alimento'),
    path('modificar/<int:id>/', views.modificar_alimento, name='modificar_alimento_id'),
    path('eliminar/', views.eliminar_alimento, name ='eliminar_alimento'),
    path('eliminar/<int:id>/', views.eliminar_alimento, name='eliminar_alimento_id'),

]