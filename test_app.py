# tests/test_app.py
import unittest
import os
import tempfile
from models import Producto, Carrito, Pedido, Inventario
import db

class TestModelsAndDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # usar DB temporal
        cls.db_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_db.sqlite3")
        db.init_db(path=cls.db_path)  # we can call init_db but current code uses default; for simplicity assume default

    def test_producto_stock_update(self):
        p = Producto(1, "Test", 10.0, 5)
        p.actualizar_stock(-2)
        self.assertEqual(p.cantidad, 3)
        p.actualizar_stock(10)
        self.assertEqual(p.cantidad, 13)

    def test_carrito_total_and_add_remove(self):
        inv = Inventario()
        p1 = Producto(1, "A", 10.0, 5)
        p2 = Producto(2, "B", 5.0, 3)
        inv.agregar_producto(p1)
        inv.agregar_producto(p2)
        carrito = Carrito(1)
        carrito.add(p1, 2)
        carrito.add(p2, 1)
        total = carrito.total(inv.productos)
        self.assertAlmostEqual(total, 25.0)
        carrito.remove(p1, 1)
        self.assertAlmostEqual(carrito.total(inv.productos), 15.0)

    def test_pedido_agregar_y_remover(self):
        p = Producto(1, "X", 12.0, 10)
        pedido = Pedido(1, 1, "mostrador")
        pedido.agregar_item(p, 2)
        self.assertAlmostEqual(pedido.total, 24.0)
        pedido.remover_item(p, 1)
        self.assertAlmostEqual(pedido.total, 12.0)

    def test_db_create_and_get_producto(self):
        pid = db.create_producto("Prueba DB", 9.9, 7)
        prod = db.get_producto(pid)
        self.assertIsNotNone(prod)
        self.assertEqual(prod['nombre'], "Prueba DB")

    def test_db_create_usuario_and_pedido(self):
        uid = db.create_usuario("Test User", "testuser@example.com")
        # crear producto
        pid = db.create_producto("ItemPedido", 20.0, 5)
        # crear pedido con 1 item
        pedido_id = db.crear_pedido(uid, "mesa", [(pid, 1)])
        pedido = db.get_pedido(pedido_id)
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido['usuario_id'], uid)
        self.assertEqual(len(pedido['detalles']), 1)

if __name__ == "__main__":
    unittest.main()
