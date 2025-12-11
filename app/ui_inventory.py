import tkinter as tk
from tkinter import ttk
from .db import get_conn


class InventoryWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Inventario de dispositivos")
        self.geometry("700x350")

        # Tabla principal: devices
        columns = ("id", "hostname", "ip", "modelo", "ios_version", "serial")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)

        self.tree.column("id", width=40)
        self.tree.column("hostname", width=120)
        self.tree.column("ip", width=120)
        self.tree.column("modelo", width=120)
        self.tree.column("ios_version", width=120)
        self.tree.column("serial", width=120)

        self.tree.pack(fill="both", expand=True, pady=10)

        self.cargar_datos()

    def cargar_datos(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, hostname, ip, modelo, ios_version, serial FROM devices")
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=row)
