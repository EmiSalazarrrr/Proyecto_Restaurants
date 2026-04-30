import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.views import login_required

from .models import Promocion, Restricciones


def _parse_decimal(value):
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        return None


@login_required(role="admin")
def promociones_view(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_restriccion":
            nombre = (request.POST.get("restriccion_nombre") or "").strip()
            minimo = request.POST.get("consumo_minimo") or "0"
            try:
                minimo_int = max(int(minimo), 0)
            except (TypeError, ValueError):
                minimo_int = None

            if not nombre:
                messages.error(request, "El nombre de la restriccion es obligatorio.")
            elif minimo_int is None:
                messages.error(request, "El consumo minimo debe ser un numero entero.")
            elif Restricciones.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, "Ya existe una restriccion con ese nombre.")
            else:
                Restricciones.objects.create(
                    nombre=nombre,
                    consumo_minimo_para_aplicar=minimo_int,
                )
                messages.success(request, "Restriccion creada correctamente.")
            return redirect("promociones")

        if action in {"create_promocion", "update_promocion"}:
            nombre = (request.POST.get("nombre") or "").strip()
            descripcion = (request.POST.get("descripcion") or "").strip()
            porcentaje = _parse_decimal(request.POST.get("porcentaje"))
            restriccion_id = request.POST.get("restriccion")

            if not all([nombre, descripcion, porcentaje is not None]):
                messages.error(request, "Completa todos los campos de la promocion.")
                return redirect("promociones")

            if porcentaje < 0 or porcentaje > 100:
                messages.error(request, "El porcentaje debe estar entre 0 y 100.")
                return redirect("promociones")

            restriccion = None
            if restriccion_id:
                restriccion = get_object_or_404(Restricciones, pk=restriccion_id)

            if action == "create_promocion":
                if Promocion.objects.filter(nombre__iexact=nombre).exists():
                    messages.error(request, "Ya existe una promocion con ese nombre.")
                else:
                    Promocion.objects.create(
                        nombre=nombre,
                        descripcion=descripcion,
                        porcentaje_a_reducir=porcentaje,
                        id_restriccion=restriccion,
                        activo=True,
                    )
                    messages.success(request, "Promocion creada correctamente.")
                return redirect("promociones")

            promocion = get_object_or_404(Promocion, pk=request.POST.get("promocion_id"))
            if Promocion.objects.exclude(pk=promocion.pk).filter(nombre__iexact=nombre).exists():
                messages.error(request, "Ya existe otra promocion con ese nombre.")
            else:
                promocion.nombre = nombre
                promocion.descripcion = descripcion
                promocion.porcentaje_a_reducir = porcentaje
                promocion.id_restriccion = restriccion
                promocion.save()
                messages.success(request, "Promocion actualizada correctamente.")
            return redirect("promociones")

        if action == "toggle_promocion":
            promocion = get_object_or_404(Promocion, pk=request.POST.get("promocion_id"))
            promocion.activo = not promocion.activo
            promocion.save(update_fields=["activo"])
            estado = "activada" if promocion.activo else "inactivada"
            messages.success(request, f"Promocion {estado} correctamente.")
            return redirect("promociones")

    promociones = Promocion.objects.select_related("id_restriccion").order_by("-activo", "nombre")
    restricciones = Restricciones.objects.order_by("consumo_minimo_para_aplicar", "nombre")
    editar_id = request.GET.get("editar")
    promocion_editar = None
    if editar_id:
        promocion_editar = Promocion.objects.filter(pk=editar_id).select_related("id_restriccion").first()

    activas = sum(1 for p in promociones if p.activo)
    inactivas = len(promociones) - activas

    context = {
        "promociones": promociones,
        "restricciones": restricciones,
        "promocion_editar": promocion_editar,
        "chart_donut": json.dumps({
            "labels": ["Activas", "Inactivas"],
            "data": [activas, inactivas],
            "colors": ["#4cc970", "#f07a7a"],
        }),
    }
    return render(request, "promociones.html", context)
