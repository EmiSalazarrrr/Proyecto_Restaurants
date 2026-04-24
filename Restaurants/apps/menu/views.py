from django.shortcuts import redirect, render, get_object_or_404
from .models import Alimentosbebidas
from django.contrib import messages

# Create your views here.
def lista_alimentos(request):
    alimentos = Alimentosbebidas.objects.all()
    return render(request, 'alimentos_bebidas.html', {'alimentos': alimentos})

def agregar_alimento(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        costo = request.POST.get('costo')
        Alimentosbebidas.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            costo=costo
        )
        messages.success(request, 'Alimento agregado exitosamente.')
        return redirect('lista_alimentos')
    return render(request, 'agregar_alimento.html')

# Modificar alimento
def modificar_alimento(request, id=None):      
    if id is None:
        alimentos = Alimentosbebidas.objects.all()
        return render(request, 'modificar_alimento.html', {'alimentos': alimentos})
    alimento = get_object_or_404(Alimentosbebidas, id_alimentosbebidas=id)
    if request.method == 'POST':
        alimento.nombre = request.POST.get('nombre')
        alimento.descripcion = request.POST.get('descripcion')
        alimento.costo = request.POST.get('costo')
        alimento.save()
        messages.success(request, 'Alimento modificado correctamente')
        return redirect('lista_alimentos')
    return render(request, 'modificar_alimento.html', {'alimento': alimento})


def eliminar_alimento(request, id=None):     
    if id is None:
        alimentos = Alimentosbebidas.objects.all()
        return render(request, 'eliminar_alimento.html', {'alimentos': alimentos})
    
    alimento = get_object_or_404(Alimentosbebidas, id_alimentosbebidas=id)
    if request.method == 'POST':
        alimento.delete()
        messages.success(request, 'Alimento eliminado correctamente')
        return redirect('lista_alimentos')
    return render(request, 'eliminar_alimento.html', {'alimento': alimento})
