# db.py
import sqlite3
from typing import List, Tuple, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_db.sqlite3")

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    cantidad INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    tipo_entrega TEXT NOT NULL,
    total REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'creado',
    created_at TEXT NOT NULL,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS detalle_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY(producto_id) REFERENCES productos(id)
);
"""

def get_conn(path=DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(path=DB_PATH):
    conn = get_conn(path)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()

# CRUD usuarios
def create_usuario(nombre: str, correo: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (nombre, correo) VALUES (?, ?)", (nombre, correo))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def get_usuario(uid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = ?", (uid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# CRUD productos
def create_producto(nombre: str, precio: float, cantidad: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO productos (nombre, precio, cantidad) VALUES (?, ?, ?)", (nombre, precio, cantidad))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def listar_productos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_producto(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM productos WHERE id = ?", (pid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_producto_stock(pid: int, nueva_cantidad: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (nueva_cantidad, pid))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed

# CRUD pedidos (simplificado)
from datetime import datetime
def crear_pedido(usuario_id: int, tipo_entrega: str, items: List[Tuple[int,int]]):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO pedidos (usuario_id, tipo_entrega, total, estado, created_at) VALUES (?, ?, ?, ?, ?)",
                (usuario_id, tipo_entrega, 0.0, 'creado', now))
    pid = cur.lastrowid
    total = 0.0
    for producto_id, cantidad in items:
        prod = get_producto(producto_id)
        if not prod:
            continue
        precio_unit = prod['precio']
        cur.execute("INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                    (pid, producto_id, cantidad, precio_unit))
        total += precio_unit * cantidad
        # actualizar stock
        new_stock = prod['cantidad'] - cantidad
        if new_stock < 0:
            new_stock = 0
        cur.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (new_stock, producto_id))
    cur.execute("UPDATE pedidos SET total = ? WHERE id = ?", (total, pid))
    conn.commit()
    conn.close()
    return pid

def get_pedido(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos WHERE id = ?", (pid,))
    p = cur.fetchone()
    if not p:
        conn.close()
        return None
    cur.execute("SELECT * FROM detalle_pedido WHERE pedido_id = ?", (pid,))
    detalles = [dict(r) for r in cur.fetchall()]
    conn.close()
    res = dict(p)
    res['detalles'] = detalles
    return res
