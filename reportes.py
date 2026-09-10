"""
reportes.py
-----------
Cálculos y resúmenes a partir de los datos de una Tienda.
No sabe nada de la interfaz gráfica: solo devuelve datos listos para mostrar.

Responsable sugerido: Persona 2 (o compartido).
"""

from collections import defaultdict
from modelo import Tienda


class Reporte:
    def __init__(self, tienda: Tienda):
        self.tienda = tienda

    def total_vendido_por_producto(self) -> dict[str, float]:
        totales = defaultdict(float)
        for venta in self.tienda.listar_ventas():
            for detalle in venta.detalles:
                totales[detalle.nombre_producto] += detalle.subtotal
        return dict(totales)

    def unidades_vendidas_por_producto(self) -> dict[str, int]:
        unidades = defaultdict(int)
        for venta in self.tienda.listar_ventas():
            for detalle in venta.detalles:
                unidades[detalle.nombre_producto] += detalle.cantidad
        return dict(unidades)

    def producto_mas_vendido(self) -> tuple[str, int] | None:
        unidades = self.unidades_vendidas_por_producto()
        if not unidades:
            return None
        return max(unidades.items(), key=lambda item: item[1])

    def total_vendido_por_dia(self) -> dict[str, float]:
        totales = defaultdict(float)
        for venta in self.tienda.listar_ventas():
            totales[venta.fecha.isoformat()] += venta.total
        return dict(sorted(totales.items()))

    def total_vendido_por_mes(self, anio: int) -> dict[int, float]:
        totales = defaultdict(float)
        for venta in self.tienda.listar_ventas():
            if venta.fecha.year == anio:
                totales[venta.fecha.month] += venta.total
        return dict(sorted(totales.items()))

    def ganancia_estimada(self) -> float:
        """
        Ganancia = precio de venta - costo, multiplicado por la cantidad vendida.
        Usa el costo ACTUAL del producto (si el producto fue borrado, no lo cuenta).
        """
        ganancia = 0.0
        for venta in self.tienda.listar_ventas():
            for detalle in venta.detalles:
                producto = self.tienda.buscar_producto(detalle.producto_id)
                if producto:
                    ganancia += (detalle.precio_unitario - producto.costo) * detalle.cantidad
        return ganancia

    def productos_bajo_stock(self, umbral: int = 5):
        return self.tienda.productos_bajo_stock(umbral)
