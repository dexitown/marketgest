"""
gui.py
------
Interfaz gráfica con Tkinter. Esta capa SOLO muestra datos y captura
interacción del usuario. Nunca calcula totales ni maneja stock
directamente: siempre delega en Tienda o Reporte.

Responsable sugerido: Persona 2.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modelo import Tienda, Producto
from reportes import Reporte
from persistencia import guardar_tienda, cargar_tienda


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Ventas e Inventario")
        self.geometry("900x600")

        self.tienda: Tienda = cargar_tienda()
        self.carrito: list[tuple[str, int]] = []  # [(producto_id, cantidad), ...]

        self._crear_pestañas()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    def _crear_pestañas(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_productos = ttk.Frame(notebook)
        self.tab_ventas = ttk.Frame(notebook)
        self.tab_reportes = ttk.Frame(notebook)

        notebook.add(self.tab_productos, text="Productos / Inventario")
        notebook.add(self.tab_ventas, text="Registrar venta")
        notebook.add(self.tab_reportes, text="Reportes")

        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._armar_tab_productos()
        self._armar_tab_ventas()
        self._armar_tab_reportes()

    def _on_tab_changed(self, event):
        tab_actual = event.widget.tab(event.widget.select(), "text")
        if tab_actual == "Productos / Inventario":
            self._refrescar_tabla_productos()
        elif tab_actual == "Registrar venta":
            self._refrescar_combo_productos()
        elif tab_actual == "Reportes":
            self._refrescar_reportes()

    # ---------------------------------------------------------------
    # TAB 1: Productos / Inventario
    # ---------------------------------------------------------------
    def _armar_tab_productos(self):
        frame = self.tab_productos

        form = ttk.LabelFrame(frame, text="Agregar / cargar stock de producto")
        form.pack(fill="x", padx=8, pady=8)
        padding = {"padx": 6, "pady": 4}

        ttk.Label(form, text="Nombre:").grid(row=0, column=0, sticky="w", **padding)
        self.entry_nombre = ttk.Entry(form)
        self.entry_nombre.grid(row=0, column=1, **padding)

        ttk.Label(form, text="Precio venta ($):").grid(row=0, column=2, sticky="w", **padding)
        self.entry_precio = ttk.Entry(form, width=10)
        self.entry_precio.grid(row=0, column=3, **padding)

        ttk.Label(form, text="Costo ($):").grid(row=0, column=4, sticky="w", **padding)
        self.entry_costo = ttk.Entry(form, width=10)
        self.entry_costo.grid(row=0, column=5, **padding)

        ttk.Label(form, text="Stock inicial:").grid(row=1, column=0, sticky="w", **padding)
        self.entry_stock = ttk.Entry(form, width=10)
        self.entry_stock.grid(row=1, column=1, **padding)

        ttk.Label(form, text="Categoría:").grid(row=1, column=2, sticky="w", **padding)
        self.entry_categoria = ttk.Entry(form, width=15)
        self.entry_categoria.grid(row=1, column=3, **padding)

        ttk.Button(form, text="Agregar producto", command=self._agregar_producto).grid(row=1, column=5, **padding)

        # Tabla de productos
        columnas = ("nombre", "categoria", "precio", "costo", "stock")
        self.tabla_productos = ttk.Treeview(frame, columns=columnas, show="headings")
        for col, texto in zip(columnas, ["Nombre", "Categoría", "Precio", "Costo", "Stock"]):
            self.tabla_productos.heading(col, text=texto)
        self.tabla_productos.pack(fill="both", expand=True, padx=8, pady=8)

        botones = ttk.Frame(frame)
        botones.pack(pady=4)
        ttk.Button(botones, text="Eliminar producto", command=self._eliminar_producto).pack(side="left", padx=4)
        ttk.Button(botones, text="Sumar 10 al stock (reponer)", command=self._reponer_stock).pack(side="left", padx=4)

    def _agregar_producto(self):
        try:
            nombre = self.entry_nombre.get()
            precio = float(self.entry_precio.get())
            costo = float(self.entry_costo.get() or 0)
            stock = int(self.entry_stock.get())
            nombre_categoria = self.entry_categoria.get()

            if not nombre.strip():
                raise ValueError("El nombre no puede estar vacío")
            if not nombre_categoria.strip():
                raise ValueError("La categoría no puede estar vacía")

            categoria = self.tienda.obtener_o_crear_categoria(nombre_categoria)
            producto = Producto(nombre, precio, stock, categoria, costo=costo)
            self.tienda.agregar_producto(producto)
            guardar_tienda(self.tienda)

            messagebox.showinfo("Listo", "Producto agregado correctamente")
            self._limpiar_form_producto()
            self._refrescar_tabla_productos()

        except ValueError as e:
            messagebox.showerror("Datos inválidos", str(e))
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))

    def _limpiar_form_producto(self):
        for entry in (self.entry_nombre, self.entry_precio, self.entry_costo, self.entry_stock, self.entry_categoria):
            entry.delete(0, tk.END)

    def _refrescar_tabla_productos(self):
        self.tabla_productos.delete(*self.tabla_productos.get_children())
        for p in self.tienda.listar_productos():
            self.tabla_productos.insert(
                "", tk.END, iid=p.id,
                values=(p.nombre, p.categoria.nombre, f"${p.precio:.2f}", f"${p.costo:.2f}", p.stock),
            )

    def _eliminar_producto(self):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Nada seleccionado", "Elegí un producto de la tabla primero")
            return
        self.tienda.eliminar_producto(seleccion[0])
        guardar_tienda(self.tienda)
        self._refrescar_tabla_productos()

    def _reponer_stock(self):
        """Botón de ejemplo rápido. TODO: reemplazar por un diálogo que pida la cantidad."""
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Nada seleccionado", "Elegí un producto de la tabla primero")
            return
        producto = self.tienda.buscar_producto(seleccion[0])
        producto.aumentar_stock(10)
        guardar_tienda(self.tienda)
        self._refrescar_tabla_productos()

    # ---------------------------------------------------------------
    # TAB 2: Registrar venta
    # ---------------------------------------------------------------
    def _armar_tab_ventas(self):
        frame = self.tab_ventas

        seleccion_frame = ttk.LabelFrame(frame, text="Agregar producto al carrito")
        seleccion_frame.pack(fill="x", padx=8, pady=8)

        ttk.Label(seleccion_frame, text="Producto:").grid(row=0, column=0, padx=6, pady=6)
        self.combo_productos = ttk.Combobox(seleccion_frame, state="readonly", width=30)
        self.combo_productos.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(seleccion_frame, text="Cantidad:").grid(row=0, column=2, padx=6, pady=6)
        self.entry_cantidad_venta = ttk.Entry(seleccion_frame, width=6)
        self.entry_cantidad_venta.grid(row=0, column=3, padx=6, pady=6)

        ttk.Button(seleccion_frame, text="Agregar al carrito", command=self._agregar_al_carrito).grid(row=0, column=4, padx=6, pady=6)

        # Carrito
        columnas = ("producto", "cantidad", "subtotal")
        self.tabla_carrito = ttk.Treeview(frame, columns=columnas, show="headings", height=8)
        for col, texto in zip(columnas, ["Producto", "Cantidad", "Subtotal"]):
            self.tabla_carrito.heading(col, text=texto)
        self.tabla_carrito.pack(fill="both", expand=True, padx=8, pady=8)

        self.label_total_carrito = ttk.Label(frame, text="Total: $0.00", font=("Segoe UI", 12, "bold"))
        self.label_total_carrito.pack(pady=4)

        botones = ttk.Frame(frame)
        botones.pack(pady=6)
        ttk.Button(botones, text="Vaciar carrito", command=self._vaciar_carrito).pack(side="left", padx=4)
        ttk.Button(botones, text="Confirmar venta", command=self._confirmar_venta).pack(side="left", padx=4)

    def _refrescar_combo_productos(self):
        productos = self.tienda.listar_productos()
        self._productos_disponibles = {p.nombre: p for p in productos}
        self.combo_productos["values"] = list(self._productos_disponibles.keys())

    def _agregar_al_carrito(self):
        try:
            nombre = self.combo_productos.get()
            cantidad = int(self.entry_cantidad_venta.get())

            if not nombre:
                raise ValueError("Elegí un producto")
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0")

            producto = self._productos_disponibles[nombre]
            if cantidad > producto.stock:
                raise ValueError(f"Stock insuficiente (disponible: {producto.stock})")

            self.carrito.append((producto.id, cantidad))
            self._refrescar_carrito()
            self.entry_cantidad_venta.delete(0, tk.END)

        except ValueError as e:
            messagebox.showerror("Datos inválidos", str(e))

    def _refrescar_carrito(self):
        self.tabla_carrito.delete(*self.tabla_carrito.get_children())
        total = 0.0
        for producto_id, cantidad in self.carrito:
            producto = self.tienda.buscar_producto(producto_id)
            subtotal = producto.precio * cantidad
            total += subtotal
            self.tabla_carrito.insert("", tk.END, values=(producto.nombre, cantidad, f"${subtotal:.2f}"))
        self.label_total_carrito.config(text=f"Total: ${total:.2f}")

    def _vaciar_carrito(self):
        self.carrito = []
        self._refrescar_carrito()

    def _confirmar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "Agregá al menos un producto")
            return
        try:
            venta = self.tienda.registrar_venta(self.carrito)
            guardar_tienda(self.tienda)
            messagebox.showinfo("Venta registrada", f"Venta por ${venta.total:.2f} registrada correctamente")
            self._vaciar_carrito()
            self._refrescar_combo_productos()
        except ValueError as e:
            messagebox.showerror("Error al registrar venta", str(e))

    # ---------------------------------------------------------------
    # TAB 3: Reportes
    # ---------------------------------------------------------------
    def _armar_tab_reportes(self):
        frame = self.tab_reportes

        self.label_total_facturado = ttk.Label(frame, text="", font=("Segoe UI", 14, "bold"))
        self.label_total_facturado.pack(pady=10)

        self.label_ganancia = ttk.Label(frame, text="")
        self.label_ganancia.pack(pady=5)

        self.label_mas_vendido = ttk.Label(frame, text="")
        self.label_mas_vendido.pack(pady=5)

        ttk.Label(frame, text="Productos con poco stock (<= 5):", font=("Segoe UI", 11, "bold")).pack(pady=(15, 5))
        self.lista_bajo_stock = tk.Listbox(frame, width=50)
        self.lista_bajo_stock.pack(pady=5)

        # TODO (Persona 2): sumar un gráfico con matplotlib embebido,
        # por ejemplo ventas por día usando FigureCanvasTkAgg.

    def _refrescar_reportes(self):
        reporte = Reporte(self.tienda)

        self.label_total_facturado.config(text=f"Total facturado: ${self.tienda.total_facturado():.2f}")
        self.label_ganancia.config(text=f"Ganancia estimada: ${reporte.ganancia_estimada():.2f}")

        mas_vendido = reporte.producto_mas_vendido()
        if mas_vendido:
            self.label_mas_vendido.config(text=f"Producto más vendido: {mas_vendido[0]} ({mas_vendido[1]} unidades)")
        else:
            self.label_mas_vendido.config(text="Todavía no hay ventas registradas")

        self.lista_bajo_stock.delete(0, tk.END)
        for producto in reporte.productos_bajo_stock():
            self.lista_bajo_stock.insert(tk.END, f"{producto.nombre}: quedan {producto.stock}")

    # ---------------------------------------------------------------
    def _al_cerrar(self):
        guardar_tienda(self.tienda)
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
