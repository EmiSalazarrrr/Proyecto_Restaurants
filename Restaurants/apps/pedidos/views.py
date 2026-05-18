import json
import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.db.models import Case, Count, IntegerField, Sum, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import localdate
from django.views.decorators.http import require_POST

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


def _promociones_elegibles(cliente, total_productos):
    from django.db.models import Sum as _Sum
    promociones = Promocion.objects.filter(activo=True).select_related("id_restriccion", "categoria")
    compras_previas = Ticket.objects.filter(nombre_usuario=cliente).count()
    monto_gastado_qs = Ticket.objects.filter(nombre_usuario=cliente, pagado=True).aggregate(total=_Sum("precio_final"))
    monto_gastado = monto_gastado_qs["total"] or Decimal("0")
    elegibles = []

    for promocion in promociones:
        tipo_promo = getattr(promocion, 'tipo', 'TOTAL')

        # CATEGORIA y COMBO siempre aparecen — el frontend filtra según el carrito
        if tipo_promo in ('CATEGORIA', 'COMBO'):
            elegibles.append(promocion)
            continue

        restriccion = promocion.id_restriccion
        if not restriccion:
            elegibles.append(promocion)
            continue

        minimo = getattr(restriccion, "consumo_minimo_para_aplicar", 0) or 0
        tipo_rest = getattr(restriccion, "tipo_restriccion", "ITEMS")

        if tipo_rest == 'VISITAS':
            cumple = compras_previas >= minimo
        elif tipo_rest == 'MONTO':
            cumple = monto_gastado >= Decimal(minimo)
        else:  # ITEMS
            cumple = total_productos >= minimo

        if cumple:
            elegibles.append(promocion)

    return elegibles


def _promocion_recomendada(cliente, total_productos):
    elegibles = _promociones_elegibles(cliente, total_productos)
    if not elegibles:
        return None
    return max(elegibles, key=lambda promo: promo.porcentaje_a_reducir or 0)


def _get_promocion_seleccionada(promocion_id):
    if not promocion_id:
        return None
    try:
        return Promocion.objects.get(pk=promocion_id, activo=True)
    except (Promocion.DoesNotExist, ValueError, TypeError):
        return None


def _cliente_cumple_restriccion(promocion, cliente, total_productos):
    if not promocion or not promocion.id_restriccion:
        return True

    restriccion = promocion.id_restriccion
    minimo = getattr(restriccion, "consumo_minimo_para_aplicar", 0) or 0
    tipo_rest = getattr(restriccion, "tipo_restriccion", "ITEMS")

    if tipo_rest == "VISITAS":
        compras_previas = Ticket.objects.filter(nombre_usuario=cliente).count()
        return compras_previas >= minimo

    if tipo_rest == "MONTO":
        monto_gastado = (
            Ticket.objects
            .filter(nombre_usuario=cliente, pagado=True)
            .aggregate(total=Sum("precio_final"))["total"]
            or Decimal("0")
        )
        return monto_gastado >= Decimal(minimo)

    return total_productos >= minimo


def _promociones_json(promociones):
    data = []
    for promocion in promociones:
        restriccion = promocion.id_restriccion
        tipo = getattr(promocion, 'tipo', 'TOTAL')
        combo_items = []
        if tipo == 'COMBO':
            combo_items = [
                {"categoria_id": ci.categoria_id, "cantidad_minima": ci.cantidad_minima}
                for ci in promocion.combo_items.all()
            ]
        data.append({
            "id":               promocion.id_promocion,
            "nombre":           promocion.nombre,
            "porcentaje":       float(promocion.porcentaje_a_reducir or 0),
            "tipo":             tipo,
            "categoria_id":     getattr(promocion, 'categoria_id', None),
            "combo_items":      combo_items,
            "minimo":           int(getattr(restriccion, "consumo_minimo_para_aplicar", 0) or 0),
            "tipo_restriccion": getattr(restriccion, "tipo_restriccion", "ITEMS") if restriccion else None,
        })
    return json.dumps(data)


def _get_estado(ticket, now):
    """
    Devuelve el estado calculado del ticket:
      'pagado'   — ya cobrado por el admin
      'canjeado' — cliente canjeó (canjeado=1), pendiente de cobro
      'expirado' — nunca canjeado y pasaron más de 24 h desde su creación
      'cancelado'— cancelado manualmente (canjeado=-1)
      'abierto'  — activo, dentro de las 24 h, esperando que el cliente canjee
    """
    if ticket.canjeado == -1:
        return "cancelado"
    if ticket.pagado:
        return "pagado"
    if ticket.canjeado == 1:
        return "canjeado"
    # canjeado == 0: ticket abierto — verificar caducidad de 24 h
    if (now - ticket.fecha).total_seconds() > 86400:
        return "expirado"
    return "abierto"


def _parse_money(value):
    if value in (None, ""):
        return Decimal("0.00")
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    return amount if amount >= 0 else None


def _calcular_cobro(request, total):
    metodo = (request.POST.get("metodo_pago") or "efectivo").strip().lower()
    efectivo_recibido = _parse_money(request.POST.get("efectivo_recibido"))
    pago_tarjeta = _parse_money(request.POST.get("pago_tarjeta"))

    if efectivo_recibido is None or pago_tarjeta is None:
        return None, "Ingresa montos de pago validos."

    if metodo == "tarjeta":
        return {
            "metodo_pago": "tarjeta",
            "pago_efectivo": Decimal("0.00"),
            "pago_tarjeta": total,
            "efectivo_recibido": Decimal("0.00"),
            "cambio": Decimal("0.00"),
        }, None

    if metodo == "efectivo":
        if efectivo_recibido < total:
            return None, "El efectivo recibido no cubre el total del ticket."
        return {
            "metodo_pago": "efectivo",
            "pago_efectivo": total,
            "pago_tarjeta": Decimal("0.00"),
            "efectivo_recibido": efectivo_recibido,
            "cambio": efectivo_recibido - total,
        }, None

    if metodo == "mixto":
        if pago_tarjeta > total:
            return None, "El monto de tarjeta no puede ser mayor al total."
        restante_efectivo = total - pago_tarjeta
        if efectivo_recibido < restante_efectivo:
            return None, "El efectivo recibido no cubre el restante del pago mixto."
        return {
            "metodo_pago": "mixto",
            "pago_efectivo": restante_efectivo,
            "pago_tarjeta": pago_tarjeta,
            "efectivo_recibido": efectivo_recibido,
            "cambio": efectivo_recibido - restante_efectivo,
        }, None

    return None, "Selecciona un metodo de pago valido."


@login_required(role="admin")
def atender_mesa(request):
    from apps.menu.models import Categoria
    alimentos = Alimentosbebidas.objects.filter(activo=True).select_related('categoria').order_by("nombre")
    categorias = Categoria.objects.order_by('orden', 'nombre')
    clientes = Cliente.objects.filter(
        id_tipo_de_usuario__tipo_de_usuario__iexact="Cliente"
    ).order_by("nombre")
    promociones = (Promocion.objects.filter(activo=True)
                   .select_related("id_restriccion", "categoria")
                   .prefetch_related("combo_items")
                   .order_by("nombre"))
    compras_clientes = {
        row["nombre_usuario"]: row["total"]
        for row in Ticket.objects.values("nombre_usuario").annotate(total=Count("id_ticket"))
    }
    monto_clientes = {
        row["nombre_usuario"]: float(row["total"] or 0)
        for row in Ticket.objects.filter(pagado=True).values("nombre_usuario").annotate(total=Sum("precio_final"))
    }

    catalogo_data = [
        {
            "id": a.id_alimentosbebidas,
            "nombre": a.nombre,
            "precio": float(a.costo),
            "categoria_id": a.categoria_id or 0,
        }
        for a in alimentos
    ]
    categorias_data = [
        {"id": c.id_categoria, "nombre": c.nombre, "icono": c.icono}
        for c in categorias
    ]

    return render(request, "atender_mesa.html", {
        "alimentos": alimentos,
        "clientes": clientes,
        "promociones": promociones,
        "promociones_json": _promociones_json(promociones),
        "compras_clientes_json": json.dumps(compras_clientes),
        "monto_clientes_json": json.dumps(monto_clientes),
        "catalogo_json": json.dumps(catalogo_data),
        "categorias_json": json.dumps(categorias_data),
    })


@login_required(role="admin")
def guardar_ticket(request):
    if request.method != "POST":
        return redirect("atender_mesa")

    nombre_usuario = request.POST.get("cliente")
    promocion_id = request.POST.get("promocion_id")
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

    promocion = _get_promocion_seleccionada(promocion_id)
    if promocion and not _cliente_cumple_restriccion(promocion, cliente, total_productos):
        messages.error(request, "El cliente no cumple la restriccion de la promocion seleccionada.")
        return redirect("atender_mesa")

    subtotal = sum(alimento.costo * cantidad for alimento, cantidad in lineas)
    precio_final = subtotal
    if promocion and promocion.porcentaje_a_reducir:
        from collections import defaultdict
        pct  = promocion.porcentaje_a_reducir / Decimal("100")
        tipo = getattr(promocion, 'tipo', 'TOTAL')

        if tipo == 'CATEGORIA' and getattr(promocion, 'categoria_id', None):
            base = sum(
                alimento.costo * cantidad
                for alimento, cantidad in lineas
                if alimento.categoria_id == promocion.categoria_id
            )
        elif tipo == 'COMBO':
            combo_items = list(promocion.combo_items.all())
            cat_counts = defaultdict(int)
            cat_costs  = defaultdict(Decimal)
            for alimento, cantidad in lineas:
                cat_counts[alimento.categoria_id] += cantidad
                cat_costs[alimento.categoria_id]  += alimento.costo * cantidad
            all_met = all(
                cat_counts[ci.categoria_id] >= ci.cantidad_minima
                for ci in combo_items
            )
            base = (
                sum(cat_costs[ci.categoria_id] for ci in combo_items)
                if (combo_items and all_met) else Decimal("0")
            )
        else:
            base = subtotal
        precio_final = subtotal - base * pct
    precio_final = precio_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    ticket = Ticket.objects.create(
        precio_final=precio_final,
        fecha=timezone.now(),
        canjeado=0,
        id_promocion=promocion,
        nombre_usuario=cliente,
        codigounico=_generar_codigo_unico(),
        metodo_pago="pendiente",
    )

    for alimento, cantidad in lineas:
        for _ in range(cantidad):
            pp = Productopedido.objects.create(id_alimentosbebidas=alimento)
            Detalleticket.objects.create(id_ticket=ticket, id_productopedido=pp)

    if promocion:
        messages.success(request, f"Ticket #{ticket.id_ticket} abierto para cocina con codigo TK-{ticket.codigounico} y promocion {promocion.nombre}.")
    else:
        messages.success(request, f"Ticket #{ticket.id_ticket} abierto para cocina con codigo TK-{ticket.codigounico}.")
    return redirect("lista_tickets")


@login_required(role="admin")
def lista_tickets(request):
    today = localdate()
    now = timezone.now()
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

    # Los tickets canjeados por el cliente (canjeado=1, no pagados) suben al tope
    # para que el admin los vea de inmediato y pueda cobrarlos.
    tickets = (
        Ticket.objects
        .filter(fecha__date__gte=desde, fecha__date__lte=hasta)
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
        .annotate(
            _sort_priority=Case(
                When(canjeado=1, pagado=False, then=Value(0)),  # canjeado arriba
                When(canjeado=0, pagado=False, then=Value(1)),  # abiertos/expirados
                default=Value(2),                               # pagados/cancelados
                output_field=IntegerField(),
            )
        )
        .order_by('_sort_priority', '-fecha')
    )

    tickets_con_estado = [(t, _get_estado(t, now)) for t in tickets]

    count_abierto   = sum(1 for _, e in tickets_con_estado if e == "abierto")
    count_canjeado  = sum(1 for _, e in tickets_con_estado if e == "canjeado")
    count_pagado    = sum(1 for _, e in tickets_con_estado if e == "pagado")
    count_expirado  = sum(1 for _, e in tickets_con_estado if e == "expirado")
    count_cancelado = sum(1 for _, e in tickets_con_estado if e == "cancelado")
    total_ingresos  = sum(t.precio_final for t, e in tickets_con_estado if e == "pagado")

    chart_data = json.dumps({
        "labels": ["Pagados", "Canjeados", "Abiertos", "Expirados", "Cancelados"],
        "data": [count_pagado, count_canjeado, count_abierto, count_expirado, count_cancelado],
        "colors": ["#4cc970", "#7eb3ff", "#D8AE48", "#f0a07a", "#f07a7a"],
    })

    return render(request, "lista_tickets.html", {
        "tickets_con_estado": tickets_con_estado,
        "total_tickets": len(tickets_con_estado),
        "total_ingresos": total_ingresos,
        "count_pagado": count_pagado,
        "count_canjeado": count_canjeado,
        "count_abierto": count_abierto,
        "count_expirado": count_expirado,
        "count_cancelado": count_cancelado,
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
    now = timezone.now()
    estado = _get_estado(ticket, now)

    # Solo se pueden modificar tickets abiertos (canjeado=0): si el cliente ya
    # canjeó el ticket no se puede cambiar la orden.
    if estado != "abierto":
        messages.error(request, "Solo se pueden modificar tickets abiertos y sin canjear.")
        return redirect("lista_tickets")

    if request.method == "POST":
        productos_ids = request.POST.getlist("producto_id[]")
        cantidades = request.POST.getlist("cantidad[]")
        promocion_id = request.POST.get("promocion_id")

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

        ticket.id_promocion = _get_promocion_seleccionada(promocion_id)
        if not ticket.codigounico:
            ticket.codigounico = _generar_codigo_unico()
        # Clear stale prefetch cache so calcular_total reads the newly added detalletickets from DB
        if hasattr(ticket, '_prefetched_objects_cache'):
            ticket._prefetched_objects_cache = {}
        ticket.precio_final = ticket.calcular_total()
        ticket.save(update_fields=["precio_final", "id_promocion", "codigounico"])

        messages.success(request, f"Ticket #{ticket.id_ticket} actualizado correctamente.")
        return redirect("lista_tickets")

    agrupados = defaultdict(lambda: {
        "alimento_id": None, "nombre": "", "precio_unitario": Decimal("0"), "cantidad": 0, "importe": Decimal("0"),
    })
    for detalle in ticket.detalleticket_set.all():
        if not detalle.id_productopedido or not detalle.id_productopedido.id_alimentosbebidas:
            continue
        alimento = detalle.id_productopedido.id_alimentosbebidas
        key = alimento.id_alimentosbebidas
        agrupados[key]["alimento_id"] = alimento.id_alimentosbebidas
        agrupados[key]["nombre"] = alimento.nombre
        agrupados[key]["precio_unitario"] = alimento.costo
        agrupados[key]["cantidad"] += 1
        agrupados[key]["importe"] += alimento.costo

    alimentos = Alimentosbebidas.objects.filter(activo=True).order_by("nombre")
    promociones = Promocion.objects.filter(activo=True).select_related("id_restriccion").order_by("nombre")
    recomendada = _promocion_recomendada(ticket.nombre_usuario, ticket.detalleticket_set.count())
    return render(request, "modificar_ticket.html", {
        "ticket": ticket,
        "productos_actuales": list(agrupados.values()),
        "alimentos": alimentos,
        "promociones": promociones,
        "promocion_recomendada": recomendada,
    })


@login_required(role="admin")
@require_POST
def eliminar_item_ticket(request, id_ticket, alimento_id):
    """AJAX: elimina todas las unidades de un alimento del ticket y recalcula total."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("id_promocion__id_restriccion", "nombre_usuario"),
        id_ticket=id_ticket,
    )

    if _get_estado(ticket, timezone.now()) != "abierto":
        return JsonResponse({"ok": False, "error": "El ticket no está en estado abierto."}, status=400)

    # Buscar los Detalleticket de ese alimento en este ticket
    detalles_qs = ticket.detalleticket_set.filter(
        id_productopedido__id_alimentosbebidas_id=alimento_id
    )
    if not detalles_qs.exists():
        return JsonResponse({"ok": False, "error": "El producto no existe en este ticket."}, status=404)

    # Guardar IDs de Productopedido antes de borrar
    pp_ids = list(detalles_qs.values_list("id_productopedido_id", flat=True))

    # Borrar Detalleticket primero (tienen FK a Productopedido)
    detalles_qs.delete()

    # Borrar Productopedido huérfanos
    Productopedido.objects.filter(id_productopedido__in=pp_ids).delete()

    # Verificar si la promoción sigue siendo válida tras la eliminación
    promo_removida = False
    if ticket.id_promocion:
        total_restante = ticket.detalleticket_set.count()
        cliente_ticket = ticket.nombre_usuario
        if cliente_ticket:
            elegibles = _promociones_elegibles(cliente_ticket, total_restante)
            promo_sigue = any(p.id_promocion == ticket.id_promocion.id_promocion for p in elegibles)
        else:
            restriccion = ticket.id_promocion.id_restriccion
            if restriccion and "frecuente" not in (restriccion.nombre or "").lower():
                promo_sigue = total_restante >= (restriccion.consumo_minimo_para_aplicar or 0)
            else:
                promo_sigue = True

        if not promo_sigue:
            ticket.id_promocion = None
            promo_removida = True

    # Recalcular total (limpiar caché de prefetch)
    if hasattr(ticket, "_prefetched_objects_cache"):
        ticket._prefetched_objects_cache = {}

    nuevo_total = ticket.calcular_total()
    ticket.precio_final = nuevo_total
    fields = ["precio_final"]
    if promo_removida:
        fields.append("id_promocion")
    ticket.save(update_fields=fields)

    ticket_vacio = ticket.detalleticket_set.count() == 0

    return JsonResponse({
        "ok": True,
        "nuevo_total": float(nuevo_total),
        "promo_removida": promo_removida,
        "ticket_vacio": ticket_vacio,
    })


@login_required(role="admin")
def cancelar_ticket(request, id_ticket):
    if request.method != "POST":
        return redirect("lista_tickets")

    ticket = get_object_or_404(Ticket, id_ticket=id_ticket)
    estado = _get_estado(ticket, timezone.now())

    # Permitir cancelar tanto tickets abiertos como canjeados (antes de cobrar).
    if estado not in ("abierto", "canjeado"):
        messages.error(request, "Solo se pueden cancelar tickets activos y sin cobrar.")
        return redirect("lista_tickets")

    ticket.canjeado = -1
    ticket.save(update_fields=["canjeado"])
    messages.success(request, f"Ticket #{ticket.id_ticket} cancelado.")
    return redirect("lista_tickets")


@login_required(role="admin")
def cobrar_ticket(request, id_ticket):
    if request.method != "POST":
        return redirect("lista_tickets")

    ticket = get_object_or_404(
        Ticket.objects.prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas"),
        id_ticket=id_ticket,
    )

    # Se puede cobrar tanto un ticket abierto como uno ya canjeado por el cliente.
    if _get_estado(ticket, timezone.now()) not in ("abierto", "canjeado"):
        messages.error(request, "Solo se pueden cobrar tickets activos.")
        return redirect("lista_tickets")

    ticket.precio_final = ticket.calcular_total()
    cobro, error_cobro = _calcular_cobro(request, ticket.precio_final)
    if error_cobro:
        messages.error(request, error_cobro)
        return redirect("lista_tickets")

    for field, value in cobro.items():
        setattr(ticket, field, value)
    ticket.pagado = True
    ticket.save(update_fields=[
        "precio_final",
        "metodo_pago",
        "pago_efectivo",
        "pago_tarjeta",
        "efectivo_recibido",
        "cambio",
        "pagado",
    ])
    messages.success(request, f"Ticket #{ticket.id_ticket} cobrado correctamente. Cambio: ${ticket.cambio}.")
    return redirect("lista_tickets")


@login_required(role="cliente")
def mis_tickets_view(request):
    """Página del cliente: tickets activos en tiempo real + recientes."""
    cliente = request.current_cliente
    now = timezone.now()

    tickets_qs = (
        Ticket.objects
        .filter(nombre_usuario=cliente)
        .select_related("id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
        .order_by("-fecha")[:20]
    )

    activos = []
    recientes = []

    for ticket in tickets_qs:
        estado = _get_estado(ticket, now)

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

        lineas = list(agrupados.values())
        subtotal = sum(l["importe"] for l in lineas)
        descuento = (subtotal - ticket.precio_final) if subtotal > ticket.precio_final else Decimal("0")

        entry = {
            "ticket": ticket,
            "estado": estado,
            "lineas": lineas,
            "subtotal": subtotal,
            "descuento": descuento,
        }

        if estado in ("abierto", "canjeado"):
            activos.append(entry)
        else:
            recientes.append(entry)

    return render(request, "mis_tickets.html", {
        "activos": activos,
        "recientes": recientes[:5],
        "cliente": cliente,
    })


@login_required(role="cliente")
def canjear_directo(request, ticket_id):
    """Canjear desde /mis-tickets/ sin necesidad de ingresar el código."""
    if request.method != "POST":
        return redirect("mis_tickets")

    ticket = get_object_or_404(Ticket, id_ticket=ticket_id)
    cliente = request.current_cliente

    if ticket.nombre_usuario != cliente:
        messages.error(request, "No tienes permiso para canjear este ticket.")
        return redirect("mis_tickets")

    estado = _get_estado(ticket, timezone.now())
    if estado != "abierto":
        messages.error(request, "Este ticket no se puede canjear en este momento.")
        return redirect("mis_tickets")

    ticket.canjeado = 1
    ticket.save(update_fields=["canjeado"])
    return redirect("confirmacion_canje", id_ticket=ticket.id_ticket)


@login_required(role="admin")
def reabrir_ticket(request, id_ticket):
    """Permite al admin revertir un ticket canjeado a abierto para poder modificarlo."""
    if request.method != "POST":
        return redirect("lista_tickets")

    ticket = get_object_or_404(Ticket, id_ticket=id_ticket)

    if ticket.canjeado != 1 or ticket.pagado:
        messages.error(request, "Solo se pueden reabrir tickets canjeados sin cobrar.")
        return redirect("lista_tickets")

    ticket.canjeado = 0
    ticket.save(update_fields=["canjeado"])
    messages.success(request, f"Ticket #{ticket.id_ticket} reabierto. El cliente podrá canjearlo de nuevo cuando esté listo.")
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

        # Caducidad: el ticket expira 24 horas después de su creación
        if (timezone.now() - ticket.fecha).total_seconds() > 86400:
            messages.error(request, "Este ticket ha expirado (más de 24 h desde su creación).")
            return render(request, "agregar_ticket.html")

        cliente_actual = request.current_cliente
        if ticket.nombre_usuario and ticket.nombre_usuario != cliente_actual:
            messages.error(request, "Este codigo pertenece a otro cliente.")
            return render(request, "agregar_ticket.html")

        ticket.canjeado = 1
        ticket.nombre_usuario = cliente_actual
        ticket.save(update_fields=["canjeado", "nombre_usuario"])
        return redirect("confirmacion_canje", id_ticket=ticket.id_ticket)

    return render(request, "agregar_ticket.html")


@login_required(role="cliente")
def confirmacion_canje(request, id_ticket):
    ticket = get_object_or_404(
        Ticket.objects
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas"),
        id_ticket=id_ticket,
        canjeado=1,
    )

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

    lineas = list(agrupados.values())
    subtotal = sum(l["importe"] for l in lineas)
    descuento_amount = (subtotal - ticket.precio_final) if subtotal > ticket.precio_final else Decimal("0")

    return render(request, "confirmacion_canje.html", {
        "ticket": ticket,
        "lineas": lineas,
        "subtotal": subtotal,
        "descuento_amount": descuento_amount,
    })


def ver_ticket(request, ticket_id):
    """Vista de detalle de ticket — accesible para admin y cliente propietario."""
    from apps.usuarios.views import get_current_cliente, is_admin
    from django.http import HttpResponseForbidden

    cliente = get_current_cliente(request)
    if not cliente:
        from django.contrib import messages as _messages
        _messages.info(request, "Inicia sesion para continuar.")
        return redirect("login")

    ticket = get_object_or_404(
        Ticket.objects
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas"),
        id_ticket=ticket_id,
    )

    es_admin = is_admin(cliente)

    # Cliente solo puede ver su propio ticket
    if not es_admin:
        if ticket.nombre_usuario != cliente:
            return HttpResponseForbidden("No tienes permiso para ver este ticket.")

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

    lineas = list(agrupados.values())
    subtotal = sum(l["importe"] for l in lineas)
    descuento_amount = (subtotal - ticket.precio_final) if subtotal > ticket.precio_final else Decimal("0")

    return render(request, "ticket_detalle.html", {
        "ticket": ticket,
        "lineas": lineas,
        "subtotal": subtotal,
        "descuento_amount": descuento_amount,
        "es_admin": es_admin,
    })


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
