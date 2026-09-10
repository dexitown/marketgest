"""
modelo.py
---------
Clases del dominio: Categoria, Producto, Cliente, DetalleVenta, Venta, Tienda.

Esta parte NO debe saber nada de la interfaz gráfica ni de cómo se
guardan los datos en disco. Solo lógica de negocio pura.
Responsable sugerido: Persona 1.
"""

from __future__ import annotations
from datetime import date
import uuid


class Categoria:
    """Categoría de producto (ej: Bebidas, Almacén, Limpieza)."""

    def __init__(self, nombre: str):
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío")
        self.nombre = nombre.strip().capitalize()

    def __eq__(self, other):
        return isinstance(other, Categoria) and self.nombre == other.nombre

    def __hash__(self):
        return hash(self.nombre)

    def __repr__(self):
        return f"Categoria({self.nombre!r})"


class Producto:
    """Un producto del inventario de la tienda."""

    def __init__(self, nombre: str, precio: float, stock: int, categoria: Categoria, costo: float = 0.0, id: str = None):
        self._validar_precio(precio)
        self._validar_stock(stock)

        self.id = id or str(uuid.uuid4())
        self.nombre = nombre.strip()
        self.precio = precio
        self.costo = costo  # lo que le cuesta a la tienda comprarlo/producirlo (para calcular ganancia)
        self.stock = stock
        self.categoria = categoria

    @staticmethod
    def _validar_precio(precio):
        if not isinstance(precio, (int, float)) or precio <= 0:
            raise ValueError("El precio debe ser un número mayor a 0")

    @staticmethod
    def _validar_stock(stock):
        if not isinstance(stock, int) or stock < 0:
            raise ValueError("El stock debe ser un entero mayor o igual a 0")

    def aumentar_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad a agregar debe ser mayor a 0")
        self.stock += cantidad

    def reducir_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad a reducir debe ser mayor a 0")
        if cantidad > self.stock:
            raise ValueError(f"Stock insuficiente de '{self.nombre}' (disponible: {self.stock})")
        self.stock -= cantidad

    @property
    def margen_unitario(self) -> float:
        return self.precio - self.costo

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": self.precio,
            "costo": self.costo,
            "stock": self.stock,
            "categoria": self.categoria.nombre,
        }

    def __repr__(self):
        return f"Producto({self.nombre!r}, ${self.precio}, stock={self.stock})"


class Cliente:
    """Cliente opcional asociado a una venta (podés vender sin cliente también)."""

    def __init__(self, nombre: str, contacto: str = "", id: str = None):
        self.id = id or str(uuid.uuid4())
        self.nombre = nombre.strip()
        self.contacto = contacto.strip()

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "contacto": self.contacto}

    def __repr__(self):
        return f"Cliente({self.nombre!r})"


class DetalleVenta:
    """Una línea dentro de una venta: qué producto, cuántas unidades, a qué precio."""

    def __init__(self, producto: Producto, cantidad: int, precio_unitario: float = None):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        self.producto_id = producto.id
        self.nombre_producto = producto.nombre  # snapshot: si el producto cambia de nombre después, la venta vieja no se altera
        self.cantidad = cantidad
        # snapshot del precio al momento de la venta (si el precio del producto cambia después, no afecta ventas pasadas)
        self.precio_unitario = precio_unitario if precio_unitario is not None else producto.precio

    @property
    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario

    def to_dict(self) -> dict:
        return {
            "producto_id": self.producto_id,
            "nombre_producto": self.nombre_producto,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
        }

    def __repr__(self):
        return f"{self.cantidad}x {self.nombre_producto} (${self.subtotal})"


class Venta:
    """Una venta completa, compuesta por uno o más DetalleVenta."""

    def __init__(self, detalles: list[DetalleVenta], cliente: Cliente = None, fecha: date = None, id: str = None):
        if not detalles:
            raise ValueError("Una venta debe tener al menos un detalle")
        self.id = id or str(uuid.uuid4())
        self.detalles = detalles
        self.cliente = cliente
        self.fecha = fecha or date.today()

    @property
    def total(self) -> float:
        return sum(d.subtotal for d in self.detalles)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fecha": self.fecha.isoformat(),
            "cliente_id": self.cliente.id if self.cliente else None,
            "cliente_nombre": self.cliente.nombre if self.cliente else None,
            "detalles": [d.to_dict() for d in self.detalles],
            "total": self.total,
        }

    def __repr__(self):
        return f"Venta({self.fecha}, total=${self.total})"


class Tienda:
    """
    Clase principal: administra productos, clientes y ventas.
    Es el punto de entrada para toda la lógica de negocio.
    """

    def __init__(self, nombre: str = "Mi tienda"):
        self.nombre = nombre
        self._productos: dict[str, Producto] = {}
        self._clientes: dict[str, Cliente] = {}
        self._categorias: dict[str, Categoria] = {}
        self._ventas: list[Venta] = []

    # ---------- Categorías ----------
    def obtener_o_crear_categoria(self, nombre: str) -> Categoria:
        cat = Categoria(nombre)
        if cat.nombre not in self._categorias:
            self._categorias[cat.nombre] = cat
        return self._categorias[cat.nombre]

    def listar_categorias(self) -> list[Categoria]:
        return list(self._categorias.values())

    # ---------- Productos ----------
    def agregar_producto(self, producto: Producto) -> None:
        self._categorias.setdefault(producto.categoria.nombre, producto.categoria)
        self._productos[producto.id] = producto

    def eliminar_producto(self, producto_id: str) -> bool:
        return self._productos.pop(producto_id, None) is not None

    def buscar_producto(self, producto_id: str) -> Producto | None:
        return self._productos.get(producto_id)

    def buscar_producto_por_nombre(self, nombre: str) -> Producto | None:
        nombre = nombre.strip().lower()
        for p in self._productos.values():
            if p.nombre.lower() == nombre:
                return p
        return None

    def listar_productos(self) -> list[Producto]:
        return sorted(self._productos.values(), key=lambda p: p.nombre)

    def productos_bajo_stock(self, umbral: int = 5) -> list[Producto]:
        return [p for p in self._productos.values() if p.stock <= umbral]

    # ---------- Clientes ----------
    def agregar_cliente(self, cliente: Cliente) -> None:
        self._clientes[cliente.id] = cliente

    def listar_clientes(self) -> list[Cliente]:
        return list(self._clientes.values())

    # ---------- Ventas ----------
    def registrar_venta(self, carrito: list[tuple[str, int]], cliente: Cliente = None, fecha: date = None) -> Venta:
        """
        carrito: lista de tuplas (producto_id, cantidad)
        Valida stock disponible ANTES de descontar nada (todo o nada).
        """
        detalles = []
        for producto_id, cantidad in carrito:
            producto = self.buscar_producto(producto_id)
            if producto is None:
                raise ValueError(f"Producto no encontrado: {producto_id}")
            if cantidad > producto.stock:
                raise ValueError(f"Stock insuficiente de '{producto.nombre}' (disponible: {producto.stock})")

        # Si llegamos hasta acá, todo el carrito es válido: ahora sí descontamos stock
        for producto_id, cantidad in carrito:
            producto = self.buscar_producto(producto_id)
            detalles.append(DetalleVenta(producto, cantidad))
            producto.reducir_stock(cantidad)

        venta = Venta(detalles, cliente=cliente, fecha=fecha)
        self._ventas.append(venta)
        return venta

    def listar_ventas(self) -> list[Venta]:
        return sorted(self._ventas, key=lambda v: v.fecha, reverse=True)

    def ventas_del_mes(self, anio: int, mes: int) -> list[Venta]:
        return [v for v in self._ventas if v.fecha.year == anio and v.fecha.month == mes]

    def total_facturado(self) -> float:
        return sum(v.total for v in self._ventas)
