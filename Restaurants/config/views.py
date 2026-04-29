from datetime import datetime

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from apps.menu.models import Alimentosbebidas
from apps.pedidos.models import Ticket
from apps.promociones.models import Promocion
from apps.usuarios.views import login_required


@login_required(role="admin")
def menu_admin_view(request):
    hoy = timezone.localdate()
    tickets_hoy = Ticket.objects.filter(fecha__date=hoy)
    ventas_hoy = tickets_hoy.aggregate(total=Sum("precio_final"))["total"] or 0
    clientes_hoy = tickets_hoy.values("nombre_usuario").distinct().count()
    promociones_activas = Promocion.objects.filter(activo=True).count()

    context = {
        "ventas_hoy": ventas_hoy,
        "tickets_hoy": tickets_hoy.count(),
        "clientes_hoy": clientes_hoy,
        "promociones_activas": promociones_activas,
    }
    return render(request, "menu_admin.html", context)


@login_required(role="admin")
def metricas_view(request):
    fecha_param = request.GET.get("fecha")
    fecha_consulta = timezone.localdate()

    if fecha_param:
        try:
            fecha_consulta = datetime.strptime(fecha_param, "%Y-%m-%d").date()
        except ValueError:
            fecha_consulta = timezone.localdate()

    tickets = (
        Ticket.objects.filter(fecha__date=fecha_consulta)
        .select_related("nombre_usuario", "id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
    )

    resumen = tickets.aggregate(total_ventas=Sum("precio_final"))
    total_ventas = resumen["total_ventas"] or 0
    total_tickets = tickets.count()
    clientes_unicos = tickets.values("nombre_usuario").distinct().count()
    promedio = (total_ventas / total_tickets) if total_tickets else 0

    top_producto = (
        Alimentosbebidas.objects.filter(productopedido__detalleticket__id_ticket__fecha__date=fecha_consulta)
        .values("nombre")
        .annotate(total=Count("productopedido"))
        .order_by("-total", "nombre")
        .first()
    )

    ventas_por_dia = (
        Ticket.objects.annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(total=Sum("precio_final"))
        .order_by("-dia")[:7]
    )

    context = {
        "fecha_consulta": fecha_consulta,
        "total_ventas": total_ventas,
        "total_tickets": total_tickets,
        "clientes_unicos": clientes_unicos,
        "promedio_ticket": promedio,
        "top_producto": top_producto,
        "ventas_por_dia": list(reversed(ventas_por_dia)),
    }
    return render(request, "metricas.html", context)
