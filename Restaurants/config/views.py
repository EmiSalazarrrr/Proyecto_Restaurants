import json
from datetime import datetime, timedelta, date

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import localdate

from apps.menu.models import Alimentosbebidas
from apps.pedidos.models import Ticket
from apps.promociones.models import Promocion
from apps.usuarios.views import login_required


def _build_daily_series(desde, hasta, queryset):
    rows = (
        queryset
        .annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(total=Sum("precio_final"))
        .order_by("dia")
    )
    raw = {row["dia"]: float(row["total"] or 0) for row in rows}
    labels, data = [], []
    current = desde
    while current <= hasta:
        labels.append(current.strftime("%d/%m"))
        data.append(raw.get(current, 0))
        current += timedelta(days=1)
    return labels, data


def _build_monthly_series(desde, hasta, queryset):
    rows = (
        queryset
        .annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(total=Sum("precio_final"))
        .order_by("mes")
    )
    labels = [row["mes"].strftime("%b %Y") for row in rows]
    data = [float(row["total"] or 0) for row in rows]
    return labels, data


@login_required(role="admin")
def menu_admin_view(request):
    today = localdate()
    tickets_hoy = Ticket.objects.filter(fecha__date=today).exclude(canjeado=-1)
    ventas_hoy = tickets_hoy.aggregate(total=Sum("precio_final"))["total"] or 0
    clientes_hoy = tickets_hoy.values("nombre_usuario").distinct().count()
    promociones_activas = Promocion.objects.filter(activo=True).count()

    desde_7 = today - timedelta(days=6)
    labels_7, data_7 = _build_daily_series(
        desde_7, today,
        Ticket.objects.exclude(canjeado=-1).filter(fecha__date__gte=desde_7, fecha__date__lte=today),
    )

    canjeados_hoy = tickets_hoy.filter(canjeado=1).count()
    pendientes_hoy = tickets_hoy.filter(canjeado=0).count()

    context = {
        "ventas_hoy": ventas_hoy,
        "tickets_hoy": tickets_hoy.count(),
        "clientes_hoy": clientes_hoy,
        "promociones_activas": promociones_activas,
        "chart_bar": json.dumps({"labels": labels_7, "data": data_7}),
        "chart_donut": json.dumps({
            "labels": ["Canjeados", "Pendientes"],
            "data": [canjeados_hoy, pendientes_hoy],
            "colors": ["#4cc970", "#c9a84c"],
        }),
    }
    return render(request, "menu_admin.html", context)


@login_required(role="admin")
def metricas_view(request):
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
    )

    total_ventas = tickets.aggregate(total=Sum("precio_final"))["total"] or 0
    total_tickets = tickets.count()
    clientes_unicos = tickets.values("nombre_usuario").distinct().count()
    promedio = (total_ventas / total_tickets) if total_tickets else 0

    dias_diff = (hasta - desde).days
    if periodo == "anio" or dias_diff > 60:
        labels_chart, data_chart = _build_monthly_series(desde, hasta, tickets)
        chart_label = "Ventas por mes"
    else:
        labels_chart, data_chart = _build_daily_series(desde, hasta, tickets)
        chart_label = "Ventas por día"

    max_chart = max(data_chart) if data_chart else 0
    chart_points = [
        {
            "label": label,
            "value": value,
            "percent": round((value / max_chart) * 100, 1) if max_chart else 0,
        }
        for label, value in zip(labels_chart, data_chart)
    ]

    top_productos = list(
        Alimentosbebidas.objects
        .filter(
            productopedido__detalleticket__id_ticket__fecha__date__gte=desde,
            productopedido__detalleticket__id_ticket__fecha__date__lte=hasta,
        )
        .values("nombre")
        .annotate(total=Count("productopedido"))
        .order_by("-total")[:5]
    )
    max_top = top_productos[0]["total"] if top_productos else 1

    top_clientes = list(
        tickets
        .values(
            "nombre_usuario__nombre",
            "nombre_usuario__apellido_paterno",
            "nombre_usuario__nombre_usuario",
        )
        .annotate(total_tickets=Count("id_ticket"))
        .order_by("-total_tickets")[:3]
    )

    context = {
        "periodo": periodo,
        "desde": desde,
        "hasta": hasta,
        "today": today,
        "fecha_str": fecha_str,
        "desde_str": desde_str,
        "hasta_str": hasta_str,
        "total_ventas": total_ventas,
        "total_tickets": total_tickets,
        "clientes_unicos": clientes_unicos,
        "promedio_ticket": round(promedio, 2),
        "chart_label": chart_label,
        "chart_points": chart_points,
        "top_productos": top_productos,
        "max_top": max_top,
        "top_clientes": top_clientes,
    }
    return render(request, "metricas.html", context)
