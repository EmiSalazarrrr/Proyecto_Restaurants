from django.shortcuts import render

def login_view(request):
    return render(request, 'login.html')

def registro_view(request):
    return render(request, 'registro.html')