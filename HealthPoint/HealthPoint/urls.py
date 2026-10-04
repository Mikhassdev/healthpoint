"""Rutas de HealthPoint."""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from core import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Autenticación con redirección según rol
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Panel de registro + tablero
    path('', views.index, name='index'),
    path('tablero/', views.tablero, name='tablero'),

    # Registro de insumos, boxes y movimientos
    path('insert/insumo/', views.insert_insumo, name='insert_insumo'),
    path('insert/box/', views.insert_box, name='insert_box'),
    path('insert/movimiento/', views.insert_movimiento, name='insert_movimiento'),

    # Registrar usuarios (solo Admin)
    path("usuarios/registrar/", views.registrar_usuario, name="registrar_usuario"),

    # Eliminar insumo (solo Supervisor, según can_delete_insumos)
    path("insumos/<int:insumo_id>/eliminar/", views.eliminar_insumo, name="eliminar_insumo"),
]
