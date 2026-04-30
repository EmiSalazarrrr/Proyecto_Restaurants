import json
import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import localdate

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


def _get_estado(ticket, today):
    if ticket.canjeado == 1:
        return "canjeado"
    if ticket.fecha and localdate(ticket.fecha) < today:
        return "expirado"
    return "pendiente"


@login_required(role="admin")
def atender_mesa(request):
    alimentos = Alimentosbebidas.objects.filter(activo=True).order_by("nombre")
    clientes = Cliente.objects.filter(
        id_tipo_de_usuario__tipo_de_usuario__iexact="Cliente"
    ).order_by("nombre")
    return render(request, "atender_mesa.html", {"alimentos": alimentos, "clientes": clientes})


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
        codigounico=_generar_codigo_unico() if promocion else None,
    )

    for alimento, cantidad in lineas:
        for _ in range(cantidad):
            pp = Productopedido.objects.create(id_alimentosbebidas=alimento)
            Detalleticket.objects.create(id_ticket=ticket, id_productopedido=pp)

    ticket.precio_final = ticket.calcular_total()
    ticket.save(update_fields=["precio_final"])

    if promocion:
        messages.success(request, f"Ticket #{ticket.id_ticket} guardado con la promocion {promocion.nombre}.")
    else:
        messages.success(request, f"Ticket #{ticket.id_ticket} guardado exitosamente.")
    return redirect("lista_tickets")


@login_required(role="admin")
def lista_tickets(request):
    today = localdate()
    periodo = request.GET.get("periodo", "hoy")
    fecha_str = request.GET.get("fecha", "")
    desde_str = request.GET.get("desde", "")
    hasta_str = request.GET.get("hasta", "")

    if fecha_str:
        try:
            desde = hasta = date.fromisoformat(fecha_str)
            periodo = "fecha"
        except ValueError:
            desde = hasta = today
            periodo = "hoy"
    elif periodo == "semana":
        desde = today - timedelta(days=today.weekday())
        hasta = today
    elif periodo == "mes":
        desde = today.replace(day=1)
        hasta = today
    elif periodo == "anio":
        desde = today.replace(month=1, day=1)
        hasta = today
    elif periodo == "rango" and desde_str and hasta_str:
        try:
            desde = date.fromisoformat(desde_str)
            hasta = date.fromisoformat(hasta_str)
        except ValueError:
            desde = hasta = today
            periodo = "hoy"
    else:
        desde = hasta = today
        periodo = "hoy"

    tickets = (
        Ticket.objects
        .filter(fecha__date__gte=desde, fecha__date__lte=hasta)
        .exclude(canjeado=-1)
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
        .order_by("-fecha")
    )

    tickets_con_estado = [(t, _get_estado(t, today)) for t in tickets]

    count_pendiente = sum(1 for _, e in tickets_con_estado if e == "pendiente")
    count_canjeado = sum(1 for _, e in tickets_con_estado if e == "canjeado")
    count_expirado = sum(1 for _, e in tickets_con_estado if e == "expirado")
    total_ingresos = sum(t.precio_final for t, _ in tickets_con_estado)

    chart_data = json.dumps({
        "labels": ["Canjeados", "Pendientes", "Expirados"],
        "data": [count_canjeado, count_pendiente, count_expirado],
        "colors": ["#4cc970", "#c9a84c", "#f07a7a"],
    })

    return render(request, "lista_tickets.html", {
        "tickets_con_estado": tickets_con_estado,
        "total_tickets": len(tickets_con_estado),
        "total_ingresos": total_ingresos,
        "total_canjeados": count_canjeado,
        "total_expirados": count_expirado,
        "chart_data": chart_data,
        "periodo": periodo,
        "desde": desde,
        "hasta": hasta,
        "today": today,
        "fecha_str": fecha_str,
        "desde_str": desde_str,
        "hasta_str": hasta_str,
    })


@login_required(role="admin")
def modificar_ticket(request, id_ticket):
    ticket = get_object_or_404(
        Ticket.objects
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas"),
        id_ticket=id_ticket,
    )
    today = localdate()
    estado = _get_estado(ticket, today)

    if estado != "pendiente":
        messages.error(request, "Solo se pueden modificar tickets en estado Pendiente.")
        return redirect("lista_tickets")

    if request.method == "POST":
        productos_ids = request.POST.getlist("producto_id[]")
        cantidades = request.POST.getlist("cantidad[]")

        for producto_id, cantidad in zip(productos_ids, cantidades):
            if not producto_id:
                continue
            try:
                alimento = Alimentosbebidas.objects.get(id_alimentosbebidas=producto_id, activo=True)
                cantidad_int = max(int(cantidad), 1)
            except (Alimentosbebidas.DoesNotExist, TypeError, ValueError):
                continue
            for _ in range(cantidad_int):
                pp = Productopedido.objects.create(id_alimentosbebidas=alimento)
                Detalleticket.objects.create(id_ticket=ticket, id_productopedido=pp)

        total_productos = ticket.detalleticket_set.count()
        nueva_promocion = _promocion_aplicable(ticket.nombre_usuario, total_productos)
        ticket.id_promocion = nueva_promocion
        if nueva_promocion and not ticket.codigounico:
            ticket.codigounico = _generar_codigo_unico()
        elif not nueva_promocion:
            ticket.codigounico = None
        ticket.precio_final = ticket.calcular_total()
        ticket.save(update_fields=["precio_final", "id_promocion", "codigounico"])

        messages.success(request, f"Ticket #{ticket.id_ticket} actualizado correctamente.")
        return redirect("lista_tickets")

    agrupados = defaultdict(lambda: {
        "nombre": "", "precio_unitario": Decimal("0"), "cantidad": 0, "importe": Decimal("0"),
    })
    for detalle in ticket.detalleticket_set.all():
        if not detalle.id_productopedido or not detalle.id_productopedido.id_alimentosbebidas:
            continue
        alimento = detalle.id_productopedido.id_alimentosbebidas
        key = alimento.id_alimentosbebidas
        agrupados[key]["nombre"] = alimento.nombre
        agrupados[key]["precio_unitario"] = alimento.costo
        agrupados[key]["cantidad"] += 1
        agrupados[key]["importe"] += alimento.costo

    alimentos = Alimentosbebidas.objects.filter(activo=True).order_by("nombre")
    return render(request, "modificar_ticket.html", {
        "ticket": ticket,
        "productos_actuales": list(agrupados.values()),
        "alimentos": alimentos,
    })


@login_required(role="admin")
def cancelar_ticket(request, id_ticket):
    if request.method != "POST":
        return redirect("lista_tickets")

    ticket = get_object_or_404(Ticket, id_ticket=id_ticket)
    estado = _get_estado(ticket, localdate())

    if estado != "pendiente":
        messages.error(request, "Solo se pueden cancelar tickets en estado Pendiente.")
        return redirect("lista_tickets")

    ticket.canjeado = -1
    ticket.save(update_fields=["canjeado"])
    messages.success(request, f"Ticket #{ticket.id_ticket} cancelado.")
    return redirect("lista_tickets")


@login_required(role="cliente")
def canjear_ticket(request):
    if request.method == "POST":
        codigo_raw = (request.POST.get("codigo") or "").strip().upper()
        codigo_raw = codigo_raw.replace("TK-", "").replace("TK", "").strip()
        try:
            codigo = int(codigo_raw)
        except ValueError:
            messages.error(request, "Código inválido. Ingresa solo el número que aparece en tu ticket.")
            return render(request, "agregar_ticket.html")

        today = localdate()
        try:
            ticket = Ticket.objects.select_related("id_promocion").get(codigounico=codigo)
        except Ticket.DoesNotExist:
            messages.error(request, "No se encontró ningún ticket con ese código.")
            return render(request, "agregar_ticket.html")

        if ticket.canjeado == 1:
            messages.error(request, "Este ticket ya fue canjeado anteriormente.")
            return render(request, "agregar_ticket.html")

        if ticket.canjeado == -1:
            messages.error(request, "Este ticket fue cancelado.")
            return render(request, "agregar_ticket.html")

        if localdate(ticket.fecha) < today:
            messages.error(request, "Este ticket ha expirado y ya no puede canjearse.")
            return render(request, "agregar_ticket.html")

        ticket.canjeado = 1
        ticket.save(update_fields=["canjeado"])
        promo_nombre = ticket.id_promocion.nombre if ticket.id_promocion else "—"
        messages.success(request, f"¡Ticket canjeado exitosamente! Promoción aplicada: {promo_nombre}.")

    return render(request, "agregar_ticket.html")


@login_required(role="admin")
def imprimir_ticket(request, id_ticket):
    ticket = get_object_or_404(
        Ticket.objects
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas"),
        id_ticket=id_ticket,
    )

    agrupados = defaultdict(lambda: {
        "nombre": "", "descripcion": "", "precio_unitario": Decimal("0"),
        "cantidad": 0, "importe": Decimal("0"),
    })
    for detalle in ticket.detalleticket_set.all():
        if not detalle.id_productopedido or not detalle.id_productopedido.id_alimentosbebidas:
            continue
        alimento = detalle.id_productopedido.id_alimentosbebidas
        key = alimento.id_alimentosbebidas
        agrupados[key]["nombre"] = alimento.nombre
        agrupados[key]["descripcion"] = alimento.descripcion
        agrupados[key]["precio_unitario"] = alimento.costo
        agrupados[key]["cantidad"] += 1
        agrupados[key]["importe"] += alimento.costo

    lineas = list(agrupados.values())
    total_piezas = sum(l["cantidad"] for l in lineas)
    subtotal = sum(l["importe"] for l in lineas)
    descuento_amount = (subtotal - ticket.precio_final) if subtotal > ticket.precio_final else Decimal("0")
    iva_rate = Decimal("0.16")
    iva_amount = (ticket.precio_final - ticket.precio_final / (1 + iva_rate)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return render(request, "ticket_imprimible.html", {
        "ticket": ticket,
        "lineas": lineas,
        "total_piezas": total_piezas,
        "subtotal": subtotal,
        "descuento_amount": descuento_amount,
        "iva_amount": iva_amount,
        "admin": request.current_cliente,
    })
