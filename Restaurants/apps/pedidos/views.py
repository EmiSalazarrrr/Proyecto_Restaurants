from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from apps.menu.models import Alimentosbebidas
from apps.usuarios.models import Cliente
from .models import Ticket, Productopedido, Detalleticket
import random

# Create your views here.
def atender_mesa(request):
    alimentos = Alimentosbebidas.objects.all()
    Clientes = Clientes.objects.all()
    return render(request, 'atender_mesa.html',{
        'alimentos': alimentos,
        'Clientes': Clientes
    })

def guardar_ticket(request):
    if request.method == 'POST':
        nombre_usuario = request.POST.get('cliente')
        productos_ids = request.POST.getlist('productos')
        cantidades = request.POST.getlist('cantidad[]')

        cliente = Cliente.objects.get(nombre_usuario=nombre_usuario)
        # Crear el ticket
        ticket = Ticket.objects.create(
            precio_final = 0,
            fecha=timezone.now(),
            canjeado=0,
            nombre_usuario=cliente,
            codigounico=random.randint(100000, 999999)
        )

        # Crear productos y detalles
        for producto_id, cantidad in zip(productos_ids, cantidades):
            alimento = Alimentosbebidas.objects.get(id_alimentosbebidas=producto_id)
            cantidad = int(cantidad)
            for _ in range(cantidad):
                producto_pedido = Productopedido.objects.create(id_alimentosbebidas=alimento)
                Detalleticket.objects.create(id_ticket=ticket, id_productopedido=producto_pedido)
        # Calcular el precio final
        ticket.precio_final = ticket.calcular_total()
        ticket.save()

        messages.success(request, f'Ticket #{ticket.id_ticket} guardado exitosamente.')
        return redirect('lista_tickets')
    return redirect ('atender_mesa')

def lista_tickets(request):
    tickets = Ticket.objects.all()
    total_ingresos = sum(t.precio_final for t in tickets)
    total_canjeados = tickets.filter(canjeado=1).count()
    return render(request,'lista_tickets.html',{
        'tickets': tickets,
        'total_ingresos': total_ingresos,
        'total_canjeados': total_canjeados
    })