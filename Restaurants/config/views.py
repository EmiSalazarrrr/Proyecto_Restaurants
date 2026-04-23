from django.shortcuts import render

def login_view(request):
    return render(request, 'login.html')

def registro_view(request):
    return render(request, 'registro.html')

def menu_admin_view(request):
    return render(request, 'menu_admin.html')

def menu_cliente_view(request):
    return render(request, 'menu_cliente.html')

def agregar_ticket_view(request):
    return render(request, 'agregar_ticket.html')

def historial_view(request):
    return render(request, 'historial.html')

def alimentos_bebidas_view(request):
    return render(request, 'alimentos_bebidas.html')

def atender_mesa_view(request):
    return render(request, 'atender_mesa.html')

def promociones_view(request):
    return render(request, 'promociones.html')

def metricas_view(request):
    return render(request, "metricas.html")