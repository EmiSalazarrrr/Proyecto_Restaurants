from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.views import login_required

from .models import Alimentosbebidas, Categoria


def _parse_costo(value):
    try:
        costo = Decimal(value)
    except (TypeError, InvalidOperation):
        return None
    return costo if costo >= 0 else None


@login_required(role="admin")
def lista_alimentos(request):
    alimentos = Alimentosbebidas.objects.select_related('categoria').order_by("-activo", "nombre")
    categorias = Categoria.objects.order_by('orden', 'nombre')

    top_productos = list(
        Alimentosbebidas.objects.filter(activo=True)
        .annotate(veces=Count("productopedido"))
        .filter(veces__gt=0)
        .order_by("-veces")[:5]
    )
    max_veces = top_productos[0].veces if top_productos else 1
    sin_movimiento = Alimentosbebidas.objects.filter(activo=True, productopedido__isnull=True).count()
    ids_sin_movimiento = list(
        Alimentosbebidas.objects.filter(activo=True, productopedido__isnull=True)
        .values_list('id_alimentosbebidas', flat=True)
    )

    return render(request, 'alimentos_bebidas.html', {
        'alimentos': alimentos,
        'categorias': categorias,
        'top_productos': top_productos,
        'max_veces': max_veces,
        'sin_movimiento': sin_movimiento,
        'ids_sin_movimiento': ids_sin_movimiento,
    })


@login_required(role="admin")
@require_POST
def cambiar_categoria_ajax(request, alimento_id):
    alimento = get_object_or_404(Alimentosbebidas, pk=alimento_id)
    categoria_id = request.POST.get('categoria_id') or None
    if categoria_id:
        alimento.categoria = get_object_or_404(Categoria, pk=categoria_id)
    else:
        alimento.categoria = None
    alimento.save(update_fields=['categoria'])
    nombre = alimento.categoria.nombre if alimento.categoria else ''
    return JsonResponse({'ok': True, 'nombre': nombre})


@login_required(role="admin")
def agregar_alimento(request):
    categorias = Categoria.objects.order_by('orden', 'nombre')
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        costo = request.POST.get('costo')
        costo_decimal = _parse_costo(costo)
        categoria_id = request.POST.get('categoria_id') or None

        if not all([nombre, descripcion, costo_decimal is not None]):
            messages.error(request, 'Completa los datos con un costo valido mayor o igual a 0.')
            return render(request, 'agregar_alimento.html', {
                'form_data': {'nombre': nombre, 'descripcion': descripcion, 'costo': costo or ''},
                'categorias': categorias,
                'selected_categoria': categoria_id,
            })

        categoria = Categoria.objects.filter(pk=categoria_id).first() if categoria_id else None
        Alimentosbebidas.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            costo=costo_decimal,
            activo=True,
            categoria=categoria,
        )
        messages.success(request, 'Alimento agregado exitosamente.')
        return redirect('lista_alimentos')
    return render(request, 'agregar_alimento.html', {'categorias': categorias})


@login_required(role="admin")
def modificar_alimento(request, id=None):
    categorias = Categoria.objects.order_by('orden', 'nombre')
    if id is None:
        alimentos = Alimentosbebidas.objects.select_related('categoria').all()
        return render(request, 'modificar_alimento.html', {'alimentos': alimentos, 'categorias': categorias})

    alimento = get_object_or_404(Alimentosbebidas, id_alimentosbebidas=id)
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        costo_decimal = _parse_costo(request.POST.get('costo'))
        categoria_id = request.POST.get('categoria_id') or None

        if not all([nombre, descripcion, costo_decimal is not None]):
            messages.error(request, 'Completa los datos con un costo valido mayor o igual a 0.')
            return render(request, 'modificar_alimento.html', {'alimento': alimento, 'categorias': categorias})

        alimento.nombre = nombre
        alimento.descripcion = descripcion
        alimento.costo = costo_decimal
        alimento.categoria = Categoria.objects.filter(pk=categoria_id).first() if categoria_id else None
        alimento.save()
        messages.success(request, 'Alimento modificado correctamente')
        return redirect('lista_alimentos')
    return render(request, 'modificar_alimento.html', {'alimento': alimento, 'categorias': categorias})


@login_required(role="admin")
def eliminar_alimento(request, id=None):
    if id is None:
        alimentos = Alimentosbebidas.objects.order_by("-activo", "nombre")
        return render(request, 'eliminar_alimento.html', {'alimentos': alimentos})

    alimento = get_object_or_404(Alimentosbebidas, id_alimentosbebidas=id)
    if request.method == 'POST':
        alimento.activo = not alimento.activo
        alimento.save(update_fields=["activo"])
        estado = "activado" if alimento.activo else "inactivado"
        messages.success(request, f'Alimento {estado} correctamente')
        return redirect('lista_alimentos')
    return render(request, 'eliminar_alimento.html', {'alimento': alimento})


@login_required(role="admin")
def lista_categorias(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            nombre = (request.POST.get('nombre') or '').strip()
            icono = (request.POST.get('icono') or '🍽️').strip() or '🍽️'
            if not nombre:
                messages.error(request, 'El nombre de la categoria es obligatorio.')
            elif Categoria.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, 'Ya existe una categoria con ese nombre.')
            else:
                orden = Categoria.objects.count()
                Categoria.objects.create(nombre=nombre, icono=icono, orden=orden)
                messages.success(request, f'Categoria "{nombre}" creada correctamente.')
            return redirect('lista_categorias')

        if action == 'delete':
            categoria = get_object_or_404(Categoria, pk=request.POST.get('categoria_id'))
            en_uso = Alimentosbebidas.objects.filter(categoria=categoria).count()
            if en_uso:
                messages.error(request, f'No se puede eliminar: {en_uso} producto(s) usan esta categoria.')
            else:
                nombre = categoria.nombre
                categoria.delete()
                messages.success(request, f'Categoria "{nombre}" eliminada.')
            return redirect('lista_categorias')

    categorias = Categoria.objects.annotate(
        total=Count('alimentosbebidas')
    ).order_by('orden', 'nombre')
    return render(request, 'categorias.html', {'categorias': categorias})
