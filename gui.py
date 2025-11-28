# gui.py
import tkinter as tk
from tkinter import messagebox, ttk
from models import Producto, Carrito
import controller
import db


class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.title("Login / Registro McD")
        self.geometry("400x250")
        self.on_login_success = on_login_success

        tk.Label(self, text="Nombre:").pack(pady=5)
        self.entry_nombre = tk.Entry(self)
        self.entry_nombre.pack()

        tk.Label(self, text="Correo:").pack(pady=5)
        self.entry_correo = tk.Entry(self)
        self.entry_correo.pack()

        # Rol solo se usa para registrar admin manual, normalmente será cliente
        tk.Label(self, text="Rol (cliente/admin):").pack(pady=5)
        self.entry_rol = tk.Entry(self)
        self.entry_rol.insert(0, "cliente")
        self.entry_rol.pack()

        frame_btns = tk.Frame(self)
        frame_btns.pack(pady=10)

        btn_registrar = tk.Button(frame_btns, text="Registrarse", command=self.registrar)
        btn_registrar.grid(row=0, column=0, padx=5)

        btn_login = tk.Button(frame_btns, text="Iniciar sesión", command=self.login)
        btn_login.grid(row=0, column=1, padx=5)

    def registrar(self):
        nombre = self.entry_nombre.get().strip()
        correo = self.entry_correo.get().strip()
        rol = self.entry_rol.get().strip().lower()

        if not nombre or not correo:
            messagebox.showwarning("Datos faltantes", "Por favor ingresa nombre y correo.")
            return

        if rol not in ("cliente", "admin"):
            rol = "cliente"

        uid = controller.crear_usuario_y_obtener_id(nombre, correo, rol)
        if uid is None:
            messagebox.showerror("Error", "No se pudo registrar el usuario.")
            return

        user = controller.obtener_usuario_por_correo(correo)
        if not user:
            messagebox.showerror("Error", "No se pudo recuperar el usuario después de registrarlo.")
            return

        messagebox.showinfo("Registro", f"Usuario registrado / encontrado: {user.mostrar_datos()}")
        self.on_login_success(user)
        self.destroy()

    def login(self):
        correo = self.entry_correo.get().strip()
        if not correo:
            messagebox.showwarning("Datos faltantes", "Ingresa el correo para iniciar sesión.")
            return
        user = controller.obtener_usuario_por_correo(correo)
        if not user:
            messagebox.showerror("No encontrado", "No existe un usuario con ese correo. Regístrate primero.")
            return
        messagebox.showinfo("Login correcto", f"Bienvenido {user.mostrar_datos()}")
        self.on_login_success(user)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("McD - Prototipo POO")
        self.geometry("900x550")

        db.init_db()
        self.inventario = controller.cargar_inventario_desde_db()
        if not self.inventario.productos:
            self._crear_productos_demo()
            self.inventario = controller.cargar_inventario_desde_db()

        self.usuario = None
        self.carrito = None

        self._crear_menu()
        self._crear_widgets_principales()

        # Mostrar ventana de login/registro al inicio
        self.after(500, self._abrir_login_inicial)

    def _abrir_login_inicial(self):
        LoginWindow(self, self._on_login_success)

    def _on_login_success(self, usuario):
        self.usuario = usuario
        self.carrito = Carrito(usuario_id=usuario.usuario_id)
        self.lbl_usuario.config(text=f"Usuario: {usuario.mostrar_datos()}")

        if usuario.rol == "admin":
            self.btn_admin.config(state=tk.NORMAL)
        else:
            self.btn_admin.config(state=tk.DISABLED)

    def _crear_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Login / Cambio de usuario", command=self._abrir_login_inicial)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)

    def _crear_productos_demo(self):
        db.create_producto("Big Mac", 85.00, 10)
        db.create_producto("McNuggets 6pz", 60.00, 15)
        db.create_producto("Papas Medianas", 35.00, 20)
        db.create_producto("Refresco 500ml", 25.00, 25)
        db.create_producto("Helado", 20.00, 12)

    def _crear_widgets_principales(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, pady=5)
        self.lbl_usuario = tk.Label(top, text="Usuario: (no autenticado)")
        self.lbl_usuario.pack(side=tk.LEFT, padx=10)

        self.btn_admin = tk.Button(top, text="Panel Admin", state=tk.DISABLED, command=self._abrir_panel_admin)
        self.btn_admin.pack(side=tk.RIGHT, padx=10)

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ========== Panel izquierdo: productos ==========
        left = tk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10)

        tk.Label(left, text="Productos").pack()
        self.lst_productos = tk.Listbox(left, width=40, height=20)
        self.lst_productos.pack()
        self.lst_productos.bind("<<ListboxSelect>>", self.event_seleccionar_producto)

        self.btn_agregar = tk.Button(left, text="Agregar al carrito", command=self.event_agregar_al_carrito)
        self.btn_agregar.pack(pady=5)

        # ========== Panel derecho: carrito + historial ==========
        right = tk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # Carrito
        tk.Label(right, text="Carrito").pack()
        self.lst_carrito = tk.Listbox(right, width=50, height=10)
        self.lst_carrito.pack()

        form = tk.Frame(right)
        form.pack(pady=5)

        tk.Label(form, text="Tipo entrega:").grid(row=0, column=0, sticky="e")
        self.combo_entrega = ttk.Combobox(form, values=["mostrador", "mesa"], state="readonly")
        self.combo_entrega.set("mostrador")
        self.combo_entrega.grid(row=0, column=1, padx=5)

        actions = tk.Frame(right)
        actions.pack(pady=5)

        self.btn_eliminar = tk.Button(actions, text="Eliminar seleccionado", command=self.event_eliminar_seleccion)
        self.btn_eliminar.grid(row=0, column=0, padx=5)
        self.btn_pagar = tk.Button(actions, text="Pagar", command=self.event_pagar)
        self.btn_pagar.grid(row=0, column=1, padx=5)
        self.btn_refrescar = tk.Button(actions, text="Refrescar inventario", command=self.event_refrescar)
        self.btn_refrescar.grid(row=0, column=2, padx=5)

        self.lbl_total = tk.Label(right, text="Total: $0.00")
        self.lbl_total.pack(pady=5)

        # Historial de compras
        frame_hist = tk.LabelFrame(right, text="Historial de compras")
        frame_hist.pack(fill=tk.BOTH, expand=True, pady=10)

        self.lst_historial = tk.Listbox(frame_hist, height=8)
        self.lst_historial.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_hist = tk.Scrollbar(frame_hist, orient=tk.VERTICAL, command=self.lst_historial.yview)
        scroll_hist.pack(side=tk.RIGHT, fill=tk.Y)
        self.lst_historial.config(yscrollcommand=scroll_hist.set)

        self.lst_historial.bind("<<ListboxSelect>>", self.event_ver_detalle_pedido)

        self._rellenar_lista_productos()

    # ================== Panel Admin ==================
    def _abrir_panel_admin(self):
        if not self.usuario or self.usuario.rol != "admin":
            messagebox.showwarning("Acceso restringido", "Solo el administrador puede acceder a este panel.")
            return

        win = tk.Toplevel(self)
        win.title("Panel de Administración")
        win.geometry("500x400")

        frame_list = tk.Frame(win)
        frame_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(frame_list, text="Productos existentes").pack()
        lst_admin = tk.Listbox(frame_list, width=30)
        lst_admin.pack(fill=tk.BOTH, expand=True)

        def refrescar_admin_list():
            lst_admin.delete(0, tk.END)
            productos = db.listar_productos()
            for p in productos:
                lst_admin.insert(tk.END, f"{p['id']} | {p['nombre']} - ${p['precio']} (Stock: {p['cantidad']})")

        refrescar_admin_list()

        frame_form = tk.Frame(win)
        frame_form.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        tk.Label(frame_form, text="Nombre:").grid(row=0, column=0, sticky="e")
        entry_nombre = tk.Entry(frame_form)
        entry_nombre.grid(row=0, column=1)

        tk.Label(frame_form, text="Precio:").grid(row=1, column=0, sticky="e")
        entry_precio = tk.Entry(frame_form)
        entry_precio.grid(row=1, column=1)

        tk.Label(frame_form, text="Cantidad:").grid(row=2, column=0, sticky="e")
        entry_cantidad = tk.Entry(frame_form)
        entry_cantidad.grid(row=2, column=1)

        def limpiar_form():
            entry_nombre.delete(0, tk.END)
            entry_precio.delete(0, tk.END)
            entry_cantidad.delete(0, tk.END)

        def evento_agregar_producto():
            nombre = entry_nombre.get().strip()
            try:
                precio = float(entry_precio.get())
                cantidad = int(entry_cantidad.get())
            except ValueError:
                messagebox.showerror("Error", "Precio o cantidad inválidos.")
                return
            if not nombre:
                messagebox.showwarning("Dato faltante", "El nombre no puede estar vacío.")
                return
            pid = db.create_producto(nombre, precio, cantidad)
            if pid:
                messagebox.showinfo("OK", "Producto creado correctamente.")
                refrescar_admin_list()
                self.inventario = controller.cargar_inventario_desde_db()
                self._rellenar_lista_productos()
                limpiar_form()
            else:
                messagebox.showerror("Error", "No se pudo crear el producto.")

        def evento_editar_producto():
            sel = lst_admin.curselection()
            if not sel:
                messagebox.showwarning("Selecciona", "Selecciona un producto para editar.")
                return
            idx = sel[0]
            line = lst_admin.get(idx)
            pid = int(line.split("|")[0].strip())
            prod = db.get_producto(pid)
            if not prod:
                messagebox.showerror("Error", "No se encontró el producto.")
                return
            # llenar form
            entry_nombre.delete(0, tk.END)
            entry_nombre.insert(0, prod['nombre'])
            entry_precio.delete(0, tk.END)
            entry_precio.insert(0, str(prod['precio']))
            entry_cantidad.delete(0, tk.END)
            entry_cantidad.insert(0, str(prod['cantidad']))

            def guardar_cambios():
                nombre = entry_nombre.get().strip()
                try:
                    precio = float(entry_precio.get())
                    cantidad = int(entry_cantidad.get())
                except ValueError:
                    messagebox.showerror("Error", "Precio o cantidad inválidos.")
                    return
                ok = controller.actualizar_producto_db(pid, nombre, precio, cantidad)
                if ok:
                    messagebox.showinfo("OK", "Producto actualizado.")
                    refrescar_admin_list()
                    self.inventario = controller.cargar_inventario_desde_db()
                    self._rellenar_lista_productos()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el producto.")

            btn_guardar.config(command=guardar_cambios)

        btn_agregar = tk.Button(frame_form, text="Agregar", command=evento_agregar_producto)
        btn_agregar.grid(row=3, column=0, pady=10)

        btn_editar = tk.Button(frame_form, text="Editar seleccionado", command=evento_editar_producto)
        btn_editar.grid(row=3, column=1, pady=10)

        btn_guardar = tk.Button(frame_form, text="Guardar cambios")
        btn_guardar.grid(row=4, column=0, columnspan=2, pady=10)

    # ================== Productos / Carrito ==================
    def _rellenar_lista_productos(self):
        self.lst_productos.delete(0, tk.END)
        for p in self.inventario.listar():
            self.lst_productos.insert(
                tk.END,
                f"{p.producto_id} | {p.nombre} - ${p.precio:.2f} (Stock: {p.cantidad})"
            )

    def event_seleccionar_producto(self, evt):
        # aquí podrías mostrar detalles si quieres
        pass

    def event_agregar_al_carrito(self):
        if not self.usuario:
            messagebox.showwarning("Sesión", "Debes iniciar sesión para comprar.")
            return

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
                self.lst_carrito.insert(tk.END, f"{prod.nombre} x{qty} - ${prod.precio*qty:.2f}")
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
        if not self.usuario:
            messagebox.showwarning("Sesión", "Debes iniciar sesión para pagar.")
            return

        if not self.carrito.items:
            messagebox.showinfo("Carrito vacío", "Agrega productos al carrito antes de pagar.")
            return

        tipo_entrega = self.combo_entrega.get()
        pid = controller.crear_pedido_db(self.usuario.usuario_id, tipo_entrega, self.carrito)
        if not pid:
            messagebox.showerror("Error", "No se pudo crear el pedido.")
            return

        messagebox.showinfo("Pedido creado", f"Pedido #{pid} creado. Gracias por su compra.")
        self.carrito.clear()
        self._actualizar_lista_carrito()

        self.inventario = controller.cargar_inventario_desde_db()
        self._rellenar_lista_productos()

        self._actualizar_historial()

    def event_refrescar(self):
        self.inventario = controller.cargar_inventario_desde_db()
        self._rellenar_lista_productos()
        messagebox.showinfo("Refrescado", "Inventario actualizado desde la base de datos.")

    # ================== Historial ==================
    def _actualizar_historial(self):
        if not self.usuario:
            return
        self.lst_historial.delete(0, tk.END)
        pedidos = controller.listar_historial_por_usuario(self.usuario.usuario_id)
        for p in pedidos:
            self.lst_historial.insert(
                tk.END,
                f"{p['id']} | {p['created_at']} | {p['tipo_entrega']} | ${p['total']:.2f}"
            )

    def event_ver_detalle_pedido(self, evt):
        sel = self.lst_historial.curselection()
        if not sel:
            return
        idx = sel[0]
        line = self.lst_historial.get(idx)
        pid = int(line.split("|")[0].strip())

        pedido = db.get_pedido(pid)
        if not pedido:
            messagebox.showerror("Error", "No se encontró el pedido.")
            return

        detalles = pedido.get("detalles", [])
        msg = f"Pedido #{pedido['id']}\nTipo entrega: {pedido['tipo_entrega']}\nTotal: ${pedido['total']}\n\nDetalle:\n"
        for d in detalles:
            prod = db.get_producto(d['producto_id'])
            nombre = prod['nombre'] if prod else f"Prod {d['producto_id']}"
            msg += f"- {nombre} x{d['cantidad']} @ ${d['precio_unitario']}\n"

        messagebox.showinfo("Detalle de pedido", msg)
