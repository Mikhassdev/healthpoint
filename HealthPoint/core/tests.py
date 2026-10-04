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


class LoginTest(TestCase):

    def login(self, username):
        return self.client.post(reverse("login"), {"username": username, "password": CLAVE})

    def test_usuario_sin_rol_no_inicia_sesion(self):
        crear_usuario("sinrol")
        self.login("sinrol")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_redireccion_por_rol(self):
        destinos = {
            "Administrador": "registrar_usuario",
            "Supervisor": "index",
            "Bodega": "index",
            "Enfermero": "tablero",
        }
        for rol, destino in destinos.items():
            with self.subTest(rol=rol):
                crear_usuario(rol.lower(), rol)
                self.assertRedirects(self.login(rol.lower()), reverse(destino), fetch_redirect_response=False)
                self.client.logout()


class PermisosEnPlantillasTest(BaseTest):

    def test_superusuario_ve_boton_eliminar(self):
        """Las plantillas deben dar al superusuario los mismos permisos que las vistas."""
        self.client.force_login(User.objects.create_superuser("root", password=CLAVE))
        self.assertContains(self.client.get(reverse("tablero")), "Eliminar")

    def test_enfermero_no_ve_boton_eliminar(self):
        self.client.force_login(crear_usuario("enfermero", "Enfermero"))
        self.assertNotContains(self.client.get(reverse("tablero")), "Eliminar")


class TableroTest(BaseTest):

    def test_indicador_cuenta_todos_los_movimientos(self):
        """El tablero lista los últimos 20, pero el indicador debe mostrar el total."""
        Movimiento.objects.bulk_create([
            Movimiento(tipo=Movimiento.ENTRADA, insumo=self.insumo, box=self.box, cantidad=1)
            for _ in range(25)
        ])
        respuesta = self.client.get(reverse("tablero"))
        self.assertEqual(respuesta.context["total_movimientos"], 25)
        self.assertEqual(len(respuesta.context["movimientos"]), 20)

    def test_consultas_no_crecen_con_los_movimientos(self):
        """Evita el problema N+1: mostrar el usuario de cada movimiento no debe sumar consultas."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def contar_consultas():
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(reverse("tablero"))
            return len(ctx.captured_queries)

        Movimiento.objects.create(tipo=Movimiento.ENTRADA, insumo=self.insumo, box=self.box,
                                  cantidad=1, usuario=self.supervisor)
        con_uno = contar_consultas()
        for i in range(10):
            Movimiento.objects.create(tipo=Movimiento.ENTRADA, insumo=self.insumo, box=self.box,
                                      cantidad=1, usuario=crear_usuario(f"bodega{i}", "Bodega"))
            Insumo.objects.create(nombre=f"Insumo {i}", unidad="unidad")
        self.assertEqual(contar_consultas(), con_uno)

    def test_stock_actual_y_alerta(self):
        Movimiento.objects.create(tipo=Movimiento.SALIDA, insumo=self.insumo, box=self.box, cantidad=8)
        insumo = self.client.get(reverse("tablero")).context["insumos"][0]
        self.assertEqual(insumo.stock_actual, 2)
        self.assertTrue(insumo.en_alerta)


class PanelRegistroTest(BaseTest):

    def test_formulario_de_movimiento_ofrece_insumos_y_boxes(self):
        """Elegir de una lista evita errores de tipeo en los nombres."""
        html = self.client.get(reverse("index")).content.decode()
        self.assertIn('<option value="Guantes nitrilo M">', html)
        self.assertIn('<option value="Box 1">', html)


class AdminTest(BaseTest):

    def test_modelos_disponibles_en_el_admin(self):
        self.client.force_login(User.objects.create_superuser("root", password=CLAVE))
        for modelo in ("insumo", "box", "movimiento"):
            with self.subTest(modelo=modelo):
                self.assertEqual(self.client.get(f"/admin/core/{modelo}/").status_code, 200)


class RegistrarMovimientoTest(BaseTest):

    def registrar(self, **cambios):
        datos = {"tipo": "ENTRADA", "insumo": self.insumo.nombre, "box": self.box.nombre, "cantidad": "3"}
        datos.update(cambios)
        return self.client.post(reverse("insert_movimiento"), datos, follow=True)

    def test_entrada_valida(self):
        self.registrar()
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_cantidad_negativa_se_rechaza_sin_error_500(self):
        respuesta = self.registrar(cantidad="-5")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_cantidad_cero_se_rechaza(self):
        self.registrar(cantidad="0")
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_tipo_invalido_se_rechaza(self):
        self.registrar(tipo="HACKEO")
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_salida_mayor_al_stock_se_rechaza(self):
        self.registrar(tipo="SALIDA", cantidad="11")
        self.assertEqual(Movimiento.objects.count(), 0)
