import random
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.menu.models import Alimentosbebidas
from apps.promociones.models import Promocion
from apps.usuarios.models import Cliente
from apps.usuarios.views import login_required

from .models import Detalleticket, Productopedido, Ticket


def _generar_codigo_unico():
    while True:
        codigo = random.randint(100000, 999999)
        if not Ticket.objects.filter(codigounico=codigo).exists():
            return codigo


def _promocion_aplicable(cliente, total_productos):
    promociones = Promocion.objects.filter(activo=True).select_related("id_restriccion")
    compras_previas = Ticket.objects.filter(nombre_usuario=cliente).count()
    elegibles = []

    for promocion in promociones:
        restriccion = promocion.id_restriccion
        minimo = getattr(restriccion, "consumo_minimo_para_aplicar", 0) or 0
        nombre_restriccion = ((restriccion.nombre if restriccion else "") or "").lower()

        if "frecuente" in nombre_restriccion:
            cumple = compras_previas >= minimo
        else:
            cumple = total_productos >= minimo

        if cumple:
            elegibles.append(promocion)

    if not elegibles:
        return None

    return max(elegibles, key=lambda promo: promo.porcentaje_a_reducir or 0)


@login_required(role="admin")
def atender_mesa(request):
    alimentos = Alimentosbebidas.objects.filter(activo=True).order_by("nombre")
    clientes = Cliente.objects.filter(id_tipo_de_usuario__tipo_de_usuario__iexact="Cliente").order_by("nombre")
    return render(
        request,
        "atender_mesa.html",
        {
            "alimentos": alimentos,
            "clientes": clientes,
        },
    )


@login_required(role="admin")
def guardar_ticket(request):
    if request.method != "POST":
        return redirect("atender_mesa")

    nombre_usuario = request.POST.get("cliente")
    productos_ids = request.POST.getlist("producto_id[]")
    cantidades = request.POST.getlist("cantidad[]")

    if not nombre_usuario or not productos_ids:
        messages.error(request, "Selecciona un cliente y al menos un producto.")
        return redirect("atender_mesa")

    try:
        cliente = Cliente.objects.get(nombre_usuario=nombre_usuario)
    except Cliente.DoesNotExist:
        messages.error(request, "El cliente seleccionado no existe.")
        return redirect("atender_mesa")

    lineas = []
    total_productos = 0

    for producto_id, cantidad in zip(productos_ids, cantidades):
        if not producto_id:
            continue
        try:
            alimento = Alimentosbebidas.objects.get(id_alimentosbebidas=producto_id, activo=True)
            cantidad_int = max(int(cantidad), 1)
        except (Alimentosbebidas.DoesNotExist, TypeError, ValueError):
            continue
        lineas.append((alimento, cantidad_int))
        total_productos += cantidad_int

    if not lineas:
        messages.error(request, "No se pudo construir el ticket con los datos enviados.")
        return redirect("atender_mesa")

    promocion = _promocion_aplicable(cliente, total_productos)
    ticket = Ticket.objects.create(
        precio_final=Decimal("0.00"),
        fecha=timezone.now(),
        canjeado=0,
        id_promocion=promocion,
        nombre_usuario=cliente,
        codigounico=_generar_codigo_unico(),
    )

    for alimento, cantidad in lineas:
        for _ in range(cantidad):
            producto_pedido = Productopedido.objects.create(id_alimentosbebidas=alimento)
            Detalleticket.objects.create(id_ticket=ticket, id_productopedido=producto_pedido)

    ticket.precio_final = ticket.calcular_total()
    ticket.save(update_fields=["precio_final"])

    if promocion:
        messages.success(
            request,
            f"Ticket #{ticket.id_ticket} guardado con la promocion {promocion.nombre}.",
        )
    else:
        messages.success(request, f"Ticket #{ticket.id_ticket} guardado exitosamente.")
    return redirect("lista_tickets")


@login_required(role="admin")
def lista_tickets(request):
    tickets = (
        Ticket.objects.select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
        .order_by("-fecha")
    )
    total_ingresos = tickets.aggregate(total=Sum("precio_final"))["total"] or 0
    total_canjeados = tickets.filter(canjeado=1).count()
    total_tickets = tickets.count()
    return render(
        request,
        "lista_tickets.html",
        {
            "tickets": tickets,
            "total_ingresos": total_ingresos,
            "total_canjeados": total_canjeados,
            "total_tickets": total_tickets,
        },
    )
