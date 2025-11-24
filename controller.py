# controller.py parte 2
from models import Inventario, Producto, Carrito, Usuario
import db
from typing import Dict, List


def cargar_inventario_desde_db() -> Inventario:
    inv = Inventario()
    rows = db.listar_productos()
    for r in rows:
        p = Producto(r['id'], r['nombre'], r['precio'], r['cantidad'])
        inv.agregar_producto(p)
    return inv


def crear_usuario_y_obtener_id(nombre: str, correo: str, rol: str = "cliente") -> int:
    return db.create_usuario(nombre, correo, rol)


def obtener_usuario_por_correo(correo: str):
    row = db.get_usuario_por_correo(correo)
    if not row:
        return None
    return Usuario(row["id"], row["nombre"], row["correo"], row.get("rol", "cliente"))


def crear_pedido_db(usuario_id: int, tipo_entrega: str, carrito: Carrito):
    items = [(pid, qty) for pid, qty in carrito.items.items()]
    pid = db.crear_pedido(usuario_id, tipo_entrega, items)
    return pid


def listar_historial_por_usuario(usuario_id: int):
    """
    Regresa la lista de pedidos (básicos) de un usuario para mostrar en el GUI.
    """
    return db.listar_pedidos_por_usuario(usuario_id)


def actualizar_producto_db(pid: int, nombre: str, precio: float, cantidad: int) -> bool:
    return db.update_producto(pid, nombre, precio, cantidad)
