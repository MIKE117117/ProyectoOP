import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling

load_dotenv()

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
    try:
        if pool is None:
            raise Exception("El pool no está inicializado.")
        return pool.get_connection()
    except Error as e:
        print(f"Error al obtener conexión: {e}")
        return None


def create_usuario(nombre, correo):
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
        return None

    finally:
        cur.close()
        conn.close()
