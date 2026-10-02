"""
URL configuration for HealthPoint project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from core.views import RoleBasedLoginView
from core import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Autenticación (NUEVO login basado en roles)
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Home + tablero
    path('', views.index, name='index'),
    path('tablero/', views.tablero, name='tablero'),

    # Inserts (usa los mismos "name" que ya usas en los forms)
    path('insert/insumo/', views.insert_insumo, name='insert_insumo'),
    path('insert/box/', views.insert_box, name='insert_box'),
    path('insert/movimiento/', views.insert_movimiento, name='insert_movimiento'),

    # Registrar usuarios (solo Admin)
    path("usuarios/registrar/", views.registrar_usuario, name="registrar_usuario"),

    # Eliminar insumo (solo Supervisor, según can_delete_insumos)
    path("insumos/<int:insumo_id>/eliminar/", views.eliminar_insumo, name="eliminar_insumo"),
]