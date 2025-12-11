import tkinter as tk
from tkinter import messagebox
from . import vlan_service


class ChangeVlanWindow(tk.Toplevel):
    def __init__(self, master, switch_ip=None, interfaz=None):
        super().__init__(master)
        self.title("Cambiar VLAN de un puerto")
        self.resizable(False, False)

        # ----- Switch IP -----
        tk.Label(self, text="Switch IP:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_ip = tk.Entry(self, width=20)
        self.entry_ip.grid(row=0, column=1, padx=10, pady=10)

        # ----- Interfaz -----
        tk.Label(self, text="Interfaz (ej. Fa1/0/2):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.entry_if = tk.Entry(self, width=20)
        self.entry_if.grid(row=1, column=1, padx=10, pady=10)

        # ----- VLAN nueva -----
        tk.Label(self, text="VLAN nueva:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.entry_vlan = tk.Entry(self, width=10)
        self.entry_vlan.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.entry_vlan.insert(0, "10")

        # ----- Botón Aplicar -----
        btn_aplicar = tk.Button(self, text="Aplicar cambio", command=self.ejecutar_cambio)
        btn_aplicar.grid(row=3, column=0, columnspan=2, padx=10, pady=15)

        # ENTER hace lo mismo que el botón
        self.bind("<Return>", lambda event: self.ejecutar_cambio())

        # Pre-cargar datos si vienen de una búsqueda
        if switch_ip:
            self.entry_ip.delete(0, tk.END)
            self.entry_ip.insert(0, switch_ip)
            # bloquear edición si viene de Find
            self.entry_ip.config(state="readonly")

        if interfaz:
            self.entry_if.delete(0, tk.END)
            self.entry_if.insert(0, interfaz)
            # bloquear edición si viene de Find
            self.entry_if.config(state="readonly")

        # Foco inicial: VLAN
        self.entry_vlan.focus()

    def ejecutar_cambio(self):
        # Aunque estén en readonly, .get() funciona
        switch_ip = self.entry_ip.get().strip()
        interfaz = self.entry_if.get().strip()
        vlan = self.entry_vlan.get().strip()

        if not switch_ip or not interfaz or not vlan:
            messagebox.showerror("Error", "Faltan datos (IP, interfaz o VLAN).")
            return

        try:
            salida = vlan_service.cambiar_vlan(switch_ip, interfaz, vlan)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al ejecutar cambio:\n{e}")
            return

        messagebox.showinfo(
            "Éxito",
            f"VLAN cambiada correctamente.\n\nSwitch: {switch_ip}\nInterfaz: {interfaz}\nVLAN nueva: {vlan}"
        )
