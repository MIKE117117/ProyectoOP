# models.py
from typing import List, Dict
from datetime import datetime

class Producto:
    def __init__(self, producto_id: int, nombre: str, precio: float, cantidad: int):
        self.producto_id = producto_id
        self.nombre = nombre
        self.precio = float(precio)
        self.cantidad = int(cantidad)

    def actualizar_stock(self, delta: int):
        self.cantidad += int(delta)
        if self.cantidad < 0:
            self.cantidad = 0

    def __repr__(self):
        return f"Producto({self.producto_id}, {self.nombre}, {self.precio}, stock={self.cantidad})"

class Usuario:
    def __init__(self, usuario_id: int, nombre: str, correo: str):
        self.usuario_id = usuario_id
        self.nombre = nombre
        self.correo = correo

    def mostrar_datos(self):
        return f"{self.nombre} <{self.correo}>"

class Empleado(Usuario):
    def __init__(self, usuario_id: int, nombre: str, correo: str, puesto: str):
        super().__init__(usuario_id, nombre, correo)
        self.puesto = puesto

    def preparar_pedido(self, pedido_id: int):
        return f"Empleado {self.nombre} preparando pedido #{pedido_id}"

class Pago:
    def __init__(self, metodo: str, monto: float, aprobado: bool=False):
        self.metodo = metodo
        self.monto = float(monto)
        self.aprobado = aprobado
        self.fecha = datetime.now()

    def aprobar(self):
        self.aprobado = True
        return self.aprobado

class Pedido:
    def __init__(self, pedido_id: int, usuario_id: int, tipo_entrega: str="mostrador"):
        self.pedido_id = pedido_id
        self.usuario_id = usuario_id
        self.tipo_entrega = tipo_entrega  # 'mostrador' o 'mesa'
        self.items: Dict[int, int] = {}  # producto_id -> cantidad
        self.total = 0.0
        self.estado = "creado"  # creado, pagado, listo, entregado
        self.created_at = datetime.now()

    def agregar_item(self, producto: Producto, cantidad: int=1):
        cantidad = int(cantidad)
        if producto.producto_id in self.items:
            self.items[producto.producto_id] += cantidad
        else:
            self.items[producto.producto_id] = cantidad
        self.total += producto.precio * cantidad

    def remover_item(self, producto: Producto, cantidad: int=1):
        pid = producto.producto_id
        cantidad = int(cantidad)
        if pid in self.items:
            self.items[pid] -= cantidad
            if self.items[pid] <= 0:
                del self.items[pid]
            self.total = max(0.0, self.total - producto.precio * cantidad)

    def marcar_pagado(self):
        self.estado = "pagado"

    def marcar_listo(self):
        self.estado = "listo"

    def __repr__(self):
        return f"Pedido(id={self.pedido_id}, usuario={self.usuario_id}, total={self.total}, estado={self.estado})"

class Carrito:
    def __init__(self, usuario_id: int):
        self.usuario_id = usuario_id
        self.items: Dict[int, int] = {}  # producto_id -> cantidad

    def add(self, producto: Producto, cantidad: int=1):
        cantidad = int(cantidad)
        self.items[producto.producto_id] = self.items.get(producto.producto_id, 0) + cantidad

    def remove(self, producto: Producto, cantidad: int=1):
        pid = producto.producto_id
        cantidad = int(cantidad)
        if pid in self.items:
            self.items[pid] -= cantidad
            if self.items[pid] <= 0:
                del self.items[pid]

    def clear(self):
        self.items.clear()

    def total(self, productos: Dict[int, Producto]):
        tot = 0.0
        for pid, qty in self.items.items():
            prod = productos.get(pid)
            if prod:
                tot += prod.precio * qty
        return tot

class Inventario:
    def __init__(self):
        # product_id -> Producto
        self.productos: Dict[int, Producto] = {}

    def agregar_producto(self, producto: Producto):
        self.productos[producto.producto_id] = producto

    def buscar(self, producto_id: int):
        return self.productos.get(producto_id)

    def listar(self):
        return list(self.productos.values())

    def actualizar_stock(self, producto_id: int, nueva_cantidad: int):
        p = self.productos.get(producto_id)
        if p:
            p.cantidad = int(nueva_cantidad)
            return True
        return False
