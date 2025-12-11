import tkinter as tk
from tkinter import messagebox

from .ui_find_mac import FindMacWindow
from .ui_inventory import InventoryWindow
from .ansible_service import correr_ansible_y_actualizar_db


class MainMenu(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)

        self.title("Proyecto redes - Menú principal")
        self.resizable(False, False)

        # ---------- Botones ----------
        btn_find = tk.Button(self, text="Buscar endpoint (IP / MAC)", width=35,
                             command=self.abrir_find_mac)
        btn_find.pack(padx=20, pady=10)

        btn_inv = tk.Button(self, text="Mostrar inventario de dispositivos", width=35,
                            command=self.abrir_inventario)
        btn_inv.pack(padx=20, pady=10)

        btn_ansible = tk.Button(self, text="Generar inventario (Ansible)", width=35,
                                command=self.generar_inventario)
        btn_ansible.pack(padx=20, pady=10)

        btn_salir = tk.Button(self, text="Salir", width=35, command=self.cerrar_todo)
        btn_salir.pack(padx=20, pady=20)

    # ---------- Acciones de botones ----------

    def abrir_find_mac(self):
        FindMacWindow(self)

    def abrir_inventario(self):
        InventoryWindow(self)

    def generar_inventario(self):
        ok, msg = correr_ansible_y_actualizar_db()
        if ok:
            messagebox.showinfo("Inventario", msg)
        else:
            messagebox.showerror("Error", msg)

    def cerrar_todo(self):
        # Cierra el menú y también el root principal
        root = self.master
        self.destroy()
        if root is not None:
            root.destroy()
