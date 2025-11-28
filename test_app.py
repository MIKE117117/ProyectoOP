# tests/test_app.py
import unittest
from models import Producto, Carrito, Pedido, Inventario
import db

class TestModelsAndDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Se ejecuta una vez antes de todos los tests.
        Verifica/crea tablas en la BD real (MySQL).
        OJO: usa la misma BD configurada en db.py (proyecto2).
        """
        db.init_db()

    # ==== TESTS DE MODELOS (no usan BD) ====
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
        carrito.add(p1, 2)   # 2 * 10 = 20
        carrito.add(p2, 1)   # 1 *  5 = 5  -> total 25
        total = carrito.total(inv.productos)
        self.assertAlmostEqual(total, 25.0)
        carrito.remove(p1, 1)  # quita 1 de A -> queda 1*A + 1*B = 10 + 5 = 15
        self.assertAlmostEqual(carrito.total(inv.productos), 15.0)

    def test_pedido_agregar_y_remover(self):
        p = Producto(1, "X", 12.0, 10)
        pedido = Pedido(1, 1, "mostrador")
        pedido.agregar_item(p, 2)  # 2 * 12 = 24
        self.assertAlmostEqual(pedido.total, 24.0)
        pedido.remover_item(p, 1)  # queda 1 * 12 = 12
        self.assertAlmostEqual(pedido.total, 12.0)

    # ==== TESTS QUE USAN BD REAL (MySQL) ====
    def test_db_create_and_get_producto(self):
        pid = db.create_producto("Prueba DB", 9.9, 7)
        self.assertIsNotNone(pid, "create_producto regresó None, hay problema de conexión o inserción.")
        prod = db.get_producto(pid)
        self.assertIsNotNone(prod, "get_producto regresó None, no se encontró el producto.")
        self.assertEqual(prod['nombre'], "Prueba DB")
        self.assertEqual(float(prod['precio']), 9.9)
        self.assertEqual(int(prod['cantidad']), 7)

    def test_db_create_usuario_and_pedido(self):
        uid = db.create_usuario("Test User", "testuser@example.com")
        self.assertIsNotNone(uid, "create_usuario regresó None, hay problema de conexión o inserción.")

        # crear producto
        pid = db.create_producto("ItemPedido", 20.0, 5)
        self.assertIsNotNone(pid, "No se pudo crear el producto para el pedido.")

        # crear pedido con 1 item
        pedido_id = db.crear_pedido(uid, "mesa", [(pid, 1)])
        self.assertIsNotNone(pedido_id, "crear_pedido regresó None, hubo error al crear el pedido.")

        pedido = db.get_pedido(pedido_id)
        self.assertIsNotNone(pedido, "get_pedido regresó None, no se encontró el pedido.")
        self.assertEqual(pedido['usuario_id'], uid)
        self.assertIn('detalles', pedido)
        self.assertEqual(len(pedido['detalles']), 1)
        detalle = pedido['detalles'][0]
        self.assertEqual(detalle['producto_id'], pid)
        self.assertEqual(detalle['cantidad'], 1)

if __name__ == "__main__":
    unittest.main()
