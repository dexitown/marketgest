"""
persistencia.py
----------------
Guardar y cargar los datos de la Tienda en un archivo JSON.

Intercambiable a futuro por SQLite u otra base, siempre que se respeten
las funciones guardar_tienda() y cargar_tienda().

Responsable sugerido: Persona 1.
"""

import json
from datetime import date
from pathlib import Path

from modelo import Tienda, Producto, Cliente, Venta, DetalleVenta

ARCHIVO_POR_DEFECTO = "datos_tienda.json"


def guardar_tienda(tienda: Tienda, ruta: str = ARCHIVO_POR_DEFECTO) -> None:
    data = {
        "nombre": tienda.nombre,
        "productos": [p.to_dict() for p in tienda.listar_productos()],
        "clientes": [c.to_dict() for c in tienda.listar_clientes()],
        "ventas": [v.to_dict() for v in tienda.listar_ventas()],
    }
    Path(ruta).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cargar_tienda(ruta: str = ARCHIVO_POR_DEFECTO) -> Tienda:
    path = Path(ruta)
    if not path.exists():
        return Tienda()

    data = json.loads(path.read_text(encoding="utf-8"))
    tienda = Tienda(nombre=data.get("nombre", "Mi tienda"))

    # 1. Productos primero (las ventas los referencian)
    for item in data.get("productos", []):
        categoria = tienda.obtener_o_crear_categoria(item["categoria"])
        producto = Producto(
            nombre=item["nombre"],
            precio=item["precio"],
            stock=item["stock"],
            categoria=categoria,
            costo=item.get("costo", 0.0),
            id=item["id"],
        )
        tienda.agregar_producto(producto)

    # 2. Clientes
    clientes_por_id = {}
    for item in data.get("clientes", []):
        cliente = Cliente(nombre=item["nombre"], contacto=item.get("contacto", ""), id=item["id"])
        tienda.agregar_cliente(cliente)
        clientes_por_id[cliente.id] = cliente

    # 3. Ventas (reconstruidas a partir del snapshot guardado, sin volver a tocar stock)
    for item in data.get("ventas", []):
        detalles = []
        for d in item["detalles"]:
            producto = tienda.buscar_producto(d["producto_id"])
            # Si el producto fue borrado después, igual reconstruimos el detalle con los datos guardados
            detalle = DetalleVenta.__new__(DetalleVenta)
            detalle.producto_id = d["producto_id"]
            detalle.nombre_producto = d["nombre_producto"]
            detalle.cantidad = d["cantidad"]
            detalle.precio_unitario = d["precio_unitario"]
            detalles.append(detalle)

        cliente = clientes_por_id.get(item.get("cliente_id"))
        venta = Venta(
            detalles=detalles,
            cliente=cliente,
            fecha=date.fromisoformat(item["fecha"]),
            id=item["id"],
        )
        tienda._ventas.append(venta)  # se agrega directo: ya está validada, no debe volver a descontar stock

    return tienda
