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

def agregar_alimento_view(request):
    return render(request, "agregar_alimento.html")

def modificar_alimento_view(request):
    return render(request, "modificar_alimento.html")

def eliminar_alimento_view(request):
    return render(request, "eliminar_alimento.html")

def agregar_promocion_view(request):
    return render(request, "agregar_promocion.html")

def consultar_promocion_view(request):
    return render(request, "consultar_promocion.html")

def editar_promocion_view(request):
    return render(request, "editar_promocion.html")

def eliminar_promocion_view(request):
    return render(request, "eliminar_promocion.html")

def configurar_restricciones_view(request):
    return render(request, "configurar_restricciones.html")
