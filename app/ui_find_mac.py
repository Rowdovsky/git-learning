import tkinter as tk
from tkinter import ttk, messagebox
from .find_mac_service import find_by_mac, find_by_ip
from .ui_change_vlan import ChangeVlanWindow


class FindMacWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Buscar endpoint (IP / MAC)")
        self.resizable(False, False)

        self.resultado_actual = None  # aquí guardamos el último resultado útil

        # ----- Entrada de búsqueda -----
        tk.Label(self, text="Valor a buscar:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.entry_valor = tk.Entry(self, width=25)
        self.entry_valor.grid(row=0, column=1, padx=10, pady=10)

        # ----- Radio buttons: IP o MAC -----
        self.modo = tk.StringVar(value="ip")
        frame_modo = tk.Frame(self)
        frame_modo.grid(row=0, column=2, padx=10, pady=10)
        tk.Radiobutton(frame_modo, text="IP", variable=self.modo, value="ip").pack(anchor="w")
        tk.Radiobutton(frame_modo, text="MAC", variable=self.modo, value="mac").pack(anchor="w")

        # ----- Botón Buscar -----
        btn_buscar = tk.Button(self, text="Buscar", command=self.ejecutar_busqueda)
        btn_buscar.grid(row=0, column=3, padx=10, pady=10)

        # ENTER lanza la búsqueda
        self.bind("<Return>", lambda event: self.ejecutar_busqueda())

        # ----- Tabla de resultado (solo 1 fila) -----
        columnas = ("ip", "mac", "switch_ip", "vlan", "interface")
        self.tree = ttk.Treeview(self, columns=columnas, show="headings", height=1)
        for col in columnas:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=120)
        self.tree.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

        # ----- Botón Cambiar VLAN desde el resultado -----
        self.btn_cambiar_vlan = tk.Button(
            self,
            text="Cambiar VLAN de este puerto",
            command=self.abrir_cambio_vlan_desde_resultado,
            state="disabled"
        )
        self.btn_cambiar_vlan.grid(row=2, column=0, columnspan=4, padx=10, pady=10)

    def ejecutar_busqueda(self):
        valor = self.entry_valor.get().strip()
        if not valor:
            messagebox.showerror("Error", "Ingresa una IP o MAC.")
            return

        modo = self.modo.get()

        try:
            if modo == "ip":
                resultados, mac = find_by_ip(valor)
            else:
                resultados = find_by_mac(valor)
                mac = None
        except Exception as e:
            messagebox.showerror("Error", f"Error en la búsqueda:\n{e}")
            return

        # Limpiar tabla y estado
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.resultado_actual = None
        self.btn_cambiar_vlan.config(state="disabled")

        # Filtrar resultados válidos (sin errores)
        resultados_validos = []
        for r in resultados:
            if r.get("error"):
                continue
            resultados_validos.append(r)

        if not resultados_validos:
            messagebox.showinfo("Sin resultados", "No se encontró información para ese valor.")
            return

        # Tomamos SOLO EL PRIMERO
        r = resultados_validos[0]
        self.resultado_actual = r

        # Insertar en la tabla
        self.tree.insert(
            "",
            "end",
            values=(
                r.get("ip") or "",
                r.get("mac") or "",
                r.get("switch_ip") or "",
                r.get("vlan") or "",
                r.get("interface") or "",
            ),
        )

        # Habilitar botón de cambiar VLAN SOLO si no es dispositivo inventariado
        if not r.get("es_dispositivo") and r.get("switch_ip") and r.get("interface"):
            self.btn_cambiar_vlan.config(state="normal")
        else:
            self.btn_cambiar_vlan.config(state="disabled")

    def abrir_cambio_vlan_desde_resultado(self):
        if not self.resultado_actual:
            messagebox.showerror("Error", "No hay resultado seleccionado.")
            return

        r = self.resultado_actual
        sw_ip = r.get("switch_ip")
        iface = r.get("interface")

        if not sw_ip or not iface:
            messagebox.showerror("Error", "Este resultado no tiene switch ni interfaz para cambiar VLAN.")
            return

        # Abrir ventana de cambio de VLAN con los datos pre-cargados
        win = ChangeVlanWindow(self, switch_ip=sw_ip, interfaz=iface)
        # el foco ya cae en la VLAN dentro de ChangeVlanWindow
