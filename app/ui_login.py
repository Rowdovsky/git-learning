import tkinter as tk
from tkinter import messagebox
from .db import get_conn


class LoginWindow:
    def __init__(self, root, on_login_ok):
        self.root = root
        self.on_login_ok = on_login_ok

        self.root.title("Login - Proyecto Redes")
        self.root.geometry("300x180")

        tk.Label(root, text="Usuario:").pack(pady=5)
        self.entry_user = tk.Entry(root)
        self.entry_user.pack()

        tk.Label(root, text="Contraseña:").pack(pady=5)
        self.entry_pass = tk.Entry(root, show="*")
        self.entry_pass.pack()

        tk.Button(root, text="Entrar", command=self.check_login).pack(pady=10)

    def check_login(self):
        user = self.entry_user.get().strip()
        pw = self.entry_pass.get().strip()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (user, pw)
        )
        row = cur.fetchone()
        conn.close()

        if row:
            self.on_login_ok()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
