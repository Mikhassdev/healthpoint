from django.db import models
from django.conf import settings

class Insumo(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    unidad = models.CharField(max_length=20)
    stock_inicial = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(
        default=0,
        help_text="Nivel mínimo recomendado para generar alerta"
    )

    def __str__(self):
        return self.nombre


class Box(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    responsable = models.CharField(max_length=80)

    def __str__(self):
        return self.nombre


class Movimiento(models.Model):
    ENTRADA = 'ENTRADA'
    SALIDA = 'SALIDA'
    TIPO_CHOICES = [(ENTRADA, 'Entrada'), (SALIDA, 'Salida')]

    fecha = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    insumo = models.ForeignKey(Insumo, on_delete=models.RESTRICT, related_name='movimiento')
    box = models.ForeignKey(Box, on_delete=models.RESTRICT, related_name='movimiento')
    cantidad = models.PositiveIntegerField()
    nota = models.CharField(max_length=200, blank=True)

    # Quién registró el movimiento (los registros antiguos pueden no tenerlo)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos"
    )

    def __str__(self):
        return f"{self.tipo} - {self.insumo} ({self.cantidad})"

