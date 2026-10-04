from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import Box, Insumo, Movimiento

CLAVE = "Clave-de-prueba-123"


def crear_usuario(username, rol=None):
    user = User.objects.create_user(username, password=CLAVE)
    if rol:
        grupo, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(grupo)
    return user


class BaseTest(TestCase):
    """Datos comunes: un supervisor con sesión iniciada, un insumo y un box."""

    def setUp(self):
        self.supervisor = crear_usuario("supervisor", "Supervisor")
        self.client.force_login(self.supervisor)
        self.insumo = Insumo.objects.create(
            nombre="Guantes nitrilo M", unidad="caja", stock_inicial=10, stock_minimo=2
        )
        self.box = Box.objects.create(nombre="Box 1", responsable="Dra. Pérez")


class EliminarInsumoTest(BaseTest):

    def url(self):
        return reverse("eliminar_insumo", args=[self.insumo.id])

    def test_get_no_elimina(self):
        """Visitar la URL de eliminación no debe borrar nada."""
        respuesta = self.client.get(self.url())
        self.assertEqual(respuesta.status_code, 405)
        self.assertTrue(Insumo.objects.filter(id=self.insumo.id).exists())

    def test_post_elimina_insumo_sin_movimientos(self):
        respuesta = self.client.post(self.url())
        self.assertRedirects(respuesta, reverse("tablero"))
        self.assertFalse(Insumo.objects.filter(id=self.insumo.id).exists())

    def test_insumo_con_movimientos_no_se_elimina_ni_cae(self):
        """El historial protege al insumo: se informa al usuario en vez de un error 500."""
        Movimiento.objects.create(
            tipo=Movimiento.SALIDA, insumo=self.insumo, box=self.box, cantidad=1, usuario=self.supervisor
        )
        respuesta = self.client.post(self.url(), follow=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Insumo.objects.filter(id=self.insumo.id).exists())
        self.assertContains(respuesta, "tiene movimientos registrados")
