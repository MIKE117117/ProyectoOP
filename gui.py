# gui.py
import tkinter as tk
from tkinter import messagebox, ttk
from models import Carrito
import controller
import db

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("McD - Prototipo POO")
        self.geometry("900x500")

        # Inicializar BD y cargar inventario
        db.init_db()
        self.inventario = controller.cargar_inventario_desde_db()

        # Si no hay productos iniciales, crear algunos
        if not self.inventario.productos:
            self._crear_productos_demo()
            self.inventario = controller.cargar_inventario_desde_db()

        self.usuario_id = None
        self.carrito = Carrito(usuario_id=0)

        self._crear_widgets()
        self._rellenar_lista_productos()

    def _crear_productos_demo(self):
        db.create_producto("Big Mac", 85.00, 10)
        db.create_producto("McNuggets 6pz", 60.00, 15)
        db.create_producto("Papas Medianas", 35.00, 20)
        db.create_producto("Refresco 500ml", 25.00, 25)
        db.create_producto("Helado", 20.00, 12)

    def _crear_widgets(self):
        # Frame izquierdo: lista de productos
        left = tk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

        tk.Label(left, text="Productos", font=("Arial", 12, "bold")).pack()
        self.lst_productos = tk.Listbox(left, width=45, height=20)
        self.lst_productos.pack()
        self.lst_productos.bind("<<ListboxSelect>>", self.event_seleccionar_producto)

        # Botón agregar al carrito
        self.btn_agregar = tk.Button(left, text="Agregar al carrito", command=self.event_agregar_al_carrito)
        self.btn_agregar.pack(pady=5)

        # Frame derecho: carrito y acciones
        right = tk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="Carrito", font=("Arial", 12, "bold")).pack()
        self.lst_carrito = tk.Listbox(right, width=50, height=10)
        self.lst_carrito.pack()

        # Formulario usuario
        form = tk.Frame(right)
        form.pack(pady=8, fill=tk.X)
        tk.Label(form, text="Nombre:").grid(row=0, column=0, sticky="e")
        self.entry_nombre = tk.Entry(form, width=30)
        self.entry_nombre.grid(row=0, column=1)

        tk.Label(form, text="Correo:").grid(row=1, column=0, sticky="e")
        self.entry_correo = tk.Entry(form, width=30)
        self.entry_correo.grid(row=1, column=1)

        # Tipo de entrega
        tk.Label(right, text="Tipo entrega:").pack()
        self.combo_entrega = ttk.Combobox(right, values=["mostrador", "mesa"], state="readonly")
        self.combo_entrega.set("mostrador")
        self.combo_entrega.pack()

        # Botones de acciones
        actions = tk.Frame(right)
        actions.pack(pady=6)
        self.btn_eliminar = tk.Button(actions, text="Eliminar seleccionado", command=self.event_eliminar_seleccion)
        self.btn_eliminar.grid(row=0, column=0, padx=4)

        self.btn_pagar = tk.Button(actions, text="Pagar", command=self.event_pagar)
        self.btn_pagar.grid(row=0, column=1, padx=4)

        self.btn_refrescar = tk.Button(actions, text="Refrescar inventario", command=self.event_refrescar)
        self.btn_refrescar.grid(row=0, column=2, padx=4)

        self.btn_historial = tk.Button(actions, text="Ver historial", command=self.event_ver_historial)
        self.btn_historial.grid(row=0, column=3, padx=4)

        # Label total
        self.lbl_total = tk.Label(right, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.lbl_total.pack(pady=6)

    def _rellenar_lista_productos(self):
        self.lst_productos.delete(0, tk.END)
        for p in self.inventario.listar():
            self.lst_productos.insert(
                tk.END,
                f"{p.producto_id} | {p.nombre} - ${p.precio:.2f} (Stock: {p.cantidad})"
            )

    # ==== Eventos ====
    def event_seleccionar_producto(self, evt):
        selection = self.lst_productos.curselection()
        if not selection:
            return
        # Podrías mostrar info si quieres
        # idx = selection[0]
        # val = self.lst_productos.get(idx)

    def event_agregar_al_carrito(self):
        sel = self.lst_productos.curselection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona un producto primero.")
            return
        idx = sel[0]
        line = self.lst_productos.get(idx)
        pid = int(line.split("|")[0].strip())
        prod = self.inventario.buscar(pid)
        if prod and prod.cantidad > 0:
            self.carrito.add(prod, 1)
            self._actualizar_lista_carrito()
        else:
            messagebox.showerror("Sin stock", "No hay stock disponible para ese producto.")

    def _actualizar_lista_carrito(self):
        self.lst_carrito.delete(0, tk.END)
        for pid, qty in self.carrito.items.items():
            prod = self.inventario.buscar(pid)
            if prod:
                self.lst_carrito.insert(
                    tk.END,
                    f"{prod.nombre} x{qty} - ${prod.precio * qty:.2f}"
                )
        total = self.carrito.total(self.inventario.productos)
        self.lbl_total.config(text=f"Total: ${total:.2f}")

    def event_eliminar_seleccion(self):
        sel = self.lst_carrito.curselection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona un ítem del carrito para eliminar.")
            return
        idx = sel[0]
        line = self.lst_carrito.get(idx)
        nombre = line.split(" x")[0]

        pid = None
        for p in self.inventario.listar():
            if p.nombre == nombre:
                pid = p.producto_id
                break
        if pid is not None:
            prod = self.inventario.buscar(pid)
            self.carrito.remove(prod, 1)
            self._actualizar_lista_carrito()

    def event_pagar(self):
        nombre = self.entry_nombre.get().strip()
        correo = self.entry_correo.get().strip()
        if not nombre or not correo:
            messagebox.showwarning("Faltan datos", "Ingresa nombre y correo.")
            return

        # Crear o reutilizar usuario
        uid = db.create_usuario(nombre, correo)
        if uid is None:
            messagebox.showerror("Error", "No se pudo crear u obtener el usuario.")
            return

        self.usuario_id = uid
        tipo_entrega = self.combo_entrega.get()

        if not self.carrito.items:
            messagebox.showinfo("Carrito vacío", "Agrega productos al carrito antes de pagar.")
            return

        pid = controller.crear_pedido_db(uid, tipo_entrega, self.carrito)
        if pid is None:
            messagebox.showerror("Error", "No se pudo crear el pedido.")
            return

        messagebox.showinfo("Pedido creado", f"Pedido #{pid} creado. Gracias por su compra.")
        # limpiar carrito
        self.carrito.clear()
        self._actualizar_lista_carrito()
        # refrescar inventario
        self.inventario = controller.cargar_inventario_desde_db()
        self._rellenar_lista_productos()

    def event_refrescar(self):
        self.inventario = controller.cargar_inventario_desde_db()
        self._rellenar_lista_productos()
        messagebox.showinfo("Refrescado", "Inventario actualizado desde la base de datos.")

    def event_ver_historial(self):
        """
        Muestra el historial de pedidos del usuario según el correo ingresado.
        """
        correo = self.entry_correo.get().strip()
        if not correo:
            messagebox.showwarning("Faltan datos", "Ingresa el correo del usuario para ver su historial.")
            return

        usuario = db.get_usuario_por_correo(correo)
        if not usuario:
            messagebox.showinfo("Sin datos", "No se encontró un usuario con ese correo.")
            return

        uid = usuario["id"]
        pedidos = controller.listar_pedidos_usuario(uid)
        if not pedidos:
            messagebox.showinfo("Sin pedidos", "Este usuario no tiene pedidos registrados.")
            return

        win = tk.Toplevel(self)
        win.title(f"Historial de pedidos - {usuario['nombre']}")
        win.geometry("600x300")

        cols = ("id", "tipo_entrega", "total", "estado", "created_at")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        tree.heading("id", text="ID")
        tree.heading("tipo_entrega", text="Entrega")
        tree.heading("total", text="Total")
        tree.heading("estado", text="Estado")
        tree.heading("created_at", text="Fecha")

        for p in pedidos:
            fecha = p["created_at"]
            if hasattr(fecha, "strftime"):
                fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_str = str(fecha)

            tree.insert(
                "",
                tk.END,
                values=(
                    p["id"],
                    p["tipo_entrega"],
                    float(p["total"]),
                    p["estado"],
                    fecha_str
                )
            )
