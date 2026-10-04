from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q, Case, When, IntegerField, Value, F, BooleanField
from django.db.models.deletion import RestrictedError
from django.db.models.functions import Coalesce
from django.contrib import messages
from .models import Insumo, Box, Movimiento
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from .forms import UserCreateForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_POST
import math

# ==============================
# Helpers de roles / grupos
# ==============================

def user_in_groups(user, group_names):
    """True si el usuario está en algún grupo de la lista. Superuser siempre pasa."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=group_names).exists()


def is_admin_user(user):
    """Solo Administrador."""
    return user_in_groups(user, ["Administrador"])


def can_manage_data(user):
    """
    Puede usar formularios / CRUD:
    Supervisor, Bodega.
    """
    return user_in_groups(user, ["Supervisor", "Bodega"])


def can_view_tablero(user):
    """
    Puede ver tablero:
    Supervisor, Bodega, Enfermero.
    """
    return user_in_groups(user, ["Supervisor", "Bodega", "Enfermero"])


def can_delete_insumos(user):
    """
    Solo Supervisor pueden borrar insumos.
    """
    return user_in_groups(user, ["Supervisor"])

def login_view(request):
    """
    Login con redirección según rol:
    - Administrador -> registrar_usuario
    - Supervisor    -> index
    - Bodega        -> index
    - Enfermero     -> tablero
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            # Redirección según rol
            if is_admin_user(user):
                return redirect("registrar_usuario")
            elif user_in_groups(user, ["Supervisor"]):
                return redirect("index")
            elif user_in_groups(user, ["Bodega"]):
                return redirect("index")
            elif user_in_groups(user, ["Enfermero"]):
                return redirect("tablero")
            else:
                # Si no tiene grupo, lo mandamos a login o index como fallback
                messages.error(request, "Tu usuario no tiene un rol asignado en el sistema.")
                return redirect("login")
    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {"form": form})

# ---------- Página que cada rol puede ver de inicio ----------

class RoleBasedLoginView(LoginView):
    template_name = "login.html"  # ya la estás usando

    def get_success_url(self):
        user = self.request.user

        # 1) ADMIN → solo registrar usuarios
        if is_admin_user(user):
            return reverse_lazy("registrar_usuario")

        # 2) ENFERMERO → solo tablero
        if is_enfermero(user):
            return reverse_lazy("tablero")

        # 3) SUPERVISOR y BODEGA → trabajan con formularios (index)
        if can_manage_data(user):
            return reverse_lazy("index")

        # 4) Cualquier otro que al menos pueda ver tablero
        if can_view_tablero(user):
            return reverse_lazy("tablero")

        # 5) Fallback: por si acaso
        return reverse_lazy("index")

@login_required
@user_passes_test(can_manage_data)
def index(request):
    return render(request, 'index.html')


# ---------- Reemplazos de insert_*.php ----------
@login_required
@user_passes_test(can_manage_data)
def insert_insumo(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        unidad = (request.POST.get('unidad') or '').strip()

        try:
            stock = int(request.POST.get('stock') or 0)
        except ValueError:
            stock = -1

        if not nombre or not unidad:
            messages.error(request, 'Completa nombre y unidad para registrar el insumo.')
            return redirect('index')

        if stock < 0:
            messages.error(request, 'El stock inicial debe ser un número entero mayor o igual a 0.')
            return redirect('index')

        # =========================
        # Cálculo automático 20%
        # =========================
        if stock > 0:
            stock_minimo = math.ceil(stock * 0.20)
        else:
            stock_minimo = 0  # si no hay stock, el umbral también queda en 0

        # Creamos solo si no existe
        obj, created = Insumo.objects.get_or_create(
            nombre=nombre,
            defaults={
                'unidad': unidad,
                'stock_inicial': stock,
                'stock_minimo': stock_minimo,
            }
        )

        if created:
            messages.success(
                request,
                f'Insumo “{obj.nombre}” registrado con stock mínimo automático de {obj.stock_minimo}.'
            )
        else:
            messages.info(
                request,
                f'El insumo “{obj.nombre}” ya existía. No se realizaron cambios.'
            )

        return redirect('index')

    return redirect('index')



@login_required
@user_passes_test(can_manage_data)
def insert_box(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        responsable = (request.POST.get('responsable') or '').strip()

        if not nombre or not responsable:
            messages.error(request, 'Completa nombre del box y su responsable.')
            return redirect('index')

        obj, created = Box.objects.get_or_create(
            nombre=nombre,
            defaults={'responsable': responsable}
        )
        if created:
            messages.success(request, f'Box “{obj.nombre}” registrado correctamente.')
        else:
            messages.info(request, f'El box “{obj.nombre}” ya existía. No se realizaron cambios.')

        return redirect('index')

    return redirect('index')

@login_required
@user_passes_test(can_manage_data)
def insert_movimiento(request):
    if request.method == "POST":
        # 1) Tomar datos del formulario
        tipo = request.POST.get("tipo")
        insumo_nombre = request.POST.get("insumo")
        box_nombre = request.POST.get("box")
        cantidad_str = request.POST.get("cantidad")
        nota = request.POST.get("nota", "").strip()

        # 2) Validar cantidad numérica
        try:
            cantidad = int(cantidad_str)
        except (TypeError, ValueError):
            messages.error(request, "La cantidad debe ser un número entero.")
            return redirect("index")

        # 3) Buscar insumo y box
        try:
            insumo = Insumo.objects.get(nombre=insumo_nombre)
        except Insumo.DoesNotExist:
            messages.error(
                request,
                f'El insumo “{insumo_nombre}” no existe. Regístralo primero.'
            )
            return redirect("index")

        try:
            box = Box.objects.get(nombre=box_nombre)
        except Box.DoesNotExist:
            messages.error(
                request,
                f'El box “{box_nombre}” no existe. Regístralo primero.'
            )
            return redirect("index")

        # 4) Calcular stock actual antes del movimiento
        agg = Movimiento.objects.filter(insumo=insumo).aggregate(
            total_entradas=Coalesce(
                Sum("cantidad", filter=Q(tipo=Movimiento.ENTRADA)),
                0
            ),
            total_salidas=Coalesce(
                Sum("cantidad", filter=Q(tipo=Movimiento.SALIDA)),
                0
            ),
        )
        stock_actual = (
            insumo.stock_inicial
            + agg["total_entradas"]
            - agg["total_salidas"]
        )

        # 5) Bloquear salidas que dejen stock negativo
        if tipo == Movimiento.SALIDA and cantidad > stock_actual:
            messages.error(
                request,
                f'No puedes registrar una SALIDA de {cantidad} {insumo.unidad}. '
                f'Stock disponible actual: {stock_actual}.'
            )
            return redirect("index")

        # 6) Crear el movimiento, guardando quién lo registró
        mov = Movimiento.objects.create(
            tipo=tipo,
            insumo=insumo,
            box=box,
            cantidad=cantidad,
            nota=nota,
            usuario=request.user,  # ya sabemos que está autenticado
        )

        # 7) Calcular stock luego del movimiento
        if tipo == Movimiento.ENTRADA:
            nuevo_stock = stock_actual + cantidad
        else:  # SALIDA
            nuevo_stock = stock_actual - cantidad

        # 8) Alerta si baja de stock mínimo
        if insumo.stock_minimo and nuevo_stock <= insumo.stock_minimo:
            messages.warning(
                request,
                f'Atención: el insumo “{insumo.nombre}” quedó en stock crítico '
                f'({nuevo_stock} {insumo.unidad}).'
            )

        # 9) Mensaje de éxito
        messages.success(
            request,
            f'{tipo.title()} de {cantidad} {insumo.unidad or ""} en '
            f'“{insumo.nombre}” / Box “{box.nombre}” registrada correctamente.'
        )
        return redirect("index")

    # Si alguien entra por GET, lo mandamos al index
    return redirect("index")


# ---------- Tablero ----------
@login_required
@user_passes_test(can_view_tablero)
def tablero(request):
    """
    stock_actual = stock_inicial + sum(entradas) - sum(salidas)
    """
    entradas = Sum(
        Case(
            When(movimiento__tipo=Movimiento.ENTRADA, then='movimiento__cantidad'),
            default=Value(0),
            output_field=IntegerField(),
        )
    )
    salidas = Sum(
        Case(
            When(movimiento__tipo=Movimiento.SALIDA, then='movimiento__cantidad'),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    insumos = (
        Insumo.objects
        .annotate(total_entradas=Coalesce(entradas, Value(0)))
        .annotate(total_salidas=Coalesce(salidas, Value(0)))
        .annotate(
            stock_actual=F('stock_inicial') + F('total_entradas') - F('total_salidas')
        )
        .annotate(
            en_alerta=Case(
                When(
                    stock_minimo__gt=0,
                    stock_actual__lte=F('stock_minimo'),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by('nombre')
    )

    movimientos_recientes = (
        Movimiento.objects
        .select_related('insumo', 'box')
        .order_by('-id')[:20]
    )

    boxes = Box.objects.order_by('nombre')

    return render(request, 'tablero.html', {
        'insumos': insumos,
        'movimientos': movimientos_recientes,
        'boxes': boxes,
    })


# ---------- Crear usuarios ----------
@login_required
@user_passes_test(is_admin_user)
def registrar_usuario(request):
    """
    Vista para que el Administrador cree nuevos usuarios con rol.
    """
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("registrar_usuario")
    else:
        form = UserCreateForm()

    return render(request, "registrar_usuario.html", {"form": form})

# ---------- Eliminacion de insumos ----------
# require_POST: una acción que borra datos nunca debe ejecutarse con un simple GET
# (un enlace, el historial o la precarga del navegador podrían dispararla).
@require_POST
@login_required
@user_passes_test(can_delete_insumos)
def eliminar_insumo(request, insumo_id):
    insumo = get_object_or_404(Insumo, id=insumo_id)
    try:
        insumo.delete()
    except RestrictedError:
        # Movimiento.insumo usa on_delete=RESTRICT para no perder el historial de stock.
        messages.error(
            request,
            f"No se puede eliminar «{insumo.nombre}» porque tiene movimientos registrados."
        )
        return redirect("tablero")
    messages.success(request, f"Insumo «{insumo.nombre}» eliminado correctamente.")
    return redirect("tablero")