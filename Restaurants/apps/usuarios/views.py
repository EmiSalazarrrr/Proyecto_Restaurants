import hashlib
from functools import wraps

from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import redirect, render

from apps.menu.models import Alimentosbebidas
from apps.pedidos.models import Ticket

from .models import Cliente, Perfiles


SESSION_USER_KEY = "cliente_username"
SESSION_ROLE_KEY = "cliente_role"


def hash_password(raw_password):
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def password_matches(raw_password, stored_password):
    if not stored_password:
        return False
    if stored_password == raw_password:
        return True
    return stored_password == hash_password(raw_password)


def get_role_name(cliente):
    perfil = getattr(cliente, "id_tipo_de_usuario", None)
    if not perfil:
        return ""
    return (perfil.tipo_de_usuario or "").strip().lower()


def is_admin(cliente):
    return "admin" in get_role_name(cliente)


def get_current_cliente(request):
    username = request.session.get(SESSION_USER_KEY)
    if not username:
        return None
    try:
        return Cliente.objects.select_related("id_tipo_de_usuario").get(nombre_usuario=username)
    except Cliente.DoesNotExist:
        request.session.flush()
        return None


def login_required(role=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            cliente = get_current_cliente(request)
            if not cliente:
                messages.info(request, "Inicia sesion para continuar.")
                return redirect("login")
            if role == "admin" and not is_admin(cliente):
                messages.error(request, "Esta seccion es solo para administradores.")
                return redirect("menu_cliente")
            if role == "cliente" and is_admin(cliente):
                return redirect("menu_admin")
            request.current_cliente = cliente
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def login_view(request):
    cliente = get_current_cliente(request)
    if cliente:
        return redirect("menu_admin" if is_admin(cliente) else "menu_cliente")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        try:
            cliente = Cliente.objects.select_related("id_tipo_de_usuario").get(nombre_usuario=username)
        except Cliente.DoesNotExist:
            messages.error(request, "Usuario o contrasena incorrectos.")
        else:
            if password_matches(password, cliente.contrase_a):
                request.session[SESSION_USER_KEY] = cliente.nombre_usuario
                request.session[SESSION_ROLE_KEY] = get_role_name(cliente)
                request.session.modified = True
                return redirect("menu_admin" if is_admin(cliente) else "menu_cliente")
            messages.error(request, "Usuario o contrasena incorrectos.")

    return render(request, "login.html")


def registro_view(request):
    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        apellido_paterno = (request.POST.get("apellido_paterno") or "").strip()
        apellido_materno = (request.POST.get("apellido_materno") or "").strip() or None
        numero_celular = (request.POST.get("numero_celular") or "").strip()
        nombre_usuario = (request.POST.get("nombre_usuario") or "").strip()
        password = request.POST.get("password") or ""
        password_confirm = request.POST.get("password_confirm") or ""

        data = {
            "nombre": nombre,
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno or "",
            "numero_celular": numero_celular,
            "nombre_usuario": nombre_usuario,
        }

        if not all([nombre, apellido_paterno, numero_celular, nombre_usuario, password, password_confirm]):
            messages.error(request, "Completa todos los campos obligatorios.")
            return render(request, "registro.html", {"form_data": data})

        if password != password_confirm:
            messages.error(request, "Las contrasenas no coinciden.")
            return render(request, "registro.html", {"form_data": data})

        if Cliente.objects.filter(nombre_usuario=nombre_usuario).exists():
            messages.error(request, "Ese nombre de usuario ya esta registrado.")
            return render(request, "registro.html", {"form_data": data})

        if Cliente.objects.filter(numero_celular=numero_celular).exists():
            messages.error(request, "Ese numero de celular ya esta registrado.")
            return render(request, "registro.html", {"form_data": data})

        perfil_cliente, _ = Perfiles.objects.get_or_create(tipo_de_usuario="Cliente")

        cliente = Cliente.objects.create(
            nombre_usuario=nombre_usuario,
            numero_celular=numero_celular,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            contrase_a=hash_password(password),
            id_tipo_de_usuario=perfil_cliente,
        )

        request.session[SESSION_USER_KEY] = cliente.nombre_usuario
        request.session[SESSION_ROLE_KEY] = get_role_name(cliente)
        messages.success(request, "Cuenta creada correctamente.")
        return redirect("menu_cliente")

    return render(request, "registro.html")


def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesion cerrada correctamente.")
    return redirect("login")


@login_required(role="cliente")
def menu_cliente_view(request):
    cliente = request.current_cliente
    tickets = (
        Ticket.objects.filter(nombre_usuario=cliente)
        .select_related("id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
        .order_by("-fecha")
    )
    alimentos = Alimentosbebidas.objects.order_by("nombre")
    total_gastado = tickets.aggregate(total=Sum("precio_final"))["total"] or 0
    total_visitas = tickets.count()
    productos_distintos = (
        Alimentosbebidas.objects.filter(productopedido__detalleticket__id_ticket__nombre_usuario=cliente)
        .distinct()
        .count()
    )

    context = {
        "cliente": cliente,
        "alimentos": alimentos,
        "tickets_recientes": tickets[:5],
        "total_gastado": total_gastado,
        "total_visitas": total_visitas,
        "productos_distintos": productos_distintos,
    }
    return render(request, "menu_cliente.html", context)


@login_required(role="cliente")
def historial_view(request):
    cliente = request.current_cliente
    tickets = (
        Ticket.objects.filter(nombre_usuario=cliente)
        .select_related("id_promocion")
        .prefetch_related("detalleticket_set__id_productopedido__id_alimentosbebidas")
        .order_by("-fecha")
    )

    historial = []
    for ticket in tickets:
        productos = [
            detalle.id_productopedido.id_alimentosbebidas.nombre
            for detalle in ticket.detalleticket_set.all()
            if detalle.id_productopedido and detalle.id_productopedido.id_alimentosbebidas
        ]
        subtotal = sum(
            detalle.id_productopedido.id_alimentosbebidas.costo
            for detalle in ticket.detalleticket_set.all()
            if detalle.id_productopedido and detalle.id_productopedido.id_alimentosbebidas
        )
        descuento = subtotal - ticket.precio_final
        historial.append(
            {
                "ticket": ticket,
                "productos": productos,
                "subtotal": subtotal,
                "descuento": descuento if descuento > 0 else 0,
            }
        )

    resumen = tickets.aggregate(total=Sum("precio_final"))
    context = {
        "cliente": cliente,
        "historial": historial,
        "total_consumos": len(historial),
        "monto_total": resumen["total"] or 0,
    }
    return render(request, "historial.html", context)
