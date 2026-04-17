from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
]

admin.site.site_header = 'Restaurants Admin'
admin.site.site_title = "Panel de Restaurants"
admin.site.index_title = "Bienvenido al Panel de Administración de Restaurants de Django"