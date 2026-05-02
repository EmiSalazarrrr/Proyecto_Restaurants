from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.views import login_required

from .models import Alimentosbebidas


def _parse_costo(value):
    try:
        costo = Decimal(value)
    except (TypeError, InvalidOperation):
        return None
    return costo if costo >= 0 else None


# Create your views here.
@login_required(role="admin")
def lista_alimentos(request):
    alimentos = Alimentosbebidas.objects.order_by("-activo", "nombre")

    top_productos = list(
        Alimentosbebidas.objects.filter(activo=True)
        .annotate(veces=Count("productopedido"))
        .filter(veces__gt=0)
        .order_by("-veces")[:5]
    )
    max_veces = top_productos[0].veces if top_productos else 1
    sin_movimiento = Alimentosbebidas.objects.filter(activo=True, productopedido__isnull=True).count()

    return render(request, 'alimentos_bebidas.html', {
        'alimentos': alimentos,
        'top_productos': top_productos,
        'max_veces': max_veces,
        'sin_movimiento': sin_movimiento,
    })

@login_required(role="admin")
def agregar_alimento(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        costo = request.POST.get('costo')
        costo_decimal = _parse_costo(costo)

        if not all([nombre, descripcion, costo_decimal is not None]):
            messages.error(request, 'Completa los datos con un costo valido mayor o igual a 0.')
            return render(request, 'agregar_alimento.html', {
                'form_data': {
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'costo': costo or '',
                }
            })

        Alimentosbebidas.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            costo=costo_decimal,
            activo=True,
        )
        messages.success(request, 'Alimento agregado exitosamente.')
        return redirect('lista_alimentos')
    return render(request, 'agregar_alimento.html')

# Modificar alimento
@login_required(role="admin")
def modificar_alimento(request, id=None):      
    if id is None:
        alimentos = Alimentosbebidas.objects.all()
        return render(request, 'modificar_alimento.html', {'alimentos': alimentos})
    alimento = get_object_or_404(Alimentosbebidas, id_alimentosbebidas=id)
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        costo_decimal = _parse_costo(request.POST.get('costo'))

        if not all([nombre, descripcion, costo_decimal is not None]):
            messages.error(request, 'Completa los datos con un costo valido mayor o igual a 0.')
            return render(request, 'modificar_alimento.html', {'alimento': alimento})

        alimento.nombre = nombre
        alimento.descripcion = descripcion
        alimento.costo = costo_decimal
        alimento.save()
        messages.success(request, 'Alimento modificado correctamente')
        return redirect('lista_alimentos')
    return render(request, 'modificar_alimento.html', {'alimento': alimento})


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
