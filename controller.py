# controller.py
from models import Inventario, Producto, Carrito
import db

def cargar_inventario_desde_db() -> Inventario:
    inv = Inventario()
    rows = db.listar_productos()
    # Debug opcional
    # print("DEBUG productos desde DB:", rows)
    for r in rows:
        p = Producto(r['id'], r['nombre'], r['precio'], r['cantidad'])
        inv.agregar_producto(p)
    return inv


def crear_usuario_y_obtener_id(nombre: str, correo: str) -> int:
    return db.create_usuario(nombre, correo)


def crear_pedido_db(usuario_id: int, tipo_entrega: str, carrito: Carrito):
    # carrito.items es: {producto_id: cantidad}
    items = [(pid, qty) for pid, qty in carrito.items.items()]
    pid = db.crear_pedido(usuario_id, tipo_entrega, items)
    return pid
