"""Carga usuarios y datos de ejemplo para probar HealthPoint en local.

Uso:  python manage.py cargar_demo
"""
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Box, Insumo, Movimiento

# Solo para desarrollo local: nunca usar estas cuentas en un servidor real.
CLAVE_DEMO = "demo-healthpoint"
USUARIOS = {
    "admin_demo": "Administrador",
    "supervisor_demo": "Supervisor",
    "bodega_demo": "Bodega",
    "enfermero_demo": "Enfermero",
}
INSUMOS = [
    ("Guantes nitrilo M", "caja", 50),
    ("Jeringa 5 ml", "unidad", 200),
    ("Mascarilla N95", "unidad", 100),
    ("Suero fisiológico 0,9%", "bolsa", 40),
]
BOXES = [("Box 1", "Dra. Pérez"), ("Box 2", "Dr. Soto"), ("Urgencia", "Enf. Rojas")]


class Command(BaseCommand):
    help = "Crea un usuario por rol, insumos, boxes y movimientos de ejemplo."

    @transaction.atomic
    def handle(self, *args, **options):
        for username, rol in USUARIOS.items():
            user, creado = User.objects.get_or_create(username=username)
            if creado:
                user.set_password(CLAVE_DEMO)
                user.save()
            user.groups.add(Group.objects.get_or_create(name=rol)[0])

        insumos = {}
        for nombre, unidad, stock in INSUMOS:
            insumos[nombre], _ = Insumo.objects.get_or_create(
                nombre=nombre,
                defaults={"unidad": unidad, "stock_inicial": stock, "stock_minimo": -(-stock // 5)},
            )
        boxes = {}
        for nombre, responsable in BOXES:
            boxes[nombre], _ = Box.objects.get_or_create(nombre=nombre, defaults={"responsable": responsable})

        if not Movimiento.objects.exists():
            bodega = User.objects.get(username="bodega_demo")
            for tipo, insumo, box, cantidad, nota in [
                (Movimiento.SALIDA, "Guantes nitrilo M", "Box 1", 12, "Turno mañana"),
                (Movimiento.SALIDA, "Mascarilla N95", "Urgencia", 85, "Alta demanda"),
                (Movimiento.ENTRADA, "Jeringa 5 ml", "Box 2", 50, "Reposición mensual"),
                (Movimiento.SALIDA, "Suero fisiológico 0,9%", "Urgencia", 10, ""),
            ]:
                Movimiento.objects.create(tipo=tipo, insumo=insumos[insumo], box=boxes[box],
                                          cantidad=cantidad, nota=nota, usuario=bodega)

        self.stdout.write(self.style.SUCCESS(
            f"Datos de demostración listos. Usuarios: {', '.join(USUARIOS)} · clave: {CLAVE_DEMO}"
        ))
