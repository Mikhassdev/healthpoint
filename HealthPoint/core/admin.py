from django.contrib import admin

from .models import Box, Insumo, Movimiento


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "unidad", "stock_inicial", "stock_minimo")
    search_fields = ("nombre",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("nombre", "responsable")
    search_fields = ("nombre", "responsable")


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo", "insumo", "box", "cantidad", "usuario")
    list_filter = ("tipo", "fecha")
    search_fields = ("insumo__nombre", "box__nombre", "nota")
    list_select_related = ("insumo", "box", "usuario")
