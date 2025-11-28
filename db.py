# db.py
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling
from datetime import datetime

load_dotenv()

# Config de conexión a MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "database": os.getenv("DB_NAME", "proyecto2"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "MC_Pedro1171"),
    "autocommit": False,
    "charset": "utf8mb4",
}

POOL_NAME = os.getenv("POOL_NAME", "proyecto2_pool")
POOL_SIZE = int(os.getenv("POOL_SIZE", 5))

try:
    pool = pooling.MySQLConnectionPool(
        pool_name=POOL_NAME,
        pool_size=POOL_SIZE,
        **DB_CONFIG
    )
    print(f"Pool de conexiones '{POOL_NAME}' creado exitosamente.")
except Error as e:
    print(f"Error al crear el pool de conexiones: {e}")
    pool = None


def get_conn():
    if pool is None:
        print("Error: pool no inicializado.")
        return None
    try:
        return pool.get_connection()
    except Error as e:
        print("Error al obtener conexión:", e)
        return None


# ========== INIT DB ==========
def init_db():
    """
    Crea las tablas si no existen.
    Asegúrate de que la estructura coincida con tu diseño.
    """
    conn = get_conn()
    if not conn:
        print("No se pudo obtener conexión para init_db")
        return

    try:
        cur = conn.cursor()

        # Tabla usuarios (correo único)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                correo VARCHAR(150) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla productos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                precio DECIMAL(10,2) NOT NULL,
                cantidad INT NOT NULL DEFAULT 0
            )
        """)

        # Tabla pedidos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                tipo_entrega VARCHAR(20) NOT NULL,
                total DECIMAL(10,2) NOT NULL DEFAULT 0,
                estado VARCHAR(20) NOT NULL DEFAULT 'creado',
                created_at DATETIME NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)

        # Tabla detalle_pedido
        cur.execute("""
            CREATE TABLE IF NOT EXISTS detalle_pedido (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pedido_id INT NOT NULL,
                producto_id INT NOT NULL,
                cantidad INT NOT NULL,
                precio_unitario DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)

        conn.commit()
        print("Tablas verificadas/creadas correctamente.")

    except Error as e:
        print("Error en init_db:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()


# ========== CRUD USUARIOS ==========
def get_usuario(uid):
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (uid,))
        row = cur.fetchone()
        return row
    except Error as e:
        print("Error al obtener usuario:", e)
        return None
    finally:
        cur.close()
        conn.close()


def get_usuario_por_correo(correo):
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        row = cur.fetchone()
        return row
    except Error as e:
        print("Error al obtener usuario por correo:", e)
        return None
    finally:
        cur.close()
        conn.close()


def create_usuario(nombre, correo):
    """
    Crea un usuario nuevo si el correo no existe.
    Si el correo ya existe, regresa el id del usuario existente.
    """
    conn = get_conn()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        sql = "INSERT INTO usuarios (nombre, correo) VALUES (%s, %s)"
        cur.execute(sql, (nombre, correo))
        conn.commit()
        return cur.lastrowid

    except Error as e:
        print("Error al crear usuario:", e)
        # 1062 = Duplicate entry
        if e.errno == 1062:
            # ya existe ese correo, regresamos su id
            try:
                cur2 = conn.cursor(dictionary=True)
                cur2.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
                row = cur2.fetchone()
                if row:
                    return row["id"]
            except Error as e2:
                print("Error al obtener usuario existente:", e2)
                return None
        return None

    finally:
        cur.close()
        conn.close()


# ========== CRUD PRODUCTOS ==========
def create_producto(nombre, precio, cantidad):
    conn = get_conn()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO productos (nombre, precio, cantidad) VALUES (%s, %s, %s)",
            (nombre, precio, cantidad)
        )
        conn.commit()
        pid = cur.lastrowid
        return pid
    except Error as e:
        print("Error al crear producto:", e)
        return None
    finally:
        cur.close()
        conn.close()


def listar_productos():
    conn = get_conn()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM productos")
        rows = cur.fetchall()
        return rows
    except Error as e:
        print("Error al listar productos:", e)
        return []
    finally:
        cur.close()
        conn.close()


def get_producto(pid):
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM productos WHERE id = %s", (pid,))
        row = cur.fetchone()
        return row
    except Error as e:
        print("Error al obtener producto:", e)
        return None
    finally:
        cur.close()
        conn.close()


def update_producto_stock(pid, nueva_cantidad):
    conn = get_conn()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("UPDATE productos SET cantidad = %s WHERE id = %s",
                    (nueva_cantidad, pid))
        conn.commit()
        changed = cur.rowcount > 0
        return changed
    except Error as e:
        print("Error al actualizar stock:", e)
        return False
    finally:
        cur.close()
        conn.close()


# ========== CRUD PEDIDOS ==========
def crear_pedido(usuario_id, tipo_entrega, items):
    """
    items es una lista de tuplas: (producto_id, cantidad)
    """
    conn = get_conn()
    if not conn:
        return None

    try:
        cur = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Crear pedido
        cur.execute(
            "INSERT INTO pedidos (usuario_id, tipo_entrega, total, estado, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (usuario_id, tipo_entrega, 0, 'creado', now)
        )
        pid = cur.lastrowid

        total = 0

        for producto_id, cantidad in items:
            prod = get_producto(producto_id)
            if not prod:
                continue

            precio_unit = float(prod["precio"])

            # detalle
            cur.execute(
                "INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad, precio_unitario) "
                "VALUES (%s, %s, %s, %s)",
                (pid, producto_id, cantidad, precio_unit)
            )

            total += precio_unit * cantidad

            # actualizar stock
            new_stock = int(prod["cantidad"]) - cantidad
            if new_stock < 0:
                new_stock = 0

            cur.execute(
                "UPDATE productos SET cantidad = %s WHERE id = %s",
                (new_stock, producto_id)
            )

        # guardar total
        cur.execute("UPDATE pedidos SET total = %s WHERE id = %s", (total, pid))

        conn.commit()
        return pid

    except Error as e:
        print("Error al crear pedido:", e)
        conn.rollback()
        return None

    finally:
        cur.close()
        conn.close()


def get_pedido(pid):
    conn = get_conn()
    if not conn:
        return None

    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM pedidos WHERE id = %s", (pid,))
        pedido = cur.fetchone()

        if not pedido:
            return None

        cur.execute("SELECT * FROM detalle_pedido WHERE pedido_id = %s", (pid,))
        detalles = cur.fetchall()

        pedido["detalles"] = detalles
        return pedido

    except Error as e:
        print("Error al obtener pedido:", e)
        return None

    finally:
        cur.close()
        conn.close()


def listar_pedidos_por_usuario(usuario_id):
    """
    Regresa una lista de pedidos con datos básicos para un usuario dado.
    """
    conn = get_conn()
    if not conn:
        return []

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, tipo_entrega, total, estado, created_at
            FROM pedidos
            WHERE usuario_id = %s
            ORDER BY created_at DESC
        """, (usuario_id,))
        rows = cur.fetchall()
        return rows
    except Error as e:
        print("Error al listar pedidos por usuario:", e)
        return []
    finally:
        cur.close()
        conn.close()
