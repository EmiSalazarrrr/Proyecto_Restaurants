import json
from datetime import date as date_type
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.views import login_required

from apps.menu.models import Categoria

from .models import Promocion, PromocionComboItem, Restricciones


def _parse_decimal(value):
    try:
        return Decimal(value)
    except (TypeError, InvalidOperation):
        return None


def _parse_date(value):
    """Convierte string 'YYYY-MM-DD' a date, o None si está vacío/inválido."""
    if not value:
        return None
    try:
        return date_type.fromisoformat(value)
    except (ValueError, TypeError):
        return None


@login_required(role="admin")
def promociones_view(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_restriccion":
            nombre = (request.POST.get("restriccion_nombre") or "").strip()
            minimo = request.POST.get("consumo_minimo") or "0"
            tipo_rest = request.POST.get("tipo_restriccion") or "ITEMS"
            if tipo_rest not in ("ITEMS", "VISITAS", "MONTO"):
                tipo_rest = "ITEMS"
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
                    tipo_restriccion=tipo_rest,
                )
                messages.success(request, "Restriccion creada correctamente.")
            return redirect("promociones")

        if action in {"create_promocion", "update_promocion"}:
            nombre = (request.POST.get("nombre") or "").strip()
            descripcion = (request.POST.get("descripcion") or "").strip()
            porcentaje = _parse_decimal(request.POST.get("porcentaje"))
            tipo = request.POST.get("tipo") or "TOTAL"
            categoria_id = request.POST.get("categoria_id") or None
            restriccion_id = request.POST.get("restriccion")
            fecha_inicio = _parse_date(request.POST.get("fecha_inicio"))
            fecha_fin = _parse_date(request.POST.get("fecha_fin"))

            if tipo not in ("TOTAL", "CATEGORIA", "COMBO"):
                tipo = "TOTAL"

            if not all([nombre, descripcion, porcentaje is not None]):
                messages.error(request, "Completa todos los campos de la promocion.")
                return redirect("promociones")

            if porcentaje < 0 or porcentaje > 100:
                messages.error(request, "El porcentaje debe estar entre 0 y 100.")
                return redirect("promociones")

            if tipo == "CATEGORIA" and not categoria_id:
                messages.error(request, "Debes seleccionar una categoria para este tipo de promocion.")
                return redirect("promociones")

            combo_categorias = request.POST.getlist("combo_categoria[]")
            combo_minimos    = request.POST.getlist("combo_minimo[]")
            if tipo == "COMBO":
                combo_pares = [
                    (cid, minv) for cid, minv in zip(combo_categorias, combo_minimos) if cid
                ]
                if len(combo_pares) < 2:
                    messages.error(request, "Un combo necesita al menos 2 categorias diferentes.")
                    return redirect("promociones")

            if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
                messages.error(request, "La fecha de fin no puede ser anterior a la de inicio.")
                return redirect("promociones")

            restriccion = None
            if restriccion_id:
                restriccion = get_object_or_404(Restricciones, pk=restriccion_id)

            categoria = None
            if tipo == "CATEGORIA" and categoria_id:
                categoria = get_object_or_404(Categoria, pk=categoria_id)

            def _guardar_combo_items(promo_obj):
                PromocionComboItem.objects.filter(promocion=promo_obj).delete()
                if tipo == "COMBO":
                    for cat_id, min_val in combo_pares:
                        try:
                            minimo = max(int(min_val or 1), 1)
                        except (ValueError, TypeError):
                            minimo = 1
                        cat = get_object_or_404(Categoria, pk=cat_id)
                        PromocionComboItem.objects.create(
                            promocion=promo_obj,
                            categoria=cat,
                            cantidad_minima=minimo,
                        )

            if action == "create_promocion":
                if Promocion.objects.filter(nombre__iexact=nombre).exists():
                    messages.error(request, "Ya existe una promocion con ese nombre.")
                else:
                    nueva = Promocion.objects.create(
                        nombre=nombre,
                        descripcion=descripcion,
                        porcentaje_a_reducir=porcentaje,
                        tipo=tipo,
                        categoria=categoria,
                        id_restriccion=restriccion,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        activo=True,
                    )
                    _guardar_combo_items(nueva)
                    messages.success(request, "Promocion creada correctamente.")
                return redirect("promociones")

            promocion = get_object_or_404(Promocion, pk=request.POST.get("promocion_id"))
            if Promocion.objects.exclude(pk=promocion.pk).filter(nombre__iexact=nombre).exists():
                messages.error(request, "Ya existe otra promocion con ese nombre.")
            else:
                promocion.nombre = nombre
                promocion.descripcion = descripcion
                promocion.porcentaje_a_reducir = porcentaje
                promocion.tipo = tipo
                promocion.categoria = categoria
                promocion.id_restriccion = restriccion
                promocion.fecha_inicio = fecha_inicio
                promocion.fecha_fin = fecha_fin
                promocion.save()
                _guardar_combo_items(promocion)
                messages.success(request, "Promocion actualizada correctamente.")
            return redirect("promociones")

        if action == "toggle_promocion":
            promocion = get_object_or_404(Promocion, pk=request.POST.get("promocion_id"))
            promocion.activo = not promocion.activo
            promocion.save(update_fields=["activo"])
            estado = "activada" if promocion.activo else "inactivada"
            messages.success(request, f"Promocion {estado} correctamente.")
            return redirect("promociones")

        if action == "delete_promocion":
            from apps.pedidos.models import Ticket
            promocion = get_object_or_404(Promocion, pk=request.POST.get("promocion_id"))
            hoy = date_type.today()
            tickets_pendientes = (
                Ticket.objects
                .filter(id_promocion=promocion, pagado=False, fecha__date=hoy)
                .exclude(canjeado=-1)
                .count()
            )
            if tickets_pendientes:
                messages.error(
                    request,
                    f"No se puede eliminar '{promocion.nombre}': hay {tickets_pendientes} "
                    f"ticket(s) pendiente(s) de hoy con esta promocion. "
                    f"Espera a que sean cobrados o cancelados."
                )
            else:
                nombre = promocion.nombre
                promocion.delete()
                messages.success(request, f"Promocion '{nombre}' eliminada correctamente.")
            return redirect("promociones")

    promociones = (
        Promocion.objects
        .select_related("id_restriccion", "categoria")
        .prefetch_related("combo_items__categoria")
        .order_by("-activo", "nombre")
    )
    restricciones = (
        Restricciones.objects
        .annotate(total_promociones=Count("promocion"))
        .order_by("consumo_minimo_para_aplicar", "nombre")
    )
    categorias = Categoria.objects.order_by("orden", "nombre")
    editar_id = request.GET.get("editar")
    promocion_editar = None
    combo_items_editar = "[]"
    if editar_id:
        promocion_editar = (
            Promocion.objects
            .filter(pk=editar_id)
            .select_related("id_restriccion", "categoria")
            .prefetch_related("combo_items__categoria")
            .first()
        )
        if promocion_editar and promocion_editar.tipo == "COMBO":
            combo_items_editar = json.dumps([
                {"categoria_id": ci.categoria_id, "cantidad_minima": ci.cantidad_minima}
                for ci in promocion_editar.combo_items.all()
            ])

    activas = sum(1 for p in promociones if p.activo)
    inactivas = len(promociones) - activas

    context = {
        "promociones": promociones,
        "restricciones": restricciones,
        "categorias": categorias,
        "promocion_editar": promocion_editar,
        "combo_items_editar": combo_items_editar,
        "chart_donut": json.dumps({
            "labels": ["Activas", "Inactivas"],
            "data": [activas, inactivas],
            "colors": ["#4cc970", "#f07a7a"],
        }),
    }
    return render(request, "promociones.html", context)


@login_required(role="admin")
@require_POST
def toggle_estado_view(request, promocion_id):
    """Endpoint AJAX: alterna activo/inactivo y devuelve JSON."""
    promocion = get_object_or_404(Promocion, pk=promocion_id)
    promocion.activo = not promocion.activo
    promocion.save(update_fields=["activo"])
    return JsonResponse({"estado": "activa" if promocion.activo else "inactiva"})


@login_required(role="admin")
def restricciones_view(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_restriccion":
            nombre = (request.POST.get("restriccion_nombre") or "").strip()
            minimo = request.POST.get("consumo_minimo") or "0"
            tipo_rest = request.POST.get("tipo_restriccion") or "ITEMS"
            if tipo_rest not in ("ITEMS", "VISITAS", "MONTO"):
                tipo_rest = "ITEMS"
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
                    tipo_restriccion=tipo_rest,
                )
                messages.success(request, "Restriccion creada correctamente.")
            return redirect("restricciones")

        if action == "update_restriccion":
            restriccion = get_object_or_404(Restricciones, pk=request.POST.get("restriccion_id"))
            nombre = (request.POST.get("restriccion_nombre") or "").strip()
            minimo = request.POST.get("consumo_minimo") or "0"
            tipo_rest = request.POST.get("tipo_restriccion") or "ITEMS"
            if tipo_rest not in ("ITEMS", "VISITAS", "MONTO"):
                tipo_rest = "ITEMS"
            try:
                minimo_int = max(int(minimo), 0)
            except (TypeError, ValueError):
                minimo_int = None

            if not nombre:
                messages.error(request, "El nombre de la restriccion es obligatorio.")
            elif minimo_int is None:
                messages.error(request, "El consumo minimo debe ser un numero entero.")
            elif Restricciones.objects.exclude(pk=restriccion.pk).filter(nombre__iexact=nombre).exists():
                messages.error(request, "Ya existe otra restriccion con ese nombre.")
            else:
                restriccion.nombre = nombre
                restriccion.consumo_minimo_para_aplicar = minimo_int
                restriccion.tipo_restriccion = tipo_rest
                restriccion.save()
                messages.success(request, "Restriccion actualizada correctamente.")
            return redirect("restricciones")

        if action == "delete_restriccion":
            restriccion = get_object_or_404(Restricciones, pk=request.POST.get("restriccion_id"))
            en_uso = Promocion.objects.filter(id_restriccion=restriccion).count()
            if en_uso:
                messages.error(request, f"No se puede eliminar: esta en uso por {en_uso} promocion(es).")
            else:
                restriccion.delete()
                messages.success(request, "Restriccion eliminada correctamente.")
            return redirect("restricciones")

    editar_id = request.GET.get("editar")
    restriccion_editar = None
    if editar_id:
        restriccion_editar = Restricciones.objects.filter(pk=editar_id).first()

    restricciones = (
        Restricciones.objects
        .annotate(total_promociones=Count("promocion"))
        .order_by("consumo_minimo_para_aplicar", "nombre")
    )
    return render(request, "restricciones.html", {
        "restricciones": restricciones,
        "restriccion_editar": restriccion_editar,
    })
